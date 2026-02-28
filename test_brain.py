from services.ado_client import ADOClient
from services.agent_logic import DevOpsAgent
import json

def run_test():
    # 1. Initialize our components
    print("--- Initializing Brain and Client ---")
    ado = ADOClient()
    brain = DevOpsAgent()

    # 2. Pick a failed Build ID
    # REPLACE with a real failed build ID from your history
    build_id = "68" 
    
    print(f"--- Fetching logs for Build {build_id} ---")
    raw_logs = ado.get_build_logs(build_id)
    
    # 3. Analyze
    print("--- Analyzing logs with AI Brain... ---")
    ai_output = brain.analyze_failure(raw_logs)
    
    # 4. Show results
    print("--- AI Diagnosis ---")
    print(ai_output)

if __name__ == "__main__":
    run_test()