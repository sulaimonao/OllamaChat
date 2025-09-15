import asyncio
import feedparser
import httpx
import yaml
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from trafilatura import extract
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import hashlib
from tools.search_engine import SearchEngine
from pathlib import Path
import logging
from urllib.parse import urlparse
from search.urlnorm import canonicalize

logger = logging.getLogger(__name__)

# --- Pydantic Models ---

class RssRequest(BaseModel):
    max_items: int = 20

class RssResponseItem(BaseModel):
    title: str
    url: str
    published: str

class RssResponse(BaseModel):
    items: List[RssResponseItem]
    error: Optional[str] = None

class SiteSearchRequest(BaseModel):
    query: str
    max_items: int = 20

class SiteSearchResponseItem(BaseModel):
    title: str
    url: str

class SiteSearchResponse(BaseModel):
    items: List[SiteSearchResponseItem]
    error: Optional[str] = None

class FetchRequest(BaseModel):
    urls: List[str]

class FetchResponseItem(BaseModel):
    url: str
    title: str
    text: str
    meta: Dict[str, Any] = {}

class IngestRequest(BaseModel):
    items: List[Dict[str, Any]]

class IngestResponse(BaseModel):
    message: str
    indexed_files: List[str]

# --- Router ---

router = APIRouter()

# --- Configuration ---

DEFAULT_CONFIG = {
  "rss_feeds": [
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.theverge.com/rss/index.xml",
    "https://www.reuters.com/rssFeed/topNews",
    "https://hnrss.org/frontpage",
    "https://www.npr.org/rss/rss.php?id=1001",
    "https://www.nature.com/subjects/artificial-intelligence.rss",
    "https://ai.googleblog.com/feeds/posts/default",
    "https://openai.com/blog/rss.xml",
    "https://www.deepmind.com/blog/rss.xml",
    "https://venturebeat.com/category/ai/feed"
  ],
  "site_search_templates": [
    {"domain":"arstechnica.com", "template":"https://arstechnica.com/search/?query={q}", "result_link_css":"ol.search-results li a"},
    {"domain":"theverge.com",    "template":"https://www.theverge.com/search?q={q}",    "result_link_css":"a[data-analytics-link='article']"},
    {"domain":"reuters.com",     "template":"https://www.reuters.com/site-search/?query={q}", "result_link_css":"a.search-result-title"},
    {"domain":"npr.org",         "template":"https://www.npr.org/search?query={q}",     "result_link_css":"article .item-info a"},
    {"domain":"nature.com",      "template":"https://www.nature.com/search?q={q}",      "result_link_css":"li.app-article-list-row__item a"},
    {"domain":"venturebeat.com", "template":"https://venturebeat.com/?s={q}",           "result_link_css":"h2 > a"},
    {"domain":"techcrunch.com",  "template":"https://techcrunch.com/search/{q}/",       "result_link_css":"a.post-block__title__link"}
  ],
  "ingest_policy": {
    "min_reliability": 0.55,
    "freshness_days": 7,
    "blocklist_domains": ["x.com", "pinterest.com", "facebook.com"],
    "allowlist_domains": [],
    "max_per_domain": 30,
    "dedupe_by": ["canonical_url","sha1_text"]
  },
  "topic_hubs": {
    "general": [
      "https://www.reuters.com/",
      "https://www.bbc.com/news",
      "https://www.npr.org/sections/news/",
      "https://arstechnica.com/",
      "https://www.theverge.com/",
      "https://news.ycombinator.com/"
    ],
    "ai": [
      "https://www.nature.com/subjects/artificial-intelligence",
      "https://ai.googleblog.com/",
      "https://openai.com/blog",
      "https://www.deepmind.com/blog",
      "https://venturebeat.com/category/ai/",
      "https://techcrunch.com/tag/ai/"
    ]
  }
}

def get_config():
    here = Path(__file__).resolve()
    cfg_path = here.parents[1] / "config" / "sources.yaml"
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        merged = DEFAULT_CONFIG.copy()
        for k,v in (data or {}).items():
            merged[k] = v
        return merged
    import logging
    logging.getLogger(__name__).warning("sources.yaml not found; using DEFAULT_CONFIG")
    return DEFAULT_CONFIG



# --- Endpoints ---

@router.get("/tools/live/sources")
def get_sources_config():
    """Returns the effective merged config."""
    return get_config()

@router.post("/tools/live/rss_latest", response_model=RssResponse)
async def rss_latest(request: RssRequest) -> RssResponse:
    """
    Load RSS feeds from sources.yaml and return the latest items.
    """
    try:
        config = get_config()
        rss_feeds = config.get("rss_feeds", [])
        items = []

        async def fetch_feed(feed_url):
            try:
                d = feedparser.parse(feed_url)
                for entry in d.entries:
                    items.append(
                        RssResponseItem(
                            title=entry.title,
                            url=entry.link,
                            published=entry.get("published", "N/A"),
                        )
                    )
            except Exception as e:
                logger.warning(f"Error fetching RSS feed {feed_url}: {e}")

        await asyncio.gather(*[fetch_feed(url) for url in rss_feeds])
        return RssResponse(items=items[:request.max_items])
    except Exception as e:
        logger.warning("rss_latest failed: %s", e)
        return RssResponse(items=[], error=str(e))


