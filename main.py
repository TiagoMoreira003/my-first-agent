import operator

from langgraph.graph import StateGraph, START, END
from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.messages import AnyMessage, ToolMessage
from typing_extensions import TypedDict, Annotated
from agent import football_api, web_search_tool
from typing import Literal
from langfuse.langchain import CallbackHandler
from langfuse import get_client, propagate_attributes

import random

langfuse = get_client()
langfuse_handler = CallbackHandler()

print("Langfuse authenticated: " + str(langfuse.auth_check()))

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int

def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content=(
                            "You answer football questions. Always query football_api first. "
                            "Use web_search_tool only after football_api returned errors or no results, or for news it cannot provide. "
                            "Resolve names to IDs via the leagues/teams endpoints before calling standings/fixtures. "
                            "If a call returns errors or no results, adjust params (e.g. season) and retry."
                        )
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }    

def football_api_was_called(messages: list) -> bool:
    return any(
        call["name"] == football_api.name
        for m in messages
        for call in getattr(m, "tool_calls", [])
    )

def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        if tool_call["name"] == web_search_tool.name and not football_api_was_called(state["messages"]):
            observation = "Not allowed yet: call football_api first, then use web search only if it fails or has no data."
        else:
            observation = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}

def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END

model = ChatOpenRouter(
    #model="openrouter/free",
    model="anthropic/claude-sonnet-4.6",
    temperature=0.7
)

tools = [football_api, web_search_tool]
model_with_tools = model.bind_tools(tools)
tools_by_name = {t.name: t for t in tools}

# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
agent = agent_builder.compile()

messages = [
    HumanMessage("Porto vs Benfica, which one is bigger. football wise!"),
]

random_number = str(random.randint(1, 100))

with propagate_attributes(session_id=random_number):
    messages = agent.invoke(
    {"messages": messages},
    config={"callbacks": [langfuse_handler]}
)
    
for m in messages["messages"]:
    m.pretty_print()