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

                ┌────────────────────┐
                │  Azure DevOps      │
                │  Pipeline Webhook  │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Orchestrator       │  ← LangGraph (recommended)
                │ (State Machine)    │
                └─────────┬──────────┘
                          │
      ┌───────────────────┼───────────────────┐
      ▼                   ▼                   ▼
Agent 1              Agent 2              Agent 3
Bug Creator          Architect            Engineer
                          │
                          ▼
                     Agent 4 (PR)
                          │
                          ▼
                   Azure DevOps PR API

## Architecture Summary

| Layer         | Tool                  |
| ------------- | --------------------- |
| LLM           | Azure GPT-4.1         |
| Orchestration | LangGraph             |
| State         | TypedDict + Cosmos    |
| Validation    | Pydantic              |
| DevOps        | Azure DevOps REST API |
| Hosting       | Azure Functions       |
| Observability | App Insights          |

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


## No of Angents and their work

| Agent                   | Responsibility                                                      | Key Constraint / Safety Gate                                        |
| ----------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Agent 1: The Observer   | Creates the Bug, collects raw logs, and initializes the "Case."     | Must verify the build actually failed (don't create false bugs).    |
| Agent 2: The Architect  | Diagnoses the error and proposes the code fix (the "brain").        | Must not commit code; output must be a "Proposed Plan" JSON.        |
| Agent 3: The Engineer   | Creates the feature branch and commits the fix proposed by Agent 2. | Must verify branch names and avoid touching protected config files. |
| Agent 4: The PR Manager | Raises the PR and triggers validation.                              | Must add a summary of Agent 2's diagnosis to the PR description.    |

## Why Multi agent

Fault Isolation: If Agent 2 (The Architect) hallucinates a bad fix, Agent 4 (The PR Manager) can still inspect the diff, realize it looks dangerous, and refuse to open the PR. In a single-agent system, the agent just "does it" without that second pair of eyes.

Context Management: LLMs have "context windows." If you feed a massive amount of code to a single agent, it gets overwhelmed. By passing only the relevant snippets from Agent 2 to Agent 3, you keep your context clean and your costs down.

Observability: If the process fails, you know exactly which agent failed. Did the bug creation fail? Or did the PR creation fail? You can debug the pipeline flow more easily.