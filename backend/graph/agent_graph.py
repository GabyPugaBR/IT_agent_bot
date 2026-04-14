from langgraph.graph import END, StateGraph

from agents.escalation_agent import escalation_agent
from agents.intake_agent import intake_agent
from agents.knowledge_agent import knowledge_agent
from agents.smalltalk_agent import smalltalk_agent
from agents.workflow_agent import workflow_agent
from graph.state import AgentState


def route(state: AgentState) -> str:
    intent = state["intent"]
    if intent == "knowledge":
        return "knowledge"
    if intent == "workflow":
        return "workflow"
    if intent == "smalltalk":
        return "smalltalk"
    return "escalation"


builder = StateGraph(AgentState)

builder.add_node("intake", intake_agent)
builder.add_node("knowledge", knowledge_agent)
builder.add_node("workflow", workflow_agent)
builder.add_node("escalation", escalation_agent)
builder.add_node("smalltalk", smalltalk_agent)

builder.set_entry_point("intake")

builder.add_conditional_edges(
    "intake",
    route,
    {
        "knowledge": "knowledge",
        "workflow": "workflow",
        "escalation": "escalation",
        "smalltalk": "smalltalk",
    },
)

builder.add_edge("knowledge", END)
builder.add_edge("workflow", END)
builder.add_edge("escalation", END)
builder.add_edge("smalltalk", END)

graph = builder.compile()
