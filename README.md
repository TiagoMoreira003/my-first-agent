# my-first-agent

This is a simple project to help understanding how to build an agent and core concepts like tool integration, state, memory and more AI related concepts.

Langgraph is the framework that I will use in this project, the idea is to create an agent that can interact with various tools, maintain state, and handle complex workflows in a structured manner.

## How to run

```
uv sync

export OPENROUTER_API_KEY=<your_openrouter_api_key>
export API_SPORTS_KEY=<your_api_sports_key>

uv run python3 main.py
```


### Iteration 1

In the first iteration I started with creating a basic agent that can interact with tools and handle simple workflows. The focus was on integrating the football API and ensuring the agent can maintain state and memory whithin the same iteration.

In this iteration each tool mapped to a single API endpoint (`find_league_id`, `search_top_team_in_league`). They are kept in `agent.py` for reference, but they are not wired into the agent.

### Iteration 2

Tools moved from one tool per endpoint to a single `football_api` tool that abstracts the API. The model chooses the endpoint and params, and the tool validates them against an allowlist.


I added a web search tool (DuckDuckGo) as a fallback for questions the football API can't answer, such as news or data outside my plan's limits.
The agent now queries the football API first. Web search calls are blocked until the API has been tried, and the API tool only accepts a fixed allowlist of read-only endpoints.
Keeping the search football-related is still only a prompt instruction, not enforced in code.

I tested this with an off-topic question ("Who was the first king of Portugal?") to check whether the model would answer or refuse. It declined, so the prompt instruction held in that test.