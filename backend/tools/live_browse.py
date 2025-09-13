import os
import datetime
import yaml
import httpx
import feedparser
import trafilatura
import asyncio
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

from tools.search_engine import SearchEngine

# --- Configuration ---

def load_sources_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'sources.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="sources.yaml not found.")
    except yaml.YAMLError as e:
        raise HTTPException(status_code=500, detail=f"Error parsing sources.yaml: {e}")

# --- Pydantic Models ---

class RssRequest(BaseModel):
    num_items: int = Field(default=5, description="Number of items to return per feed.")

class SiteSearchRequest(BaseModel):
    query: str = Field(..., description="The search query.")

class FetchRequest(BaseModel):
    url: str = Field(..., description="The URL to fetch.")

class IngestRequest(BaseModel):
    url: str = Field(..., description="The source URL of the content.")
    title: str = Field(..., description="The title of the content.")
    text: str = Field(..., description="The text content to ingest.")

class IngestResponse(BaseModel):
    message: str
    filepath: str

# --- API Router ---

router = APIRouter(prefix="/tools/live", tags=["Live Browsing"])

# --- Endpoints ---

@router.post("/rss_latest")
async def rss_latest(request: RssRequest):
    """
    Load feeds from backend/config/sources.yaml and return the latest items.
    """
    config = load_sources_config()
    rss_feeds = config.get("rss_feeds", [])
    all_items = []

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        tasks = [client.get(feed["url"]) for feed in rss_feeds]
        responses = await asyncio.gather(*[asyncio.create_task(t) for t in tasks], return_exceptions=True)

    for i, response in enumerate(responses):
        feed_info = rss_feeds[i]
        if isinstance(response, httpx.Response):
            try:
                feed = feedparser.parse(response.text)
                for entry in feed.entries[:request.num_items]:
                    all_items.append({
                        "title": entry.title,
                        "url": entry.link,
                        "published": entry.get("published", "N/A"),
                        "source": feed_info.get("name", feed.feed.title)
                    })
            except Exception as e:
                print(f"Error parsing feed {feed_info['url']}: {e}") # Log error
        else:
            print(f"Error fetching feed {feed_info['url']}: {response}") # Log error

    # Sort by published date, if available
    try:
        all_items.sort(key=lambda x: feedparser._parse_date(x['published']), reverse=True)
    except Exception:
        # If dates are not available or parsable, just leave as is
        pass

    return {"items": all_items}

@router.post("/site_search")
async def site_search(request: SiteSearchRequest):
    """
    For each template in sources.yaml, format {q}, GET page, parse links, dedupe, and return.
    """
    config = load_sources_config()
    templates = config.get("site_search_templates", [])
    all_links = set()

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        tasks = []
        for template in templates:
            url = template["search_url_template"].format(q=request.query)
            tasks.append(client.get(url))

        responses = await asyncio.gather(*[asyncio.create_task(t) for t in tasks], return_exceptions=True)

    for i, response in enumerate(responses):
        template = templates[i]
        if isinstance(response, httpx.Response):
            try:
                soup = BeautifulSoup(response.text, "html.parser")
                links = soup.select(template["results_link_selector"])
                for link in links:
                    href = link.get("href")
                    if href:
                        # Make sure the URL is absolute
                        absolute_url = httpx.URL(template["search_url_template"]).join(href)
                        all_links.add((link.get_text(strip=True), str(absolute_url)))
            except Exception as e:
                print(f"Error processing site search for {template['domain']}: {e}")
        else:
            print(f"Error fetching site search for {template['domain']}: {response}")

    return {"results": [{"title": title, "url": url} for title, url in all_links]}

@router.post("/fetch")
async def fetch(request: FetchRequest):
    """
    Fetch a URL, extract content with trafilatura, and return the text.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(request.url)
            response.raise_for_status()

        # Trafilatura extracts main text and title
        extracted_text = trafilatura.extract(response.text, include_comments=False, favor_precision=True)

        # Fallback to BeautifulSoup for title if trafilatura fails
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "No title found"

        if not extracted_text:
            # Basic fallback if trafilatura fails
            extracted_text = "Could not extract main content."

        return {"url": request.url, "title": title, "text": extracted_text}

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error fetching URL: {e}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error fetching URL: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    """
    Write Markdown files with YAML front-matter and trigger the indexer.
    """
    try:
        # Define the directory for live web data
        live_data_dir = os.path.join(os.path.dirname(__file__), '..', 'local_data', 'web_live')
        os.makedirs(live_data_dir, exist_ok=True)

        # Sanitize the title for the filename
        safe_filename = "".join(c for c in request.title if c.isalnum() or c in (' ', '_')).rstrip()
        if not safe_filename:
            safe_filename = f"ingested_{datetime.datetime.utcnow().timestamp()}"
        filepath = os.path.join(live_data_dir, f"{safe_filename}.md")

        # Create the content with YAML front-matter
        ingested_at = datetime.datetime.utcnow().isoformat()
        front_matter = {
            "source": "web_live",
            "url": request.url,
            "title": request.title,
            "ingested_at": ingested_at
        }
        content = f"---\n{yaml.dump(front_matter)}---\n\n{request.text}"

        # Write the file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Trigger the indexer
        search_engine = SearchEngine() # Uses default config
        search_engine.index([filepath])

        return {"message": "Content ingested and indexed successfully.", "filepath": filepath}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during ingestion: {e}")
