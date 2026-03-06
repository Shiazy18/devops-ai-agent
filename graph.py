# graph.py

from langgraph.graph import StateGraph
from agents.architect import run as architect
from agents.app_engineer import run as app_engineer
from agents.infra_engineer import run as infra_engineer
from agents.pipeline_engineer import run as pipeline_engineer
from agents.pr_agent import run as pr_agent
from agents.manager import run as manager
from agents.engineer import run as engineer
import state

# def route_by_failure_type(state):
#     diagnosis = state.get("diagnosis", {})
#     failure_type = diagnosis.get("failure_type", "unknown")
#     confidence = diagnosis.get("confidence", 0.5)

#     if confidence < 0.6:
#         return "manager"
    
#     print(f"[Router] Routing based on failure type: {failure_type} with confidence {confidence}")

#     if failure_type == "application":
#         return "app_engineer"
#     elif failure_type == "infrastructure":
#         return "infra_engineer"
#     elif failure_type == "pipeline":
#         return "pipeline_engineer"
#     else:
#         return "manager"


def build_graph():
    workflow = StateGraph(dict)

    workflow.add_node("architect", architect)
    workflow.add_node("engineer", engineer)
    # workflow.add_node("app_engineer", app_engineer)
    # workflow.add_node("infra_engineer", infra_engineer)
    # workflow.add_node("pipeline_engineer", pipeline_engineer)
    workflow.add_node("pr_agent", pr_agent)
    workflow.add_node("manager", manager)

    workflow.set_entry_point("architect")

    # workflow.add_conditional_edges("architect", route_by_failure_type)

    workflow.add_edge("architect", "engineer")
    workflow.add_edge("engineer", "pr_agent")
    workflow.add_edge("pr_agent", "manager")

        

    # workflow.add_edge("app_engineer", "pr_agent")
    # workflow.add_edge("infra_engineer", "pr_agent")
    # workflow.add_edge("pipeline_engineer", "pr_agent")

   # workflow.add_edge("pr_agent", "manager")

    return workflow.compile()