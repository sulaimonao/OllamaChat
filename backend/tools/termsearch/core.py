import hashlib, time, sqlite3, urllib.parse, re, io
from typing import List, Dict, Optional, Iterable, Tuple
import httpx
import trafilatura
from bs4 import BeautifulSoup

import re
_WORD_RE = re.compile(r'\S+')

def _fts_safe(text: str) -> str:
    """Sanitize text for FTS5 MATCH query."""
    text = (text or "").strip()
    if not text:
        return ""
    # De-double-quote and wrap each token in double quotes.
    # FTS5 will parse this as a phrase query for each token.
    toks = _WORD_RE.findall(text)
    return " ".join(['"{}"'.format(t.replace('"', '""')) for t in toks])

# ---------- Utilities ----------

def normalize_url(u: str) -> str:
    try:
        parts = urllib.parse.urlsplit(u)
        # drop fragment
        return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))
    except Exception:
        return u

def seed_urls_from_file(path: str) -> List[str]:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            u = line.strip()
            if u and u.startswith("http"):
                out.append(normalize_url(u))
    return out

def seed_urls_from_sitemap(sitemap_url: str) -> List[str]:
    urls = []
    with httpx.Client(follow_redirects=True, headers={"User-Agent": "termsearch/0.1"}) as client:
        r = client.get(sitemap_url, timeout=20)
        r.raise_for_status()
        text = r.text
    # Basic parse: collect <loc>...</loc>
    for m in re.finditer(r"<loc>(.*?)</loc>", text, flags=re.I|re.S):
        url = m.group(1).strip()
        if url.startswith("http"):
            urls.append(normalize_url(url))
    return urls

# ---------- Index (SQLite + FTS5) ----------

