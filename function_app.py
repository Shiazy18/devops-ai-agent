import azure.functions as func
from main import run_remediation

app = func.FunctionApp()


def find_build_id_in_payLoad(payload):
    """ Extract build ID from Azure DevOps webhook payload."""
    try:
        resource = payload.get('resource', {})
        build_id = resource.get('id')
        if build_id is None:
            raise ValueError("Build ID not found in payload")
        return build_id
    except Exception as e:
        print(f"[FunctionApp ERROR] {str(e)}")
        return None

@app.route(route="webhook_trigger", methods=["POST"])
def webhook_trigger(req: func.HttpRequest) -> func.HttpResponse:
    payload = req.get_json()
    build_id = find_build_id_in_payLoad(payload)

    if build_id is None:
        return func.HttpResponse("Build ID not found", status_code=400)

    run_remediation(build_id)

    return func.HttpResponse("Remediation started", status_code=202)