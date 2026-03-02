from services.ado_client import ADOClient
from services.llm import get_llm
import json

def run(state):

    ado = ADOClient()

    # 🔥 Deterministic failure detection
    result = ado.get_build_result(state["build_id"])

    if result != "failed":
        state["failure_verified"] = False
        state["status"] = f"Build result was {result}"
        return state

    state["failure_verified"] = True

    logs = ado.get_build_logs(state["build_id"])
    state["logs"] = logs
    print(f"[BugValidator] Fetched logs for build {state['build_id']}")
    

    return state