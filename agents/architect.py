from services.llm import get_llm
from pydantic import BaseModel
from typing import List

class ProposedPlan(BaseModel):
    root_cause: str
    files_to_modify: List[str]
    fix_summary: str
    validation_steps: List[str]

def run(state):

    if not state["failure_verified"]:
        state["status"] = "No failure detected"
        return state

    llm = get_llm().with_structured_output(ProposedPlan)

    result = llm.invoke(f"""
    Diagnose the pipeline failure and propose fix.
    Do not write full code.
    Logs:
    {state["logs"][:8000]}
    """)

    state["diagnosis"] = result.dict()
    return state