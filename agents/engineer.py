# agents/engineer.py

from services.ado_client import ADOClient
from services.llm import get_llm


def run(state):
    try:
        # --------------------------------------------------
        # 1️⃣ Validate required state
        # --------------------------------------------------
        required_keys = ["build_id", "repo_id", "source_branch"]
        for key in required_keys:
            if key not in state:
                raise Exception(f"{key} missing from state")

        build_id = state["build_id"]
        repo_id = state["repo_id"]
        base_branch = state["source_branch"]

        print(f"[Engineer] Build ID: {build_id}")
        print(f"[Engineer] Repo ID: {repo_id}")
        print(f"[Engineer] Base Branch: {base_branch}")

        ado = ADOClient()
        llm = get_llm()

        # --------------------------------------------------
        # 2️⃣ Create Fix Branch
        # --------------------------------------------------
        branch_name = f"fix/build-{build_id}"

        print(f"[Engineer] Creating branch: {branch_name}")

        ado.create_branch(
            repository_id=repo_id,
            branch_name=branch_name,
            base_branch=base_branch
        )

        # --------------------------------------------------
        # 3️⃣ Determine Files to Modify
        # --------------------------------------------------
        files = state.get("diagnosis", {}).get("files_to_modify")

        print(f"[Engineer] Files suggested for modification: {files}")

        if not files or len(files) == 0:
            print("[Engineer] No files suggested. Using PoC fallback.")
            files = ["/README.md"]  # Safe PoC fallback

        # --------------------------------------------------
        # 4️⃣ Generate Fix + Commit
        # --------------------------------------------------
        for file_path in files:
            print(f"[Engineer] Generating fix for: {file_path}")

            content_prompt = f"""
            You are a senior software engineer.

            Based on the following pipeline failure diagnosis,
            generate the COMPLETE updated file content for: {file_path}

            Return ONLY valid file content. No markdown. No explanation.

            Diagnosis:
            {state.get('diagnosis', {}).get('raw_text', 'No diagnosis available')}
            """

            response = llm.invoke(content_prompt)
            new_content = response.content.strip()

            if not new_content:
                raise Exception(f"LLM returned empty content for {file_path}")

            print(f"[Engineer] Committing update to {file_path}")

            ado.commit_file_update(
                repository_id=repo_id,
                branch_name=branch_name,
                file_path=file_path,
                new_content=new_content
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