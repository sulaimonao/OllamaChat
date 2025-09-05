# backend/api/web_search.py
from fastapi import APIRouter, Query, HTTPException
import httpx
import logging

router = APIRouter()

@router.get("/search")
async def web_search(query: str = Query(..., description="Search query")):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.duckduckgo.com", params={
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
                    results.append({
                        "title": r.get("Text"),
                        "url": r.get("FirstURL"),
                        "snippet": r.get("Result"),
                    })

            return {"results": results}

    except Exception as e:
        logging.error(f"Error performing web search: {e}")
        raise HTTPException(status_code=500, detail="Web search failed")