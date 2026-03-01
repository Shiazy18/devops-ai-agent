import os
import logging
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_0.work_item_tracking.models import JsonPatchOperation
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
    
    def create_branch(self, branch_name: str, base_branch: str = "main"):
        git_client = self.connection.clients.get_git_client()
        repo = git_client.get_repository(self.project)

        refs = git_client.get_refs(
            repository_id=repo.id,
            filter=f"heads/{base_branch}"
        )

        if not refs:
            raise Exception("Base branch not found")

        base_commit = refs[0].object_id

        git_client.update_refs(
            ref_updates=[
                {
                    "name": f"refs/heads/{branch_name}",
                    "oldObjectId": "0000000000000000000000000000000000000000",
                    "newObjectId": base_commit
                }
            ],
            repository_id=repo.id
        )


    def commit_file_update(self, branch_name: str, file_path: str, new_content: str):
        git_client = self.connection.clients.get_git_client()
        repo = git_client.get_repository(self.project)

        # Get latest branch object ID
        refs = git_client.get_refs(
            repository_id=repo.id,
            filter=f"heads/{branch_name}"
        )

        if not refs:
            raise Exception("Branch not found")

        latest_commit = refs[0].object_id

        push_body = {
            "refUpdates": [
                {
                    "name": f"refs/heads/{branch_name}",
                    "oldObjectId": latest_commit
                }
            ],
            "commits": [
                {
                    "comment": "Auto remediation fix",
                    "changes": [
                        {
                            "changeType": "edit",
                            "item": {"path": file_path},
                            "newContent": {
                                "content": new_content,
                                "contentType": "rawtext"
                            }
                        }
                    ]
                }
            ]
        }

        git_client.create_push(push_body, repository_id=repo.id)


    def create_pull_request(self, source_branch: str, description: str):
        git_client = self.connection.clients.get_git_client()
        repo = git_client.get_repository(self.project)

        pr = git_client.create_pull_request(
            git_pull_request_to_create={
                "sourceRefName": f"refs/heads/{source_branch}",
                "targetRefName": "refs/heads/main",
                "title": f"Auto Fix: {source_branch}",
                "description": description
            },
            repository_id=repo.id
        )

        return pr.pull_request_id

    # Set up logging so you can see errors in Azure/Console
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)