@router.post("/tools/live/site_search", response_model=SiteSearchResponse)
async def site_search(request: SiteSearchRequest) -> SiteSearchResponse:
    """
    For each template in sources.yaml, format {q}, GET page, parse links, and return them.
    """
    try:
        config = get_config()
        templates = config.get("site_search_templates", [])
        items = []

        async with httpx.AsyncClient() as client:
            for template in templates:
                url = template["template"].format(q=request.query)
                try:
                    response = await client.get(url, follow_redirects=True, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")
                    links = soup.select(template["result_link_css"])
                    for link in links:
                        items.append(
                            SiteSearchResponseItem(
                                title=link.get_text(strip=True),
                                url=link.get("href")
                            )
                        )
                except httpx.RequestError as e:
                    logger.warning(f"Error fetching {url}: {e}")
                except Exception as e:
                    logger.warning(f"Error processing {url}: {e}")

        seen_urls = set()
        deduped_items = []
        for item in items:
            if item.url and item.url not in seen_urls:
                seen_urls.add(item.url)
                deduped_items.append(item)

        return SiteSearchResponse(items=deduped_items[:request.max_items])
    except Exception as e:
        logger.warning("site_search failed: %s", e)
        return SiteSearchResponse(items=[], error=str(e))

@router.post("/tools/live/fetch", response_model=List[FetchResponseItem])
async def fetch(request: FetchRequest):
    """
    Fetch a URL, extract content with trafilatura, and return the text.
    """
    async def fetch_one(url: str):
        try:
            await asyncio.sleep(0.5)
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True, timeout=15)
                response.raise_for_status()
                html_content = response.text

            text = extract(html_content, include_comments=False, include_tables=False)
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.string if soup.title else "No title found"

            if not text:
                return None

            meta = {"fetched_at": datetime.utcnow().isoformat(), "length": len(text)}
            return FetchResponseItem(url=url, title=title, text=text, meta=meta)
        except httpx.RequestError as e:
            logger.warning(f"Error fetching URL {url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"An error occurred processing {url}: {e}")
            return None

    tasks = [fetch_one(url) for url in request.urls]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res]


@router.post("/tools/live/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    """
    Write content to a Markdown file with YAML front-matter and trigger the indexer.
    """
    data_dir = Path("backend/local_data/web_live/")
    data_dir.mkdir(parents=True, exist_ok=True)

    indexed_files = []
    for item in request.items:
        try:
            url = item['url']
            text = item['text']
            title = item.get('title', '')
            canonical_url = canonicalize(item.get('canonical_url', url))
            sha1_text = hashlib.sha1(text.encode('utf-8')).hexdigest()
            url_hash = hashlib.sha1(canonical_url.encode('utf-8')).hexdigest()[:16]
            domain = urlparse(canonical_url).netloc or "unknown"
            domain_dir = data_dir / domain
            domain_dir.mkdir(parents=True, exist_ok=True)

            # dedupe by canonical_url or sha1_text
            existing_canon = set()
            existing_sha = set()
            for fp in domain_dir.glob("*.md"):
                try:
                    with fp.open('r', encoding='utf-8') as f:
                        if f.readline().strip() != '---':
                            continue
                        meta_lines = []
                        for line in f:
                            if line.strip() == '---':
                                break
                            meta_lines.append(line)
                    meta = yaml.safe_load(''.join(meta_lines)) or {}
                    existing_canon.add(canonicalize(meta.get('canonical_url', '')))
                    existing_sha.add(meta.get('sha1_text'))
                except Exception:
                    continue
            if canonical_url in existing_canon or sha1_text in existing_sha:
                continue

            filepath = domain_dir / f"{url_hash}.md"
            ingested_at = datetime.utcnow().isoformat()
            front_matter = {
                "source": "web_live",
                "url": url,
                "canonical_url": canonical_url,
                "title": title,
                "sha1_text": sha1_text,
                "ingested_at": ingested_at,
            }
            content = f"---\n{yaml.dump(front_matter)}---\n\n{text}"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            indexed_files.append(str(filepath))
        except Exception as e:
            logger.error(f"Failed to ingest item {item.get('url', 'N/A')}: {e}")

    if indexed_files:
        try:
            search_engine = SearchEngine()
            search_engine.index(indexed_files)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to index documents: {e}")

    return IngestResponse(message=f"Ingested and indexed {len(indexed_files)} documents.", indexed_files=indexed_files)
