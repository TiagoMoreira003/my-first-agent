# Learnings

A log of what I built and learned in each iteration.

## Iteration 1: One tool per endpoint

- **What:** a basic agent with tools that each mapped to one API endpoint (`find_league_id`, `search_top_team_in_league`).
- **Learned:** state is kept within a single run. The tools are still in `agent.py` for reference, but they are not wired into the agent.

## Iteration 2: One tool that abstracts the API, plus web search

- **What:** replaced the per-endpoint tools with a single `football_api` tool. The model chooses the endpoint and params, and the tool validates them against an allowlist of read-only endpoints.
- **What:** added DuckDuckGo web search as a fallback for news or data outside my plan's limits. Web search is blocked in code until `football_api` has been tried.
- **Learned:** a docstring works as a prompt, while the allowlist is the real safety check.
- **Test:** I asked an off-topic question ("Who was the first king of Portugal?") to see whether the model would answer or refuse. It declined, but keeping search football-only is still only a prompt instruction, not enforced in code.
- **Open question:** how to enforce "football only" in code.

## Iteration 3: Observability with Langfuse

- **What:** set up the Langfuse client and callback handler and passed it to `agent.invoke`. Each LLM call, tool call and state transition is now traced.
- **Learned:** traces make it much easier to debug and understand the agent's behavior.
- **TODO:** note what the traces show (number of calls, latency, cost) and add a screenshot.

## Iteration 4: Tool failures and prediction questions

- **Problem:** asking whether Porto would pass the Champions League league phase failed. The Langfuse trace showed `web_search_tool` with status Error and `output: undefined`. The query was long and specific ("Porto Champions League 2026/27 league phase standings all results") and DuckDuckGo returned no results.
- **Cause:** the search library raised an exception instead of returning an empty list, so the model never got a message it could use to retry.
- **Learned:** tool failures should go back to the model as text, not as exceptions, so it can adjust and try again. Short queries (3 to 6 words) work better than long ones.
- **Learned:** a prediction is not a tool. The agent fetches facts (standings, fixtures, recent form) and the model reasons over them, presenting the result as an estimate.
- **Fix:** wrapped the search in a `try/except` that returns the error to the model as text, and added a line to the tool docstring asking for short, simple queries.
- **Result:** after the fix the agent gave a good answer.
- **Learned:** Langfuse made the cause visible in one trace, so I did not have to guess.

## Iteration 5: Session management with Langfuse

- Now I added the session argument it is not dynamic yet, but this already aggregates a single call under a session ID in Langfuse.
