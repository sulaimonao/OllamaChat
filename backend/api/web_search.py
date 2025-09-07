# backend/api/web_search.py
from fastapi import APIRouter, Query, HTTPException
import httpx
import logging
import json
from langchain.tools import tool

router = APIRouter()

def _perform_duckduckgo_search(query: str):
    """
    Performs a search using the DuckDuckGo API and returns the results.
    """
    try:
        response = httpx.get("https://api.duckduckgo.com", params={
            "q": query,
            "format": "json",
            "no_redirect": 1,
            "no_html": 1,
        })
        response.raise_for_status()
        data = response.json()

        # Extract relevant information
        results = []
        if "Results" in data and data["Results"]:
            for r in data["Results"]:
                results.append({
                    "title": r.get("Text"),
                    "url": r.get("FirstURL"),
                    "snippet": r.get("Result"),
                })
        elif "RelatedTopics" in data and data["RelatedTopics"]:
            for r in data["RelatedTopics"]:
                # Filter out sub-topics which have no URL
                if r.get("FirstURL"):
                    results.append({
                        "title": r.get("Text"),
                        "url": r.get("FirstURL"),
                        "snippet": r.get("Result"),
                    })
        return results
    except Exception as e:
        logging.error(f"Error performing web search: {e}")
        return []

@tool
def web_search(query: str) -> str:
    """
    Performs a web search using DuckDuckGo for the given query.
    Returns a JSON string with the search results.
    """
    search_results = _perform_duckduckgo_search(query)
    return json.dumps(search_results)


@router.get("/search")
async def web_search_endpoint(query: str = Query(..., description="Search query")):
    try:
        results = _perform_duckduckgo_search(query)
        return {"results": results}
    except Exception as e:
        # The _perform_duckduckgo_search function already logs the error.
        # We just need to raise the HTTP exception.
        raise HTTPException(status_code=500, detail="Web search failed")