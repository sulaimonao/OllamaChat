# backend/api/web_search.py
from fastapi import APIRouter, Query, HTTPException
import requests
import logging

router = APIRouter()

@router.get("/search")
def web_search(query: str = Query(..., description="Search query")):
    try:
        response = requests.get("https://api.duckduckgo.com", params={
            "q": query,
            "format": "json",
            "no_redirect": 1,
            "no_html": 1,
        })
        response.raise_for_status()
        data = response.json()
        results = {
            "abstract": data.get("AbstractText", ""),
            "related_topics": data.get("RelatedTopics", [])
        }
        return results
    except Exception as e:
        logging.error(f"Error performing web search: {e}")
        raise HTTPException(status_code=500, detail="Web search failed")