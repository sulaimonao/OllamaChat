from __future__ import annotations

import asyncio
import hashlib
from typing import List, Dict
from urllib.parse import urlparse

import numpy as np
from sentence_transformers import SentenceTransformer

from tools.live_browse import fetch, ingest, FetchRequest, IngestRequest
from tools.live_browse_utils import compute_reliability
from search.urlnorm import canonicalize
from search.query_bundle import CONFIG

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _embed(text: str) -> np.ndarray:
    m = _get_model()
    return m.encode([text])[0]


def compute_relevance(query: str, doc: str) -> float:
    a = _embed(query)
    b = _embed(doc)
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return float(np.dot(a, b))


def select_and_ingest(user_query: str, hits: List[Dict]) -> List[Dict]:
    cfg = CONFIG
    policy = fetch_config()
    threshold = cfg["thresholds"].get("relevance", 0.70)
    min_rel = policy.get("min_reliability", 0)

    uniq = []
    seen = set()
    for h in hits:
        url = h.get("url")
        if not url:
            continue
        canon = canonicalize(url)
        if canon in seen:
            continue
        seen.add(canon)
        h["canonical_url"] = canon
        uniq.append(h)

    if not uniq:
        return []

    fetched = asyncio.run(fetch(FetchRequest(urls=[u["url"] for u in uniq])))
    fetched_map = {f.url: f for f in fetched}

    accepted = []
    q_emb = _embed(user_query)
    for h in uniq:
        f = fetched_map.get(h["url"])
        if not f:
            continue
        text = f.text
        title = f.title
        relevance = compute_relevance(user_query, text)
        rel = compute_reliability(f.dict(), policy)
        if relevance >= threshold and rel >= min_rel:
            sha1_text = hashlib.sha1(text.encode("utf-8")).hexdigest()
            accepted.append({
                "url": h["url"],
                "canonical_url": h["canonical_url"],
                "title": title,
                "text": text,
                "relevance": relevance,
                "reliability": rel,
                "published_ts": f.meta.get("published_ts", 0),
                "host": urlparse(h["canonical_url"]).netloc,
                "sha1_text": sha1_text,
            })

    if not accepted:
        return []

    ingest_items = [
        {
            "url": d["url"],
            "canonical_url": d["canonical_url"],
            "title": d["title"],
            "text": d["text"],
        }
        for d in accepted
    ]
    asyncio.run(ingest(IngestRequest(items=ingest_items)))

    accepted.sort(key=lambda d: (
        -d["relevance"],
        -d["reliability"],
        -d.get("published_ts", 0),
        d["host"],
        hashlib.sha1(d["canonical_url"].encode("utf-8")).hexdigest(),
    ))
    return accepted


def fetch_config():
    from tools.live_browse import get_config
    cfg = get_config()
    return cfg.get("ingest_policy", {})

