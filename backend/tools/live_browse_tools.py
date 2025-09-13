import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# --- Tool Schemas ---

class RssInput(BaseModel):
    """Input for the rss_latest tool."""
    pass

class SiteSearchInput(BaseModel):
    """Input for the site_search tool."""
    query: str = Field(description="The search query to execute.")

class FetchInput(BaseModel):
    """Input for the fetch_url tool."""
    url: str = Field(description="The URL to fetch.")

# --- Live Browsing Tools ---

@tool(args_schema=RssInput)
def rss_latest() -> str:
    """
    Fetches the latest headlines from a predefined list of news RSS feeds.
    Use this for broad, general, or news-related queries like "what's the latest news?".
    """
    try:
        with httpx.Client() as client:
            response = client.post("http://localhost:8000/tools/live/rss_latest", json={})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return f"Error fetching RSS feeds: {e}"

@tool(args_schema=SiteSearchInput)
def site_search(query: str) -> str:
    """
    Searches a predefined list of websites for a specific query.
    Use this for topical queries about technology, science, or specific products.
    For example: "M-series chip rumors" or "latest advancements in AI".
    """
    try:
        with httpx.Client() as client:
            response = client.post("http://localhost:8000/tools/live/site_search", json={"query": query})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return f"Error performing site search: {e}"

@tool(args_schema=FetchInput)
def fetch_url(url: str) -> str:
    """
    Fetches the content of a URL, extracts the main text, and ingests it into the local index.
    Use this to read the content of a specific URL provided by the user or found in search results.
    """
    try:
        with httpx.Client() as client:
            # 1. Fetch the content
            fetch_response = client.post("http://localhost:8000/tools/live/fetch", json={"url": url})
            fetch_response.raise_for_status()
            fetched_data = fetch_response.json()

            # 2. Ingest the content
            ingest_response = client.post("http://localhost:8000/tools/live/ingest", json=fetched_data)
            ingest_response.raise_for_status()

            # Return the extracted text to the agent
            return fetched_data.get("text", "Content fetched and ingested, but no text was returned.")

    except Exception as e:
        return f"Error fetching or ingesting URL {url}: {e}"
