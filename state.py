from typing import TypedDict, Optional, Dict

class PipelineState(TypedDict):
    build_id: int
    logs: Optional[str]

    failure_verified: bool
    bug_id: Optional[int]

    diagnosis: Optional[Dict]

    branch_name: Optional[str]
    pr_id: Optional[int]

    status: str