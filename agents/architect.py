
from pydoc import text
from services.ado_client import ADOClient
from services.llm import get_llm
import re


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
        print(f"[Architect] RepoID: {state['repo_id']}")

        # --------------------------------------------------
        # 2️⃣ Fetch Logs
        # --------------------------------------------------
        logs = ado.get_build_logs(build_id)

        if not logs:
            raise Exception("No logs found for build")

        state["logs"] = logs


        # Use diagnosis utility for log analysis
        from services.diagnosis import diagnose_pipeline_failure
        print("[Architect] Running diagnosis via diagnosis utility...")
        diagnosis = diagnose_pipeline_failure(logs)
        state["diagnosis"] = diagnosis
        print(f"[Architect] Diagnosis:\n{diagnosis['raw_text']}")
        print(f"[Architect] Files to modify: {diagnosis['files_to_modify']}")
        state["status"] = "Diagnosis completed"
        print("[Architect] Diagnosis complete.")

    except Exception as e:
        print(f"[Architect ERROR] {str(e)}")
        state["status"] = f"Architect failed: {str(e)}"

    return state