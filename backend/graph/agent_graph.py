from langgraph.graph import END, StateGraph

from agents.escalation_agent import escalation_agent
from agents.intake_agent import intake_agent
from agents.knowledge_agent import knowledge_agent
from agents.workflow_agent import workflow_agent
from graph.state import AgentState


def route(state: AgentState) -> str:
    if state["intent"] == "knowledge":
        return "knowledge"
    if state["intent"] == "workflow":
        return "workflow"
    return "escalation"


builder = StateGraph(AgentState)

builder.add_node("intake", intake_agent)
builder.add_node("knowledge", knowledge_agent)
builder.add_node("workflow", workflow_agent)
builder.add_node("escalation", escalation_agent)

builder.set_entry_point("intake")

builder.add_conditional_edges(
    "intake",
    route,
    {
        "knowledge": "knowledge",
        "workflow": "workflow",
        "escalation": "escalation",
    },
)

builder.add_edge("knowledge", END)
builder.add_edge("workflow", END)
builder.add_edge("escalation", END)

graph = builder.compile()
