from langgraph.graph import StateGraph
from state import PipelineState

from agents import bug_validator, architect, engineer, pr_creator, manager

def build_graph():

    graph = StateGraph(PipelineState)

    graph.add_node("validate", bug_validator.run)
    graph.add_node("architect", architect.run)
    graph.add_node("engineer", engineer.run)
    graph.add_node("manager", manager.run)
    graph.add_node("pr_creator", pr_creator.run)

    graph.set_entry_point("validate")

    graph.add_edge("validate", "architect")
    graph.add_edge("architect", "engineer")
    graph.add_edge("engineer", "manager")
    graph.add_edge("manager", "pr_creator")
    return graph.compile()