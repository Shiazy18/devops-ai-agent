# devops-ai-agent

Agents to detect pipeline failure, create bug in Azure devops Boards, create new branch and suggest changes for the failure and raise PR

## Architect

Pipeline Fails
    ↓
ADO Board Bug Created (via pipeline only)
    ↓ 
Azure Function / Python Worker (polls every 5 min)
    ↓
Fetch New Bugs via REST API
    ↓
Call Azure AI Foundry Agent
    ↓
AI Returns Structured Fix Plan
    ↓
Update Work Item (Boards API)
    ↓
Optional: Change State to Resolved

## What's next

🔹 Auto PR creation via Git API

🔹 Failure trend clustering

🔹 Incident severity scoring

🔹 Teams notification

🔹 Dashboard with Power BI

🔹 Containerize and deploy to AKS