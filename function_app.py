import azure.functions as func
import logging
import json
from services.ado_client import ADOClient
from services.agent_logic import DevOpsAgent

# Initialize the Function App
app = func.FunctionApp()

@app.route(route="webhook_trigger", methods=["POST"])
def webhook_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Webhook received from Azure DevOps.")
    
    try:
        # 1. Extract JSON body
        req_body = req.get_json()
        
        # 2. Extract the Build ID
        # ADO webhooks are nested. Adjust this path based on the specific event structure.
        build_id = req_body.get('resource', {}).get('id')
        
        if not build_id:
            return func.HttpResponse("Build ID not found in payload", status_code=400)

        logging.info(f"Processing build_id: {build_id}")

        # 3. Instantiate your logic
        ado = ADOClient()
        agent = DevOpsAgent()

        # 4. Execute the pipeline
        raw_logs = ado.get_build_logs(build_id)
        diagnosis = agent.analyze_failure(raw_logs)
        
        # 5. Log output for debugging in App Insights
        logging.info(f"AI Diagnosis: {diagnosis}")
        
        return func.HttpResponse(
            json.dumps({"status": "success", "diagnosis": diagnosis}), 
            mimetype="application/json", 
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse("Internal Server Error", status_code=500)