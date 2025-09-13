import json, typer
from typing import Optional
from .core import Crawler, get_index, seed_urls_from_sitemap, seed_urls_from_file

app = typer.Typer(help="termsearch (no-API) — crawl & search locally")

@app.command()
def crawl(urls: Optional[str] = typer.Option(None, help="Comma-separated URLs to seed"),
          sitemap: Optional[str] = typer.Option(None, help="Sitemap URL to seed"),
          seeds_file: Optional[str] = typer.Option(None, help="Text file with one URL per line"),
          db: str = typer.Option(None, help="SQLite index path (defaults to centralized path)"),
          max_pages: int = typer.Option(50),
          rate: float = typer.Option(1.0, help="Seconds between requests to the same host"),
          depth: int = typer.Option(1, help="Link depth from seeds"),
          timeout: float = typer.Option(15.0),
          user_agent: str = typer.Option("termsearch/0.1 (+local)")):
    idx = get_index(db) if db else get_index()
    seeds = []
    if urls:
        seeds += [u.strip() for u in urls.split(",") if u.strip()]
    if sitemap:
        seeds += seed_urls_from_sitemap(sitemap)
    if seeds_file:
        seeds += seed_urls_from_file(seeds_file)
    seeds = list(dict.fromkeys(seeds))  # dedupe while keeping order
    c = Crawler(idx, rate=rate, timeout=timeout, user_agent=user_agent, max_depth=depth)
    stats = c.crawl(seeds, max_pages=max_pages)
    typer.echo(json.dumps({"crawled": stats}, indent=2))

@app.command()
def rank(db: str = typer.Option(None), iters: int = typer.Option(30), damping: float = typer.Option(0.85)):
    idx = get_index(db) if db else get_index()
    n = idx.compute_pagerank(iters=iters, damping=damping)
    typer.echo(json.dumps({"pagerank_nodes": n, "iters": iters, "damping": damping}, indent=2))

@app.command()
def query(text: str,
          db: str = typer.Option(None, help="SQLite index path"),
          limit: int = typer.Option(10),
          site: Optional[str] = typer.Option(None, help="Filter by site/domain contains this substring"),
          mix: float = typer.Option(0.0, help="Mix factor [0..1] to blend BM25 with PageRank (score = (1-mix)*bm25_norm + mix*pr_norm)")):
    idx = get_index(db) if db else get_index()
    hits = idx.query(text, limit=limit, site_filter=site, mix=mix)
    typer.echo(json.dumps({"query": text, "hits": hits}, ensure_ascii=False, indent=2))

@app.command()
def show(doc_id: int, db: str = typer.Option(None)):
    idx = get_index(db) if db else get_index()
    doc = idx.get(doc_id)
    if not doc:
        raise typer.Exit(code=1)
    typer.echo(json.dumps(doc, ensure_ascii=False, indent=2))

@app.command()
def export(out: str = typer.Option("docs.jsonl"), db: str = typer.Option(None)):
    idx = get_index(db) if db else get_index()
    count = 0
    with open(out, "w", encoding="utf-8") as f:
        for doc in idx.all_docs():
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            count += 1
    typer.echo(json.dumps({"exported": count, "file": out}, indent=2))

if __name__ == "__main__":
    app()
