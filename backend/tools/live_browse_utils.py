from __future__ import annotations
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List
from urllib.parse import urlparse

TRUSTED_DOMAINS = {
    "reuters.com",
    "bbc.co.uk",
    "bbc.com",
    "npr.org",
    "arstechnica.com",
    "theverge.com",
    "nature.com",
    "ai.googleblog.com",
    "openai.com",
    "deepmind.com",
    "venturebeat.com",
    "techcrunch.com",
}

def compute_reliability(doc: Dict[str, Any], policy: Dict[str, Any]) -> float:
    """Compute a crude reliability score in [0,1]."""
    score = 0.0
    url = doc.get("url", "")
    text = doc.get("text", "")
    meta = doc.get("meta", {})
    domain = urlparse(url).netloc.lower()

    if domain in TRUSTED_DOMAINS:
        score += 0.3
    if url.startswith("https://"):
        score += 0.1
    if len(text) > 1000:
        score += 0.2
    fetched_at = meta.get("fetched_at")
    if fetched_at:
        try:
            ts = datetime.fromisoformat(fetched_at)
            if datetime.utcnow() - ts < timedelta(days=policy.get("freshness_days", 7)):
                score += 0.2
        except Exception:
            pass
    if meta.get("author"):
        score += 0.1
    if text.count("http") >= 3:
        score += 0.1
    return min(score, 1.0)

AI_KEYWORDS = {"ai", "artificial intelligence", "ml", "machine learning", "gpt", "llm", "transformer"}

def pick_hubs(query: str, config: Dict[str, Any]) -> List[str]:
    hubs_cfg = config.get("topic_hubs", {})
    is_ai = any(k in query.lower() for k in AI_KEYWORDS)
    return hubs_cfg.get("ai" if is_ai else "general", [])

