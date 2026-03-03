from typing import TypedDict, Optional, List, Literal


class Diagnosis(TypedDict, total=False):
    root_cause: str
    failure_type: Literal["application", "infrastructure", "pipeline", "unknown"]
    confidence: float
    files_to_modify: List[str]
    raw_text: str


class PipelineState(TypedDict, total=False):
    # Build metadata
    build_id: int
    logs: Optional[str]
    repo_id: Optional[str]
    repo_name: Optional[str]
    source_branch: Optional[str]
    commit_id: Optional[str]
    new_branch: Optional[str]

    processed_logs: Optional[str]

    # Failure validation
    failure_verified: bool

    # Diagnosis
    diagnosis: Optional[Diagnosis]

    # Code changes
    branch_name: Optional[str]
    modified_files: Optional[List[str]]

    # PR & Work items
    pr_id: Optional[int]
    bug_id: Optional[int]

    # Execution metadata
    active_agent: Optional[str]
    error: Optional[str]

    # System state
    status: str

    timeline: Optional[List[str]]

    raw_logs: Optional[str]