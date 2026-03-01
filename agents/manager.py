from tools.ado_tools import CreateBugTool

def run(state):
    try:
        bug_tool = CreateBugTool()
        bug_title = f"Pipeline failure: Build {state['build_id']}"
        bug_description = state.get("diagnosis", {}).get("raw_text", "No diagnosis")
        bug_id = bug_tool._run(bug_title, bug_description)
        state["bug_id"] = bug_id
        state["status"] = "Bug logged"

    except Exception as e:
        state["status"] = f"Manager failed: {str(e)}"

    return state