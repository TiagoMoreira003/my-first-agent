import http.client
import os
import json
from urllib.parse import urlencode 

from ddgs import DDGS
from langchain.tools import tool

from langchain_community.retrievers import BM25Retriever
from langchain_core.tools import Tool

from retriever import docs

bm25_retriever = BM25Retriever.from_documents(docs)

ALLOWED_ENDPOINTS = {"leagues", "teams", "standings", "fixtures", "players/topscorers"}
MAX_CHARS = 8000  # keep tool output small for the model's context

@tool
def search_top_team_in_league(league_id: int) -> str:
    """
    Returns the top position team in the specified football league.
    Call find_league_id first and use the ID it returns; never guess the ID.

    Args:
        league_id (int): The ID of the football league.

    Returns:
        str: The team currently at the top position in the league.
    """

    print("starting search_top_team_in_league")
    print("league_id received:", league_id)

    # Placeholder implementation, fetch from an API 

    conn = http.client.HTTPSConnection("v3.football.api-sports.io")
    headers = {
        'x-apisports-key': os.environ.get("API_SPORTS_KEY")
        }

    conn.request("GET", "/standings?league=" + str(league_id) + "&season=" + str(2024), headers=headers)
    res = conn.getresponse()
    data = res.read()

    # Here you would parse the JSON response to extract the top team
    # For now, we return a placeholder
    json_data = json.loads(data)
    print(json_data.get("errors"), json_data.get("results"))

    if not json_data['response']:
        return f"No standings found for league {league_id}: {json_data.get('errors')}"

    top_team = json_data['response'][0]['league']['standings'][0][0]['team']['name']

    print("finished search_top_team_in_league")

    return "Top team in league " + str(league_id) + " is " + top_team 

@tool
def find_league_id(league: str) -> str:
    """
    Returns the ID of the specified football league.

    Args:
        league (str): The name of the football league.

    Returns:
        str: The ID of the league.
    """

    print("starting find_league_id")

    conn = http.client.HTTPSConnection("v3.football.api-sports.io")
    headers = {
        'x-apisports-key': os.environ.get("API_SPORTS_KEY")
        }

    conn.request("GET", "/leagues?" + urlencode({"search": league}), headers=headers)
    res = conn.getresponse()
    data = res.read()

    json_data = json.loads(data)
    if not json_data['response']:
        return "League not found: " + league

    league_id = json_data['response'][0]['league']['id']
    print("finished find_league_id")

    return "League ID for " + league + " is " + str(league_id)



@tool
def football_api(endpoint: str, params: dict) -> str:
    """
Query the API-Football v3 (v3.football.api-sports.io) with a GET request and return raw JSON.

    Endpoints and common params:
    - leagues: search (name, min 3 chars), country, id, season
    - teams: league + season, or search (name)
    - standings: league (id) + season (year the season starts, e.g. 2024)
    - fixtures: league + season, team, date (YYYY-MM-DD), live=all
    - players/topscorers: league + season

    Notes:
    - League and team IDs are not guessable; look them up with `leagues` or `teams` first.
    - The response has "errors" and "results"; if results is 0, fix the params and retry.
    - Data is limited by plan, so try an earlier season if one returns nothing.
    """
    if endpoint not in ALLOWED_ENDPOINTS:
        return f"Unknown endpoint '{endpoint}'. Allowed: {sorted(ALLOWED_ENDPOINTS)}"

    path = f"/{endpoint}?{urlencode(params or {})}"
    conn = http.client.HTTPSConnection("v3.football.api-sports.io")
    conn.request("GET", path, headers={"x-apisports-key": os.environ["API_SPORTS_KEY"]})
    body = conn.getresponse().read().decode()
    return body[:MAX_CHARS]

@tool
def web_search_tool(query: str) -> str:
    """Search the web (DuckDuckGo) and return the top results as title, URL and snippet.

    Use for football news or facts the football_api cannot answer. Do not search for other topics.
    Queries unrelated to football will be ignored.
    Only provide results relevant to football.

    Use small queries (3 to 4 words), if it fails try with different keywords or simplify the query.
    """
    try:
        results = DDGS().text(query, max_results=5)
        return "\n\n".join(f"{r['title']}\n{r['href']}\n{r['body']}" for r in results)
    except Exception as e:
        return f"Search failed: {e}. Try a shorter, simpler query"

@tool(name_or_callable="best_club_info")
def best_club_info(query: str) -> str:
    """Retrieves detailed information about Portuguese football clubs based on their name."""
    results = bm25_retriever.invoke(query)
    if results:
        return "\n\n".join([doc.page_content for doc in results[:3]])
    else:
        return "No matching guest information found."

@tool(name_or_callable="best_club_info")
def best_club_info(query: str) -> str:
    """Retrieves detailed information about Portuguese football clubs based on their name."""
    results = bm25_retriever.invoke(query)
    if results:
        return "\n\n".join([doc.page_content for doc in results[:3]])
    else:
        return "No matching guest information found."
