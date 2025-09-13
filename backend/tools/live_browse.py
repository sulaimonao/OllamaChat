import asyncio
import feedparser
import httpx
import yaml
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from trafilatura import fetch_url, extract
from typing import List, Dict, Any
from datetime import datetime
import os
import hashlib
from .search_engine import SearchEngine

# --- Pydantic Models ---

class RssRequest(BaseModel):
    pass

class RssResponseItem(BaseModel):
    title: str
    url: str
    published: str

class SiteSearchRequest(BaseModel):
    query: str

class SiteSearchResponseItem(BaseModel):
    title: str
    url: str

class FetchRequest(BaseModel):
    url: str

class FetchResponse(BaseModel):
    url: str
    title: str
    text: str

class IngestRequest(BaseModel):
    url: str
    title: str
    text: str

class IngestResponse(BaseModel):
    message: str
    document_path: str

# --- Router ---

router = APIRouter()

# --- Configuration ---

def get_config():
    with open("backend/config/sources.yaml", "r") as f:
        return yaml.safe_load(f)

# --- Endpoints ---

@router.post("/tools/live/rss_latest", response_model=List[RssResponseItem])
async def rss_latest(request: RssRequest):
    """
    Load RSS feeds from sources.yaml and return the latest items.
    """
    config = get_config()
    rss_feeds = config.get("rss_feeds", [])
    items = []

    async def fetch_feed(feed):
        try:
            d = feedparser.parse(feed["url"])
            for entry in d.entries:
                items.append(
                    RssResponseItem(
                        title=entry.title,
                        url=entry.link,
                        published=entry.get("published", "N/A"),
                    )
                )
        except Exception as e:
            # In a real app, you'd want to log this error
            print(f"Error fetching RSS feed {feed['url']}: {e}")

    await asyncio.gather(*[fetch_feed(feed) for feed in rss_feeds])
    return items

@router.post("/tools/live/site_search", response_model=List[SiteSearchResponseItem])
async def site_search(request: SiteSearchRequest):
    """
    For each template in sources.yaml, format {q}, GET page, parse links, and return them.
    """
    config = get_config()
    templates = config.get("site_search_templates", [])
    items = []

    async with httpx.AsyncClient() as client:
        for template in templates:
            url = template["url_template"].format(q=request.query)
            try:
                response = await client.get(url, follow_redirects=True, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                links = soup.select(template["css_selector"])
                for link in links:
                    items.append(
                        SiteSearchResponseItem(
                            title=link.get_text(strip=True),
                            url=link.get("href")
                        )
                    )
            except httpx.RequestError as e:
                print(f"Error fetching {url}: {e}")
            except Exception as e:
                print(f"Error processing {url}: {e}")

    # Deduplicate results
    seen_urls = set()
    deduped_items = []
    for item in items:
        if item.url and item.url not in seen_urls:
            seen_urls.add(item.url)
            deduped_items.append(item)

    return deduped_items

@router.post("/tools/live/fetch", response_model=FetchResponse)
async def fetch(request: FetchRequest):
    """
    Fetch a URL, extract content with trafilatura, and return the text.
    """
    try:
        # Use httpx to fetch the page content
        async with httpx.AsyncClient() as client:
            response = await client.get(request.url, follow_redirects=True, timeout=15)
            response.raise_for_status()
            html_content = response.text

        # Use trafilatura to extract the main content and title
        text = extract(html_content, include_comments=False, include_tables=False)

        # Use BeautifulSoup to get the title
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "No title found"

        if not text:
            raise HTTPException(status_code=404, detail="Could not extract content from URL.")

        return FetchResponse(url=request.url, title=title, text=text)
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error fetching URL: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@router.post("/tools/live/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    """
    Write content to a Markdown file with YAML front-matter and trigger the indexer.
    """
    data_dir = "backend/local_data/web_live/"
    os.makedirs(data_dir, exist_ok=True)

    # Generate a unique filename
    url_hash = hashlib.sha256(request.url.encode()).hexdigest()
    filename = f"{url_hash}.md"
    filepath = os.path.join(data_dir, filename)

    # Create the content with YAML front-matter
    ingested_at = datetime.utcnow().isoformat()
    front_matter = {
        "source": "web_live",
        "url": request.url,
        "title": request.title,
        "ingested_at": ingested_at,
    }
    content = f"---\n{yaml.dump(front_matter)}---\n\n{request.text}"

    # Write the file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    # Trigger the indexer
    try:
        search_engine = SearchEngine()
        search_engine.index([filepath])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index document: {e}")

    return IngestResponse(message="Document ingested and indexed.", document_path=filepath)
