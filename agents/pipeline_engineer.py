# agents/pipeline_engineer.py

from services.ado_client import ADOClient
from services.llm import get_llm

def run(state):
    try:
        if not state.get("failure_verified"):
            state["status"] = "PipelineEngineer skipped"
            return state

        ado = ADOClient()
        llm = get_llm()
        branch_name = f"pipeline-fix/build-{state['build_id']}"
        state["branch_name"] = branch_name

        ado.create_branch(
            repository_id=state["repo_id"],
            branch_name=branch_name,
            base_branch=state["source_branch"]
        )

        # for debugging
        print(f"[PipelineEngineer] Created branch '{branch_name}' for pipeline fixes.")


        files = state["diagnosis"]["files_to_modify"]

        for file_path in files:
            print(f"[PipelineEngineer] Fetching existing file: {file_path}")
            existing_content = ado.get_file_content(
                repository_id=state["repo_id"],
                branch_name=state["source_branch"],
                file_path=file_path
            )
            prompt = f"""
            You are a Senior DevOps Engineer.
            Here is the current content of pipeline {file_path}:
            {existing_content}
            Root cause:
            {state['diagnosis']['root_cause']}
            IMPORTANT: Do NOT change the pool configuration unless the root cause is directly related to the pool. If the error is about pool change, do NOT modify the pool section. Only fix the actual failure.
            Provide ONLY the FULL corrected file content. No markdown, no explanation, just the file content.
            """
            new_content = llm.invoke(prompt).content
            # Validate that pool is not changed unless required
            if "pool:" in new_content and "pool:" not in existing_content:
                print("[PipelineEngineer] WARNING: Pool configuration was added unexpectedly. Skipping commit.")
                continue
            ado.commit_file_update(
                repository_id=state["repo_id"],
                branch_name=branch_name,
                file_path=file_path,
                new_content=new_content
            )

        state["status"] = "PipelineEngineer completed"

        print(f"[PipelineEngineer] Created branch {branch_name} with fixes for files: {files}")
        print(f"[PipelineEngineer] Status updated in state.")
        print(f"[PipelineEngineer] State: {state}")

    except Exception as e:
        state["status"] = f"PipelineEngineer failed: {str(e)}"

    return state