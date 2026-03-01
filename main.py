from graph import build_graph

def run_remediation(build_id: int):

    app = build_graph()

    initial_state = {
        "build_id": build_id,
        "logs": None,
        "failure_verified": False,
        "bug_id": None,
        "diagnosis": None,
        "branch_name": None,
        "pr_id": None,
        "status": "STARTED"
    }

    result = app.invoke(initial_state)
    return result

