import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
load_dotenv()

ORG=os.getenv("ORG")
PROJECT=os.getenv("PROJECT")
PAT=os.getenv("PAT")
bug_id=0

get_bug_id = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/wit/wiql?api-version=7.0"

{
  "query": "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.TeamProject] = @project AND [System.WorkItemType] = 'Bug' ORDER BY [System.CreatedDate] DESC"
}

query = {
    "query": """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = @project
        AND [System.WorkItemType] = 'Bug'
        ORDER BY [System.CreatedDate] DESC
    """
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {PAT}"
}

response = requests.post(get_bug_id, json=query, headers=headers)

print(response.status_code)

if response.status_code == 200:
    work_items = response.json().get('workItems', [])
    print(f"Found {len(work_items)} new bugs that haven't been processed by AI.")
    for item in work_items:
        bug_id = item['id']
        print(f"Bug ID: {item['id']}")
else:
    print(f"Failed to fetch work items. Status code: {response.status_code}, Response: {response.text}")

get_bug_details = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/wit/workitems/{bug_id}?api-version=7.0"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {PAT}"
}

response = requests.get(get_bug_details, headers=headers)
print(response.status_code)
if response.status_code == 200:
    bug_details = response.json()
    fields=bug_details.get('fields', {})
    print(f"Title: {fields.get('System.Title', 'N/A')}")
    print(f"Description: {fields.get('System.Description', 'N/A')}")
else:
    print(f"Failed to fetch bug details. Status code: {response.status_code}, Response: {response.text}")