from services.ado_client import ADOClient

def run(state):
    """ 
        Which jobs failed
        what tasks failed
        which commit introduced the failure
    """
    try:
        ado = ADOClient()
        build_id = state["build_id"]

        print(f"[ContextBuilder] Fetching context for build ID: {build_id}")
        timeline = ado.get_build_timeline(build_id)
        if not timeline:
            raise Exception("Timeline not found for build")
        state["timeline"] = timeline

        failed_tasks = [
            {
                "name": record.name,
                "type": record.record_type,
            }
            for record in timeline.records
            if record.result == "failed"      
        ]

        state["failed_tasks"] = failed_tasks
        state["status"] = "Context built successfully"

        print(f"[ContextBuilder] Failed tasks extracted: {failed_tasks}")

        # get commit details
        build = ado.build_client.get_build(
            project=ado.project,
            build_id=build_id
        )
        if not build:
            raise Exception(f"Build {build_id} not found")
        state["context"] = {
            "commit_id": build.source_version,
            "repo_id": build.repository.id,
            "repo_name": build.repository.name,
            "source_branch": build.source_branch.replace("refs/heads/", "")
        }
        print(f"[ContextBuilder] Commit ID: {state['context']['commit_id']}")