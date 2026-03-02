# from services.ado_client import ADOClient
# from dotenv import load_dotenv

# load_dotenv()
# client = ADOClient()

# builds = client.get_recent_builds(69)

# print("Recent Builds:")
# for b in builds:
#     print(b.id, b.status, b.result)

import os
from dotenv import load_dotenv
from main import run_remediation
from services.ado_client import ADOClient

load_dotenv()

def test_run():
    # 🔹 Replace with a REAL failed build ID
    build_id = 71
    ado = ADOClient()
    result = run_remediation(build_id)



    # print("\n====== FINAL STATE ======")
    # for k, v in result.items():
    #     print(f"{k}: {v}")

if __name__ == "__main__":
    test_run()

# from services.llm import get_llm

# llm = get_llm()

# response = llm.invoke("Say hello in JSON format")

# print(response.content)