import azure.functions as func
from main import run_remediation

app = func.FunctionApp()

@app.route(route="webhook_trigger", methods=["POST"])
def webhook_trigger(req: func.HttpRequest) -> func.HttpResponse:
    payload = req.get_json()
    build_id = payload['resource']['id']

    run_remediation(build_id)

    return func.HttpResponse("Remediation started", status_code=202)