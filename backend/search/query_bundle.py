from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict
import yaml

DEFAULT_CONFIG = {
    "trusted_domains": [
        "nature.com",
        "reuters.com",
        "arxiv.org",
        "npr.org",
        "arstechnica.com",
        "theverge.com",
    ],
    "blocklist_domains": [
        "x.com",
        "facebook.com",
        "pinterest.com",
    ],
    "allow_query_domains": [
        "arxiv.org",
        "nature.com",
    ],
    "thresholds": {
        "relevance": 0.70,
    },
    "limits": {
        "per_query": 10,
        "per_domain": 30,
    },
}


def _load_config() -> Dict:
    cfg_path = Path(__file__).resolve().parent.parent / "config" / "search.yaml"
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        cfg = DEFAULT_CONFIG.copy()
        for k in ("trusted_domains", "blocklist_domains", "allow_query_domains"):
            if k in data:
                cfg[k] = data[k]
        if "thresholds" in data:
            cfg["thresholds"].update(data["thresholds"] or {})
        if "limits" in data:
            cfg["limits"].update(data["limits"] or {})
        return cfg
    return DEFAULT_CONFIG

CONFIG = _load_config()


def _escape(text: str) -> str:
    return text.replace("'", "\\'")


def _trim(q: str) -> str:
    return q[:120]


def build_query_bundle(user_query: str) -> List[Dict[str, str]]:
    """Build four query variants for termsearch."""
    uq = _escape(user_query.strip())
    tokens = [t for t in re.findall(r"\w+", uq)]
    precision_terms = " ".join(f"+{t}" for t in tokens)
    precision = _trim(f'+"{uq}" {precision_terms} --QDF=4')

    recall = _trim(" ".join(tokens))

    exploration_terms = " OR ".join(sorted(set(tokens)))
    exploration = _trim(f'({exploration_terms}) --QDF=4')

    domains = CONFIG.get("trusted_domains", [])
    site_filter = " OR ".join(f"site:{d}" for d in domains)
    validation = _trim(f'"{uq}" {site_filter}')

    return [
        {"type": "precision", "query": precision},
        {"type": "recall", "query": recall},
        {"type": "exploration", "query": exploration},
        {"type": "validation", "query": validation},
    ]

