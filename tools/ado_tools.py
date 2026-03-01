from langchain_core.tools import BaseTool
from pydantic import Field
from services.ado_client import ADOClient
from typing import Type

# 1. Create a class for Bug Creation
class CreateBugTool(BaseTool):
    name: str = "Create Bug"
    description: str = "Use this to create a bug in Azure DevOps."

    def _run(self, title: str, description: str) -> str:
        return ADOClient().create_bug(title, description)

# 2. Create a class for Log Fetching
class FetchLogsTool(BaseTool):
    name: str = "Fetch Pipeline Logs"
    description: str = "Use this to get logs for a specific build ID."

    def _run(self, build_id: int) -> str:
        return ADOClient().get_build_logs(int(build_id))