class Index:
    def __init__(self, path: str = "termsearch.db"):
        self.path = path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS docs ("
            "id INTEGER PRIMARY KEY,"
            "url TEXT UNIQUE,"
            "title TEXT,"
            "text TEXT,"
            "html_hash TEXT,"
            "fetched_at REAL"
            ");"
        )
        cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(title, text, content='docs', content_rowid='id');")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS links ("
            "src INTEGER,"
            "dst_url TEXT,"
            "depth INTEGER,"
            "FOREIGN KEY(src) REFERENCES docs(id)"
            ");"
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_links_src ON links(src);")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS ranks ("
            "doc_id INTEGER PRIMARY KEY,"
            "score REAL,"
            "FOREIGN KEY(doc_id) REFERENCES docs(id)"
            ");"
        )
        conn.commit()
        conn.close()

    def upsert(self, url: str, title: str, text: str, html_hash: str) -> int:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT id, html_hash FROM docs WHERE url=?", (url,))
        row = cur.fetchone()
        now = time.time()
        if row:
            if row["html_hash"] == html_hash:
                conn.close()
                return row["id"]
            cur.execute("UPDATE docs SET title=?, text=?, html_hash=?, fetched_at=? WHERE id=?",
                        (title, text, html_hash, now, row["id"]))
            doc_id = row["id"]
            cur.execute("INSERT INTO docs_fts(rowid, title, text) VALUES (?, ?, ?)", (doc_id, title, text))
        else:
            cur.execute("INSERT INTO docs(url, title, text, html_hash, fetched_at) VALUES (?, ?, ?, ?, ?)",
                        (url, title, text, html_hash, now))
            doc_id = cur.lastrowid
            cur.execute("INSERT INTO docs_fts(rowid, title, text) VALUES (?, ?, ?)", (doc_id, title, text))
        conn.commit()
        conn.close()
        return doc_id

    def add_links(self, src_id: int, links: Iterable[Tuple[str, int]]):
        conn = self._connect()
        cur = conn.cursor()
        cur.executemany("INSERT INTO links(src, dst_url, depth) VALUES (?, ?, ?)", ((src_id, u, d) for u, d in links))
        conn.commit()
        conn.close()

    def _normalize_scores(self, vals: List[float]) -> List[float]:
        if not vals:
            return []
        lo, hi = min(vals), max(vals)
        if hi - lo < 1e-9:
            return [1.0 for _ in vals]
        return [(v - lo) / (hi - lo) for v in vals]

    def query(self, text: str, limit: int = 10, site_filter: Optional[str] = None, mix: float = 0.0) -> List[Dict]:
        # Full-text search
        conn = self._connect()
        cur = conn.cursor()
        qtext = _fts_safe(text)
        if site_filter:
            cur.execute(
                "SELECT d.id, d.url, d.title, snippet(docs_fts, 1, '<b>', '</b>', ' … ', 12) AS snippet, "
                "bm25(docs_fts) AS bm25 "
                "FROM docs_fts JOIN docs d ON d.id = docs_fts.rowid "
                "WHERE docs_fts MATCH ? AND d.url LIKE ? "
                "ORDER BY bm25 LIMIT ?",
                (qtext, f"%{site_filter}%", limit*5)
            )
        else:
            cur.execute(
                "SELECT d.id, d.url, d.title, snippet(docs_fts, 1, '<b>', '</b>', ' … ', 12) AS snippet, "
                "bm25(docs_fts) AS bm25 "
                "FROM docs_fts JOIN docs d ON d.id = docs_fts.rowid "
                "WHERE docs_fts MATCH ? "
                "ORDER BY bm25 LIMIT ?",
                (qtext, limit*5)
            )
        rows = cur.fetchall()

        # optional pagerank mix
        ids = [r["id"] for r in rows]
        pr = { }
        if ids and mix > 0.0:
            qmarks = ",".join("?" for _ in ids)
            cur.execute(f"SELECT doc_id, score FROM ranks WHERE doc_id IN ({qmarks})", ids)
            for rr in cur.fetchall():
                pr[rr["doc_id"]] = rr["score"]

        bm25s = [r["bm25"] for r in rows]
        # lower bm25 is better; invert before normalization
        inv_bm25 = [(-b) for b in bm25s]
        bm25_norm = self._normalize_scores(inv_bm25)
        pr_vals = [pr.get(r["id"], 0.0) for r in rows]
        pr_norm = self._normalize_scores(pr_vals)

        out = []
        for i, r in enumerate(rows):
            score = (1.0 - mix) * bm25_norm[i] + mix * (pr_norm[i] if pr_norm else 0.0)
            out.append({"id": r["id"], "url": r["url"], "title": r["title"], "snippet": r["snippet"], "score": round(score, 6)})
        # final cut to limit
        out.sort(key=lambda x: x["score"], reverse=True)
        conn.close()
        return out[:limit]

    def get(self, doc_id: int) -> Optional[Dict]:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT id, url, title, text, fetched_at FROM docs WHERE id=?", (doc_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def all_docs(self):
        conn = self._connect()
        cur = conn.cursor()
        cursor = cur.execute("SELECT id, url, title, text FROM docs ORDER BY id ASC")
        for row in cursor:
            yield dict(row)
        conn.close()

    def compute_pagerank(self, iters: int = 30, damping: float = 0.85) -> int:
        # Build adjacency: map url->id for dsts
        conn = self._connect()
        cur = conn.cursor()
        # Universe
        cur.execute("SELECT id, url FROM docs")
        id2url = {row["id"]: row["url"] for row in cur.fetchall()}
        url2id = {u:i for i,u in id2url.items()}
        n = len(id2url)
        if n == 0:
            conn.close()
            return 0
        # Outlinks
        outlinks = {i: [] for i in id2url.keys()}
        for row in cur.execute("SELECT src, dst_url FROM links"):
            dst_id = url2id.get(normalize_url(row["dst_url"]))
            if dst_id is not None and row["src"] in outlinks:
                outlinks[row["src"]].append(dst_id)
        # Initialize PR
        pr = {i: 1.0 / n for i in id2url.keys()}
        for _ in range(iters):
            new = {i: (1 - damping) / n for i in id2url.keys()}
            # leakage handling (dangling nodes)
            sink_sum = sum(pr[i] for i, outs in outlinks.items() if len(outs) == 0)
            for i in new:
                new[i] += damping * sink_sum / n
            for i, outs in outlinks.items():
                if not outs:
                    continue
                share = damping * pr[i] / len(outs)
                for j in outs:
                    new[j] += share
            pr = new
        # Persist
        cur.execute("DELETE FROM ranks")
        cur.executemany("INSERT INTO ranks(doc_id, score) VALUES (?, ?)", [(i, pr[i]) for i in pr])
        conn.commit()
        conn.close()
        return n

