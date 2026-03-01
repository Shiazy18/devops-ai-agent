import os
import logging
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_0.work_item_tracking.models import JsonPatchOperation
from dotenv import load_dotenv

load_dotenv()

# Set up logging so you can see errors in Azure/Console
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