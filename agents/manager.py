from services.ado_client import ADOClient

def run(state):
    try:
        ado = ADOClient()

        # Create a bug if failure verified
        if state.get("failure_verified") and not state.get("bug_id"):
            title = f"Pipeline failed: build {state['build_id']}"
            description = state.get("diagnosis", {}).get("raw_text", "No details")
            bug_id = ado.create_bug(title, description)
            state["bug_id"] = bug_id

        state["status"] = "Manager completed"

    except Exception as e:
        state["status"] = f"Manager failed: {str(e)}"

    return state