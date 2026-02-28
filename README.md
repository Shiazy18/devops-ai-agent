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


## Features, Phase,Task,Tools/Action

1. Trigger,Detect failure,Azure DevOps Webhook (triggered on build fail) → Azure Function.
2. Context,Gather data,"Fetch build logs, error messages, and relevant code snippets from the Repo."
3. Reasoning,Analyze,Send context to an AI Agent (Azure AI Foundry) to propose a code fix.
4. Action,Remediate,"Create a bug ticket, branch the repo, commit the fix, and open a PR via REST API."
5. Validation,Safety Gate,"Run unit/integration tests on the PR. If failed, alert human."
6. Closure,Finalize,"If tests pass (and confidence score > threshold), merge (or request approval)."

