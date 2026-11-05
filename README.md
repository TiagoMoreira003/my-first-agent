# my-first-agent

This is a simple project to help understanding how to build an agent and core concepts like tool integration, state, memory and more AI related concepts.

Langgraph is the framework that I will use in this project, the idea is to create an agent that can interact with various tools, maintain state, and handle complex workflows in a structured manner.

## Stack

In this project, the agent will interact with the following tools:

- OpenRouter API (model provider + model routing)
- API Sports (sports data provider)
- DuckDuckGo web search (fallback for news and data the API can't provide)
- Langfuse (observability and monitoring)

## Workflow

The workflow of the agent can be summarized as follows:

- The agent receives a user query or task.
- It determines which tools are needed to fulfill the request.
- The agent interacts with the appropriate tools (API Sports first, web search as a fallback) to gather the required data.
- State is kept within a single run (memory across chats is planned).
- Observability and monitoring are handled through Langfuse to track the agent's actions and performance.

## How to run

```
uv sync

export OPENROUTER_API_KEY=<your_openrouter_api_key>
export API_SPORTS_KEY=<your_api_sports_key>
export LANGFUSE_SECRET_KEY=<your_langfuse_secret_key>
export LANGFUSE_PUBLIC_KEY=<your_langfuse_public_key>
export LANGFUSE_BASE_URL=<your_langfuse_base_url>

uv run python3 main.py
```

You can run the langfuse locally by following the instructions in the Langfuse documentation. Make sure to set the `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, and `LANGFUSE_BASE_URL` environment variables accordingly.

[local langfuse setup](https://langfuse.com/self-hosting/deployment/docker-compose)

You also can connect the agent to cloud, please check the Langfuse cloud documentation for setup instructions. I did the local setup for this project.

## Notes

The model is set through OpenRouter, so you can switch models or routing strategies by changing the model parameters. OpenRouter can also fall back to another model when one is unavailable, which helps reliability. See [model routing](https://openrouter.ai/blog/insights/model-routing/).

See [LEARNINGS.md](LEARNINGS.md) for the iteration log and what I learned along the way.
