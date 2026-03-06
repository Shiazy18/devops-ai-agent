# agents/engineer.py

from services.ado_client import ADOClient
from services.llm import get_llm


def run(state):
    try:
        # --------------------------------------------------
        # 1️⃣ Validate required state
        # --------------------------------------------------
        if not state.get("failure_verified"):
            state["status"] = "Engineer skipped"
            return state

        ado = ADOClient()
        llm = get_llm()

        # build_id = state["build_id"]
        # repo_id = state["repo_id"]
        # base_branch = state["source_branch"]
        # root_cause = state["diagnosis"]["root_cause"]

        print(f"[Engineer] Build ID: {state['build_id']}")
        print(f"[Engineer] Repo ID: {state['repo_id']}")
        print(f"[Engineer] Base Branch: {state['source_branch']}")
        print(f"[Engineer] Root Cause: {state['diagnosis']['root_cause']}")

        

        # --------------------------------------------------
        # 2️⃣ Create Fix Branch
        # --------------------------------------------------
        branch_name = f"fix/build-{state['build_id']}"


        print(f"[Engineer] Creating branch: {branch_name}")

        state["new_branch"] = branch_name  # Store the new branch in state for visibility

        

        ado.create_branch(
            repository_id=state['repo_id'],
            branch_name=branch_name,
            base_branch=state['source_branch']
        )

        # --------------------------------------------------
        # 3️⃣ Determine Files to Modify
        # --------------------------------------------------
        files = state["diagnosis"]["files_to_modify"]   

        print(f"[Engineer] Files suggested for modification: {files}")

        # if not files or len(files) == 0:
        #     print("[Engineer] No files suggested. Using PoC fallback.")
        #     files = ["/README.md"]  

        # --------------------------------------------------
        # 4️⃣ Generate Fix + Commit
        # --------------------------------------------------
        from services.llm import get_llm_response
        for file_path in files:
            print(f"[Engineer] Fetching existing file: {file_path}")
            existing_content = ado.get_file_content(
                repository_id=state['repo_id'],
                branch_name=state['source_branch'],
                file_path=file_path
            )
            print(f"[Engineer] Generating fix for: {file_path}")
            content_prompt = f"""
            Fix only the minimal lines needed for this root cause:
            {state['diagnosis']['root_cause']}
            File: {file_path}
            Content:
            {existing_content}
            Return only the corrected file content. No explanation.
            """
            patch_instructions = get_llm_response(content_prompt).strip()

            print(f"[Engineer] LLM patch instructions for {file_path} received.")
            #print(f"[Engineer] Patch instructions:\n{patch_instructions}")


            # commiting changes to file

            print(f"[Engineer] Committing file {file_path} changes to branch {branch_name}...")

            ado.commit_file_update(
                repository_id=state['repo_id'],
                branch_name=branch_name,
                file_path=file_path,  # Just committing the first file for PoC
                new_content=patch_instructions  # Placeholder content
            )

        # --------------------------------------------------
        # 5️⃣ Update State
        # --------------------------------------------------
        state["branch_name"] = branch_name
        state["status"] = "Fix committed successfully"

        print(f"[Engineer] Fix committed to branch {branch_name}")

    except Exception as e:
        print(f"[Engineer ERROR] {str(e)}")
        state["status"] = f"Engineer failed: {str(e)}"

    return state