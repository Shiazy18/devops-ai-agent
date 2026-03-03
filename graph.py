# graph.py

from langgraph.graph import StateGraph
from agents.architect import run as architect
from agents.app_engineer import run as app_engineer
from agents.infra_engineer import run as infra_engineer
from agents.pipeline_engineer import run as pipeline_engineer
from agents.pr_agent import run as pr_agent
from agents.manager import run as manager
from agents.engineer import run as engineer


def route_by_failure_type(state):
    diagnosis = state.get("diagnosis", {})
    failure_types = diagnosis.get("failure_type", ["unknown"])
    confidence = diagnosis.get("confidence", 0.5)

    print(f"[Router] Routing based on failure types: {failure_types} with confidence {confidence}")

    # If confidence is low, escalate to manager for human review
    if confidence < 0.6:
        return ["manager"]

    # Map failure types to agent names
    agent_map = {
        "application": "app_engineer",
        "infrastructure": "infra_engineer",
        "pipeline": "pipeline_engineer"
    }
    agents = []
    for t in failure_types:
        agent = agent_map.get(t)
        if agent:
            agents.append(agent)
    if not agents:
        agents = ["manager"]
    return agents


def build_graph():
    workflow = StateGraph(dict)

    workflow.add_node("architect", architect)
    workflow.add_node("engineer", engineer)
    workflow.add_node("app_engineer", app_engineer)
    workflow.add_node("infra_engineer", infra_engineer)
    workflow.add_node("pipeline_engineer", pipeline_engineer)
    workflow.add_node("pr_agent", pr_agent)
    workflow.add_node("manager", manager)

    workflow.set_entry_point("architect")

    # Route to the correct agent based on diagnosis
    workflow.add_conditional_edges("architect", route_by_failure_type)

    workflow.add_edge("app_engineer", "pr_agent")
    workflow.add_edge("infra_engineer", "pr_agent")
    workflow.add_edge("pipeline_engineer", "pr_agent")
    workflow.add_edge("engineer", "pr_agent")
    workflow.add_edge("pr_agent", "manager")

    return workflow.compile()