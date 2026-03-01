from services.ado_client import ADOClient
from services.llm import get_llm

from services.ado_client import ADOClient
from services.llm import get_llm

def run(state):
    try:
        ado = ADOClient()
        llm = get_llm()

        branch_name = f"fix/build-{state['build_id']}"

        # 🔹 Force branch creation
        ado.create_branch(branch_name)

        # 🔹 Pick file to modify
        files = state.get("diagnosis", {}).get("files_to_modify")
        if not files or len(files) == 0:
            # PoC: force a file
            files = ["/README.md"]

        for file_path in files:
            # Generate new content via LLM
            content_prompt = f"""
            Based on this diagnosis, generate the full content for {file_path}.
            Only return the file content.
            Diagnosis:
            {state.get('diagnosis', {}).get('raw_text', 'No diagnosis')}
            """
            response = llm.invoke(content_prompt)
            new_content = response.content

            ado.commit_file_update(
                branch_name=branch_name,
                file_path=file_path,
                new_content=new_content
            )

        state["branch_name"] = branch_name
        state["status"] = "Fix committed"

    except Exception as e:
        state["status"] = f"Engineer failed: {str(e)}"

    return state