# ---------- Crawler ----------

class RobotsCache:
    def __init__(self, client: httpx.Client, user_agent: str):
        self.client = client
        self.user_agent = user_agent
        self.cache = {}

    def allowed(self, url: str) -> bool:
        from urllib.robotparser import RobotFileParser
        parts = urllib.parse.urlsplit(url)
        base = f"{parts.scheme}://{parts.netloc}"
        robots_url = urllib.parse.urljoin(base, "/robots.txt")
        if base not in self.cache:
            try:
                r = self.client.get(robots_url, timeout=10)
                rp = RobotFileParser()
                rp.parse(r.text.splitlines())
                self.cache[base] = rp
            except Exception:
                self.cache[base] = None
        rp = self.cache.get(base)
        if rp is None:
            return False
        return rp.can_fetch(self.user_agent, url)

def extract_links(base_url: str, html: str) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    urls = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        absu = urllib.parse.urljoin(base_url, href)
        if absu.startswith("http"):
            urls.append(normalize_url(absu))
    return urls

def extract_text(html: str, url: str):
    downloaded = trafilatura.extract(html, include_comments=False, favor_precision=True, include_links=False)
    if downloaded:
        soup = BeautifulSoup(html, "lxml")
        t = soup.find("title")
        title = t.get_text(strip=True) if t else url
        return title or url, downloaded
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else url
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    return title, text

class Crawler:
    def __init__(self, index: Index, rate: float = 1.0, timeout: float = 15.0, user_agent: str = "termsearch/0.1", max_depth: int = 1):
        self.index = index
        self.rate = rate
        self.timeout = timeout
        self.user_agent = user_agent
        self.max_depth = max_depth
        self.client = httpx.Client(headers={"User-Agent": user_agent}, follow_redirects=True)
        self.robots = RobotsCache(self.client, user_agent)
        self.last_host_time = {}

    def _polite_wait(self, url: str):
        host = urllib.parse.urlsplit(url).netloc
        last = self.last_host_time.get(host, 0)
        delta = time.time() - last
        if delta < self.rate:
            time.sleep(self.rate - delta)
        self.last_host_time[host] = time.time()

    def crawl(self, seeds: List[str], max_pages: int = 50) -> Dict:
        queue = [(normalize_url(u), 0) for u in seeds if u.startswith("http")]
        seen = set()
        count = 0
        while queue and count < max_pages:
            url, depth = queue.pop(0)
            if url in seen or depth > self.max_depth:
                continue
            seen.add(url)
            if not self.robots.allowed(url):
                continue
            try:
                self._polite_wait(url)
                r = self.client.get(url, timeout=self.timeout)
                ctype = r.headers.get("content-type", "")
                if r.status_code != 200 or ("text/html" not in ctype and "application/xhtml" not in ctype):
                    continue
                html = r.text
                html_hash = hashlib.sha256(html.encode("utf-8", errors="ignore")).hexdigest()
                title, text = extract_text(html, url)
                doc_id = self.index.upsert(url, title, text, html_hash)
                if depth < self.max_depth:
                    links = extract_links(url, html)
                    next_depth = depth + 1
                    self.index.add_links(doc_id, [(u, next_depth) for u in links])
                    for u in links:
                        if u not in seen:
                            queue.append((u, next_depth))
                count += 1
            except Exception:
                continue
        return {"pages_indexed": count, "seeds": len(seeds)}
