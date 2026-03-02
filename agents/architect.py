
from services.ado_client import ADOClient
from services.llm import get_llm


def run(state):
    try:
        if "build_id" not in state:
            raise Exception("build_id missing from state")

        build_id = state["build_id"]
        print(f"[Architect] Processing build ID: {build_id}")

        ado = ADOClient()
        llm = get_llm()

        # --------------------------------------------------
        # 1️⃣ Fetch Build Metadata
        # --------------------------------------------------
        build = ado.build_client.get_build(
            project=ado.project,
            build_id=build_id
        )

        if not build:
            raise Exception(f"Build {build_id} not found")

        # Check build result
        if build.result != "failed":
            print(f"[Architect] Build result is '{build.result}'. Skipping remediation.")
            state["status"] = "Build not failed. No action required."
            state["failure_verified"] = False
            return state

        state["failure_verified"] = True

        # Extract repository metadata
        state["repo_id"] = build.repository.id
        state["repo_name"] = build.repository.name
        state["source_branch"] = build.source_branch.replace("refs/heads/", "")
        state["commit_id"] = build.source_version

        print(f"[Architect] Repo: {state['repo_name']}")
        print(f"[Architect] Branch: {state['source_branch']}")
        print(f"[Architect] Commit: {state['commit_id']}")

        # --------------------------------------------------
        # 2️⃣ Fetch Logs
        # --------------------------------------------------
        logs = ado.get_build_logs(build_id)

        if not logs:
            raise Exception("No logs found for build")

        state["logs"] = logs

        # --------------------------------------------------
        # 3️⃣ Diagnose via LLM (PoC version)
        # --------------------------------------------------
        print("[Architect] Running diagnosis via LLM...")

        prompt = f"""
        You are a senior DevOps Architect.

        Analyze the following Azure DevOps pipeline failure logs.

        1. Identify the root cause.
        2. Suggest which file likely needs modification.
        3. Keep the answer concise.
        4. Return plain text (no markdown).

        Logs:
        {logs[:8000]}
        """

        response = llm.invoke(prompt)
        diagnosis_text = response.content.strip()

        if not diagnosis_text:
            raise Exception("LLM returned empty diagnosis")

        # For PoC we force at least one file
        state["diagnosis"] = {
            "raw_text": diagnosis_text,
            "files_to_modify": ["/README.md"]  # Safe fallback for PoC
        }

        state["status"] = "Diagnosis completed"

        print("[Architect] Diagnosis complete.")

    except Exception as e:
        print(f"[Architect ERROR] {str(e)}")
        state["status"] = f"Architect failed: {str(e)}"

    return state