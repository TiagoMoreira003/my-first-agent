import operator
from urllib import response

from langgraph.graph import StateGraph, START, END
from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain.messages import AnyMessage, ToolMessage
from pydantic import BaseModel
from typing_extensions import TypedDict, Annotated
from typing import Optional
from tools import best_club_info, football_api, web_search_tool
from typing import Literal
from langfuse.langchain import CallbackHandler
from langfuse import get_client, propagate_attributes
import streamlit as st

import random

langfuse = get_client()
langfuse_handler = CallbackHandler()

print("Langfuse authenticated: " + str(langfuse.auth_check()))

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    is_football: bool
    llm_calls: int
    club: Optional[str]
    league: Optional[str]
    player: Optional[str]

class Verdict(BaseModel):
    is_football: bool
    reason: str

class ParsedInfo(BaseModel):
    club: Optional[str] = None
    league: Optional[str] = None
    player: Optional[str] = None



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

def parse_information(state: dict):
    """Parse the information from the LLM's messages"""
    parsed = parse_model.invoke(
        [SystemMessage(content="Extract the club, league and player mentioned. Use null when absent."), *state["messages"][-3:]]
    )

    return {"club": parsed.club, "league": parsed.league, "player": parsed.player}

def guard(state: dict):
    """
    Guard to ensure that the question is about football before starting the whole workflow
    Returns the data with Verdict class structure.
    """
    message = "Is this question about football? Set is_football=true when unsure."
    verdict = guard_model.invoke([SystemMessage(content=message), *state["messages"][-3:]])
    return {"is_football": verdict.is_football}

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

def refuse(state: dict):
    """Refuse to answer if the question is not about football"""
    
    return {"messages": [AIMessage(content="I can only answer questions about football.")]}

def refuse_sporting(state: dict):
    """Refuse to answer if the club is Sporting"""
    
    return {"messages": [AIMessage(content="I cannot answer questions about Sporting.")]}

def route_after_guard(state: MessagesState) -> Literal["parse_information", "refuse"]:
    return "parse_information" if state["is_football"] else "refuse"

def route_after_parse(state: MessagesState) -> Literal["llm_call", "refuse_sporting"]:
    club = (state.get("club") or "").lower()
    return "refuse_sporting" if "sporting" in club else "llm_call"

model = ChatOpenRouter(
    model="openrouter/free",
    #model="mistralai/mistral-nemo",
    temperature=0.7
)

tools = [football_api, web_search_tool, best_club_info]
model_with_tools = model.bind_tools(tools)
guard_model = model.with_structured_output(Verdict)
parse_model = model.with_structured_output(ParsedInfo)
tools_by_name = {t.name: t for t in tools}

# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_node("guard", guard)
agent_builder.add_node("refuse", refuse)
agent_builder.add_node("refuse_sporting", refuse_sporting)
agent_builder.add_node("parse_information", parse_information)

# Add edges to connect nodes
agent_builder.add_edge(START, "guard")
agent_builder.add_conditional_edges("guard", route_after_guard, ["parse_information", "refuse"])
agent_builder.add_edge("refuse", END)
agent_builder.add_edge("refuse_sporting", END)
agent_builder.add_conditional_edges("parse_information", route_after_parse, ["llm_call", "refuse_sporting"])
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
agent = agent_builder.compile()

# guard_model = model.guard(messages[-1].content, {"messages": messages})
random_number = str(random.randint(1, 100))

if "messages" not in st.session_state:
    st.session_state.messages = []

prompt = st.chat_input("Say something")
if prompt:

    messages = st.session_state.messages
    messages.append(HumanMessage(prompt))

    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with propagate_attributes(session_id=random_number):
        messages = agent.invoke(
        {"messages": messages},
        config={"callbacks": [langfuse_handler]}
    )

    with st.chat_message("assistant"):
        st.markdown(messages["messages"][-1].content)