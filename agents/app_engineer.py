from services.ado_client import ADOClient
from services.llm import get_llm

def run(state):
    try:
        if not state.get("failure_verified"):
            state["status"] = "AppEngineer skipped"
            return state

        ado = ADOClient()
        llm = get_llm()

        #for debugging
        print(f"[AppEngineer] Starting AppEngineer for build {state['build_id']}")

        branch_name = f"fix/build-{state['build_id']}"
        state["branch_name"] = branch_name

        # Create branch
        ado.create_branch(
            repository_id=state["repo_id"],
            branch_name=branch_name,
            base_branch=state["source_branch"]
        )

        # for debugging
        print(f"[AppEngineer] Created branch '{branch_name}' for application fixes.")

        files = state["diagnosis"]["files_to_modify"]

        #for debugging
        print(f"[AppEngineer] Files suggested for modification: {files}")

        if not files or len(files) == 0:
            print("[AppEngineer] No files suggested.")
        
        for file_path in files:
            print(f"[AppEngineer] Fetching existing file: {file_path}")

            existing_content = ado.get_file_content(
                repository_id=state["repo_id"],
                branch_name=state["source_branch"],
                file_path=file_path
            )

            prompt = f"""
            You are a senior Software Developer.

            Here is the current content of {file_path}:

            {existing_content}

            Root cause:
            {state['diagnosis']['root_cause']}

            Provide the FULL corrected file content only.
            Do not explain anything.
            """

            print("[AppEngineer] Calling LLM...")
            response = llm.invoke(prompt)
            print("[AppEngineer] LLM responded.")

            new_content = response.content

            print(f"[AppEngineer] Committing updated file: {file_path}")

            ado.commit_file_update(
                repository_id=state["repo_id"],
                branch_name=branch_name,
                file_path=file_path,
                new_content=new_content
            )

        # for file_path in files:
        #     print(f"[AppEngineer] Generating fix for: {file_path}")
        #     prompt = f"""
        #     Based on this root cause, generate updated content for {file_path}.

        #     Root cause:
        #     {state['diagnosis']['root_cause']}
        #     """

        #     response = llm.invoke(prompt)
        #     new_content = response.content

        #     #for debugging
        #     print(f"[AppEngineer] Generated new content for {file_path}:\n{new_content}")

        #     ado.commit_file_update(
        #         repository_id=state["repo_id"],
        #         branch_name=branch_name,
        #         file_path=file_path,
        #         new_content=new_content
        #     )

        state["status"] = "AppEngineer completed"

        print(f"[AppEngineer] Status updated in state.")
        print(f"[AppEngineer] State: {state}")

    except Exception as e:
        state["status"] = f"AppEngineer failed: {str(e)}"

    return state