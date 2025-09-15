from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import yaml

DEFAULT_ALLOW_QUERY = ["arxiv.org", "nature.com"]


def _load_allow() -> list:
    cfg_path = Path(__file__).resolve().parent.parent / "config" / "search.yaml"
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("allow_query_domains", DEFAULT_ALLOW_QUERY)
    return DEFAULT_ALLOW_QUERY

ALLOW_QUERY_DOMAINS = _load_allow()


def canonicalize(url: str) -> str:
    try:
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        host = parts.hostname.lower() if parts.hostname else ""
        port = parts.port
        netloc = host
        if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
            netloc = f"{host}:{port}"
        path = re.sub(r"/+", "/", parts.path or "/").lower()
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        query = parts.query if host in ALLOW_QUERY_DOMAINS else ""
        return urlunsplit((scheme, netloc, path, query, ""))
    except Exception:
        return url

