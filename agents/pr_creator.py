from services.ado_client import ADOClient
import json

def run(state):

    if not state["branch_name"]:
        return state

    ado = ADOClient()

    pr_id = ado.create_pull_request(
        source_branch=state["branch_name"],
        description=json.dumps(state["diagnosis"], indent=2)
    )

    state["pr_id"] = pr_id
    state["status"] = "PR Created"

    return state