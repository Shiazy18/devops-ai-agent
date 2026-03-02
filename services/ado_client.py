import os
import logging
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
try:
    from azure.devops.v7_0.work_item_tracking.models import JsonPatchOperation
except ImportError:
    from azure.devops.released.work_item_tracking.models import JsonPatchOperation
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ADOClient:
    def __init__(self):
        # Using '' as username is the standard way to auth with PATs
        self.token = os.getenv("PAT")
        self.org_url = f"https://dev.azure.com/{os.getenv('ORG')}"
        self.project = os.getenv("PROJECT")

        if not all([self.token, self.org_url, self.project]):
            raise ValueError("Missing environment variables: PAT, ORG, or PROJECT.")

        # BasicAuthentication is the preferred method for PATs
        credentials = BasicAuthentication('', self.token)
        self.connection = Connection(base_url=self.org_url, creds=credentials)
        self.build_client = self.connection.clients.get_build_client()
    def get_recent_builds(self, top=5):
        """Returns a list of build objects instead of printing them."""
        try:
            return self.build_client.get_builds(project=self.project, top=top)
        except Exception as e:
            logger.error(f"Failed to fetch builds: {e}")
            return []

    def get_build_logs(self, build_id):
        """Returns the log string or None if failed."""
        try:
            log_refs = self.build_client.get_build_logs(project=self.project, build_id=build_id)
            if not log_refs:
                return None

            combined_text = []
            for ref in log_refs:
                log_stream = self.build_client.get_build_log(project=self.project, build_id=build_id, log_id=ref.id)
                
                # Your robust decoding logic is excellent—keeping it here
                if hasattr(log_stream, '__iter__'):
                    parts = [chunk.decode('utf-8', errors='replace') if isinstance(chunk, bytes) else str(chunk) for chunk in log_stream]
                    combined_text.append("".join(parts))
                else:
                    combined_text.append(str(log_stream))
            
            return "\n".join(combined_text)

        except Exception as e:
            logger.error(f"Error fetching logs: {e}")
            return None
        
    def get_build_result(self, build_id: int):
        build = self.build_client.get_build(
            project=self.project,
            build_id=build_id
        )
        return build.result
    
    def create_bug(self, title: str, description: str) -> str:
        wit_client = self.connection.clients.get_work_item_tracking_client()

        patch_document = [
            JsonPatchOperation(
                op="add",
                path="/fields/System.Title",
                value=title
            ),
            JsonPatchOperation(
                op="add",
                path="/fields/System.Description",
                value=description
            ),
        ]

        work_item = wit_client.create_work_item(
            document=patch_document,
            project=self.project,
            type="Bug"
        )

        return f"Bug created with ID: {work_item.id}"
    
    def create_branch(self, repository_id: str, branch_name: str, base_branch: str):
        git_client = self.connection.clients.get_git_client()

        print(f"[ADO-Client]Creating branch '{branch_name}' from '{base_branch}'")

        # Remove refs prefix if passed
        base_branch = base_branch.replace("refs/heads/", "")

        # Get base branch reference
        refs = git_client.get_refs(
            repository_id=repository_id,
            project=self.project,
            filter=f"heads/{base_branch}"
        )

        if not refs:
            raise Exception(f"Base branch '{base_branch}' not found")

        base_commit_id = refs[0].object_id

        # Check if branch already exists
        existing = git_client.get_refs(
            repository_id=repository_id,
            project=self.project,
            filter=f"heads/{branch_name}"
        )

        if existing:
            print(f"[ADO-Client]Branch '{branch_name}' already exists. Skipping creation.")
            return

        # Create new branch
        git_client.update_refs(
            ref_updates=[{
                "name": f"refs/heads/{branch_name}",
                "oldObjectId": "0000000000000000000000000000000000000000",
                "newObjectId": base_commit_id
            }],
            repository_id=repository_id,
            project=self.project
        )

        print(f"[ADO-Client]Branch '{branch_name}' created successfully.")
    

    def commit_file_update(self, repository_id: str, branch_name: str, file_path: str,new_content: str):
        git_client = self.connection.clients.get_git_client()

        print(f"[ADO-Client]Committing to branch '{branch_name}' file '{file_path}'")

        branch_name = branch_name.replace("refs/heads/", "")

        # Get branch reference
        refs = git_client.get_refs(
            repository_id=repository_id,
            project=self.project,
            filter=f"heads/{branch_name}"
        )

        if not refs:
            raise Exception(f"Branch '{branch_name}' not found")

        old_object_id = refs[0].object_id

        # Determine if file exists (edit vs add)
        try:
            from azure.devops.v7_1.git.models import GitVersionDescriptor
            version_desc = GitVersionDescriptor(version_type="branch", version=branch_name)
            git_client.get_item(
                repository_id=repository_id,
                project=self.project,
                path=file_path,
                version_descriptor=version_desc
            )
            # git_client.get_item(
            #     repository_id=repository_id,
            #     project=self.project,
            #     path=file_path,
            #     version_descriptor={
            #         "versionType": "branch",
            #         "version": branch_name
            #     }
            # )
            change_type = "edit"
            print(f"[ADO-Client] File exists. Performing EDIT.")
        except Exception as ex:
            # Only set to 'add' if the error is file not found
            if hasattr(ex, 'message') and ('not found' in ex.message.lower() or 'does not exist' in ex.message.lower()):
                change_type = "add"
                print(f"[ADO-Client] File does not exist. Performing ADD.")
            else:
                print(f"[ADO-Client] Unexpected error: {ex}")
                raise

        # Create commit payload
        commit = {
            "comment": "Automated fix from DevOps remediation agent",
            "changes": [{
                "changeType": change_type,
                "item": {"path": file_path},
                "newContent": {
                    "content": new_content,
                    "contentType": "rawtext"
                }
            }]
        }

        # Push commit
        git_client.create_push(
            push={
                "refUpdates": [{
                    "name": f"refs/heads/{branch_name}",
                    "oldObjectId": old_object_id
                }],
                "commits": [commit]
            },
            repository_id=repository_id,
            project=self.project
        )

        print(f"[ADO-Client] Commit successful on branch '{branch_name}'.")

    # def commit_file_update(self, branch_name: str, file_path: str, new_content: str):
    #     git_client = self.connection.clients.get_git_client()
    #     repo = git_client.get_repository(self.project)

    #     # Get latest branch object ID
    #     refs = git_client.get_refs(
    #         repository_id=repo.id,
    #         filter=f"heads/{branch_name}"
    #     )

    #     if not refs:
    #         raise Exception("Branch not found")

    #     latest_commit = refs[0].object_id

    #     push_body = {
    #         "refUpdates": [
    #             {
    #                 "name": f"refs/heads/{branch_name}",
    #                 "oldObjectId": latest_commit
    #             }
    #         ],
    #         "commits": [
    #             {
    #                 "comment": "Auto remediation fix",
    #                 "changes": [
    #                     {
    #                         "changeType": "edit",
    #                         "item": {"path": file_path},
    #                         "newContent": {
    #                             "content": new_content,
    #                             "contentType": "rawtext"
    #                         }
    #                     }
    #                 ]
    #             }
    #         ]
    #     }

    #     git_client.create_push(push_body, repository_id=repo.id)


    # def create_pull_request(self, source_branch: str, description: str):
    #     git_client = self.connection.clients.get_git_client()
    #     repo = git_client.get_repository(self.project)

    #     pr = git_client.create_pull_request(
    #         git_pull_request_to_create={
    #             "sourceRefName": f"refs/heads/{source_branch}",
    #             "targetRefName": "refs/heads/main",
    #             "title": f"Auto Fix: {source_branch}",
    #             "description": description
    #         },
    #         repository_id=repo.id
    #     )

    #     return pr.pull_request_id
    def create_pull_request(self, repository_id, source_branch, target_branch, title, description):
        from azure.devops.v7_0.git.models import GitPullRequest

        git_client = self.connection.clients.get_git_client()
        print(f"[ADO-Client]Creating PR from '{source_branch}' to '{target_branch}' with title '{title}'")
        pr = GitPullRequest(
            source_ref_name=f"refs/heads/{source_branch}",
            target_ref_name=f"refs/heads/{target_branch}",
            title=title,
            description=description
        )

        print(f"[ADO-Client] Description: {description}")
        print(f"[ADO-Client] Starting PR creation...")
        
        try:
            created_pr = git_client.create_pull_request(
                git_pull_request_to_create=pr,
                repository_id=repository_id,
                project=self.project
            )
        except Exception as e:
            print(f"[ADO-Client] Error creating PR: {e}")
            raise

        print(f"[ADO-Client] PR created with ID: {created_pr.pull_request_id}") 

        return created_pr
    
    def get_file_content(self, repository_id: str, branch_name: str, file_path: str) -> bytes:
        """
        Streams the file from ADO and returns raw bytes.
        Suitable for large/binary/LFS files.
        """
        try:
            from azure.devops.v7_1.git.models import GitVersionDescriptor, GitVersionType
        except ImportError:
            from azure.devops.released.git.models import GitVersionDescriptor, GitVersionType

        if not file_path.startswith("/"):
            file_path = "/" + file_path
        branch = branch_name.replace("refs/heads/", "")

        version_descriptor = GitVersionDescriptor(
            version=branch,
            version_type=GitVersionType.branch
        )

        # get_item_content streams the file; join all chunks into bytes
        # (Same underlying REST: Items - Get; here content comes as a stream) [1](https://learn.microsoft.com/en-us/rest/api/azure/devops/git/items/get?view=azure-devops-rest-7.1)[3](https://stackoverflow.com/questions/78814586/how-can-i-extract-file-contents-of-a-specific-commit-using-azure-devops-api-pyt)
        content_iter = self.git_client.get_item_content(
            repository_id=repository_id,
            path=file_path,
            project=self.project,
            version_descriptor=version_descriptor,
            resolve_lfs=True  # get actual content if file is LFS-tracked
        )
        return b"".join(content_iter)


    # Set up logging so you can see errors in Azure/Console
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)