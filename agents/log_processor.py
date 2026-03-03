from services.pre_processing import LogProcessor
from services.ado_client import ADOClient


def run(state):
    try:
        if not state.get("build_id"):
            state["status"] = "LogProcessor skipped (no logs)"
            print(f"[LogProcessor] No logs found for build {state['build_id']}. Skipping log processing.")
            return state
        
        build_id = state["build_id"]
        print(f"[LogProcessor] Starting log processing for build {build_id}")

        pplogs = LogProcessor()
        ado = ADOClient()

        # --------------------------------------------------
        # Fetch Build Metadata
        # --------------------------------------------------
        build = ado.build_client.get_build(
            project=ado.project,
            build_id=build_id
        )



        if not build:
            raise Exception(f"Build {build_id} not found")
        print(f"[LogProcessor] Build found: ID {build_id}, Repo {build.repository.name}, Branch {build.source_branch}")
        # Check build result
        if build.result != "failed":
            print(f"[LogProcessor] Build result is '{build.result}'. Skipping remediation.")
            state["status"] = "Build not failed. No action required."
            state["failure_verified"] = False
            return state
        
        # Extract repository metadata
        state["repo_id"] = build.repository.id
        state["repo_name"] = build.repository.name
        state["source_branch"] = build.source_branch.replace("refs/heads/", "")
        state["commit_id"] = build.source_version

        print(f"[LogProcessor] Repo: {state['repo_name']}")
        print(f"[LogProcessor] Branch: {state['source_branch']}")
        print(f"[LogProcessor] Commit: {state['commit_id']}")
        print(f"[LogProcessor] RepoID: {state['repo_id']}")
        
        # --------------------------------------------------
        # Fetch Build Logs
        # --------------------------------------------------

        raw_logs = ado.get_build_logs(build_id)

        if not raw_logs:
            raise Exception("No logs found for build")

        state["raw_logs"] = raw_logs



        print(f"[LogProcessor] Processing logs for build {build_id}")
        processed_logs = pplogs.extract_errors(raw_logs)
        state["processed_logs"] = processed_logs
        state["status"] = "Logs processed"
        print(f"[LogProcessor] Extracted error logs:\n{processed_logs}")

    except Exception as e:
        state["status"] = f"LogProcessor failed: {str(e)}"
        print(f"[LogProcessor] Error processing logs for build {build_id}: {e}")

    return state