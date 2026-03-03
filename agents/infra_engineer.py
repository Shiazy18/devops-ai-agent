# agents/infra_engineer.py

from services.ado_client import ADOClient
from services.llm import get_llm

def run(state):
    try:
        if not state.get("failure_verified"):
            state["status"] = "InfraEngineer skipped"
            return state

        ado = ADOClient()
        llm = get_llm()
        branch_name = f"infra-fix/build-{state['build_id']}"
        state["branch_name"] = branch_name

        ado.create_branch(
            repository_id=state["repo_id"],
            branch_name=branch_name,
            base_branch=state["source_branch"]
        )

        # for debugging
        print(f"[InfraEngineer] Created branch '{branch_name}' for infrastructure fixes.")

        files = state["diagnosis"]["files_to_modify"]

        # for debugging
        print(f"[InfraEngineer] Files suggested for modification: {files}")
        for file_path in files:
            existing_content = ado.get_file_content(
                repository_id=state["repo_id"],
                branch_name=state["source_branch"],
                file_path=file_path
            )
            prompt = f"""
            You are a senior Infrastructure Engineer.
            Here is the current content of {file_path}:
            {existing_content}
            Root cause:
            {state['diagnosis']['root_cause']}
            Provide ONLY the FULL corrected file content. No markdown, no explanation, just the file content.
            """
            new_content = llm.invoke(prompt).content
            ado.commit_file_update(
                repository_id=state["repo_id"],
                branch_name=branch_name,
                file_path=file_path,
                new_content=new_content
            )

        state["status"] = "InfraEngineer completed"

        
        print(f"[InfraEngineer] Status updated in state.")
        print(f"[InfraEngineer] State: {state}")

    except Exception as e:
        state["status"] = f"InfraEngineer failed: {str(e)}"

    return state