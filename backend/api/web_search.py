from fastapi import APIRouter, Query, HTTPException
import logging
import json
from langchain.tools import tool
import subprocess
import tempfile
import os
import sys

router = APIRouter()

def _perform_termsearch(query: str):
    """
    Performs a search using the local termsearch crawler and returns the results.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "termsearch.db")
        # Assuming the server is run from the 'backend' directory
        seeds_path = os.path.join('tools', 'termsearch', 'news_seeds.txt')

        # 1. Crawl the seed URLs
        crawl_command = [
            sys.executable,
            "-m", "tools.termsearch.main",
            "crawl",
            "--seeds-file", seeds_path,
            "--db", db_path,
            "--depth", "1",
            "--max-pages", "20"
        ]
        try:
            # The server runs from the 'backend' directory, so paths are relative to it.
            crawl_result = subprocess.run(
                crawl_command,
                capture_output=True,
                text=True,
                timeout=300, # 5 minutes timeout for crawling
                check=True
            )
            logging.info(f"Crawl output: {crawl_result.stdout}")
            if crawl_result.stderr:
                logging.error(f"Crawl error: {crawl_result.stderr}")

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logging.error(f"Crawling failed: {e}")
            if hasattr(e, 'stderr'):
                logging.error(f"Crawler stderr: {e.stderr}")
            return []

        # 2. Query the index
        query_command = [
            sys.executable,
            "-m", "tools.termsearch.main",
            "query",
            query,
            "--db", db_path,
            "--limit", "10"
        ]
        try:
            query_result = subprocess.run(
                query_command,
                capture_output=True,
                text=True,
                timeout=60,
                check=True
            )
            if query_result.stderr:
                 logging.error(f"Query error: {query_result.stderr}")

            # The output is a JSON string, parse it
            data = json.loads(query_result.stdout)
            return data.get("hits", [])

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logging.error(f"Querying failed: {e}")
            if hasattr(e, 'stderr'):
                logging.error(f"Query stderr: {e.stderr}")
            return []


@tool
def web_search(query: str) -> str:
    """
    Performs a web search by crawling a set of news sites for the given query.
    Returns a JSON string with the search results.
    """
    search_results = _perform_termsearch(query)
    return json.dumps(search_results)


@router.get("/search")
async def web_search_endpoint(query: str = Query(..., description="Search query")):
    try:
        results = _perform_termsearch(query)
        return {"results": results}
    except Exception as e:
        logging.error(f"Web search failed: {e}")
        raise HTTPException(status_code=500, detail="Web search failed")