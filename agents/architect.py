
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

        # --------------------------------------------------
        # 3️⃣ Diagnose via LLM (PoC version)
        # --------------------------------------------------
        print("[Architect] Running diagnosis via LLM...")

        from services.llm import get_llm_response
        prompt = f"""
        Analyze these pipeline logs for errors. Focus only on failed jobs.
        Return:
        ROOT_CAUSE: <short>
        FAILURE_TYPE: <application|infrastructure|pipeline>
        FILES_TO_MODIFY: <file paths>
        CONFIDENCE: <0.0-1.0>
        Logs (truncated): {logs[:2000]}
        """
        diagnosis_text = get_llm_response(prompt)


        if not diagnosis_text:
            raise Exception("LLM returned empty diagnosis")

        failure_type = re.search(r"FAILURE_TYPE:\s*(.*)", diagnosis_text)
        confidence = re.search(r"CONFIDENCE:\s*(.*)", diagnosis_text)
        root_cause = re.search(r"ROOT_CAUSE:\s*(.*)", diagnosis_text)

        files=[]

        for line in diagnosis_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("-"):
                file_name = stripped[1:].strip() 
                if not file_name.startswith("/"):
                    file_name = "/" + file_name   # add leading slash if missing
                    files.append(file_name)
            


        state["diagnosis"] = {
            "raw_text": diagnosis_text,
            "failure_type": failure_type.group(1).strip().lower() if failure_type else "unknown",
        }
        # Remove logs from state to minimize context passed to next agent
        if "logs" in state:
            del state["logs"]
            "confidence": float(confidence.group(1)) if confidence else 0.0,
            "root_cause": root_cause.group(1).strip() if root_cause else "No root cause identified",
            "files_to_modify": files


        print(f"[Architect] Diagnosis:\n{diagnosis_text}")
        print(f"[Architect] Files to modify: {state['diagnosis']['files_to_modify']}")


        state["status"] = "Diagnosis completed"

        print("[Architect] Diagnosis complete.")

    except Exception as e:
        print(f"[Architect ERROR] {str(e)}")
        state["status"] = f"Architect failed: {str(e)}"

    return state