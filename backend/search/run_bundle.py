from __future__ import annotations

import json
import os
import subprocess
import tempfile
from typing import List, Dict


def run_bundle(bundle: List[Dict[str, str]], limit_per_query: int = 10) -> List[Dict]:
    """Run a set of termsearch queries and collect hits."""
    tmpdb = os.environ.get("TERMSEARCH_DB")
    if not tmpdb:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        tmpdb = tmp.name
        tmp.close()

    hits: List[Dict] = []
    seen = set()
    for entry in bundle:
        q = entry["query"]
        cmd = [
            "python",
            "-m",
            "tools.termsearch.main",
            "query",
            q,
            "--db",
            tmpdb,
            "--limit",
            str(limit_per_query),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(res.stdout or "[]")
            for item in data:
                url = item.get("url")
                if not url or url in seen:
                    continue
                seen.add(url)
                item["origin"] = {"type": entry.get("type"), "query": q}
                hits.append(item)
        except Exception:
            continue
    return hits

