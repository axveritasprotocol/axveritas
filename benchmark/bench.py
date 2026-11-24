"""Axveritas dead-end benchmark.

Samples domains from the Tranco top-1M list, fetches each homepage once (and one
internal "deep" page for reachable sites) with the same User-Agent and verdict
rules as Axveritas /v1/preflight, and records results to JSONL.

Usage: python -I bench.py <tranco_csv> <out_jsonl>
"""
import asyncio, csv, json, random, re, sys, time
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

SEED = 20261123
UA = "Mozilla/5.0 (compatible; AxveritasPreflight/3.5; +https://axveritas.onrender.com)"
TIMEOUT = 8.0
CONCURRENCY = 12
TIERS = [("top_1k", 1, 1000, 350), ("1k_10k", 1001, 10000, 350), ("10k_100k", 10001, 100000, 300)]
CF_MARKERS = ("cf-browser-verification", "attention required! | cloudflare", "cf-chl-", "just a moment...")
OTHER_WAF = ("captcha", "access denied", "are you a robot", "px-captcha", "datadome", "perimeterx", "incapsula")


def classify(status, html):
    """Mirror Axveritas /v1/preflight rules, plus a finer category for the report."""
    low = html[:4000].lower()
    if status in (401, 403, 429, 503) or any(m in low for m in CF_MARKERS):
        verdict, cat = "DEAD_END", "blocked"
    elif status >= 400:
        verdict, cat = "DEAD_END", "broken"
    elif len(html.strip()) < 120:
        verdict, cat = "DEAD_END", "empty"
    else:
        verdict, cat = "PASSABLE", "ok"
    # Finer signal (not used by Axveritas today): 200 OK pages that are really walls or JS shells.
    soft = None
    if verdict == "PASSABLE":
        soup = BeautifulSoup(html, "html.parser")
        for t in soup(["script", "style", "noscript", "svg"]):
            t.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        if any(m in low for m in OTHER_WAF) and len(text) < 1500:
            soft = "soft_block"
        elif len(text) < 200:
            soft = "js_shell"
    return verdict, cat, soft


def pick_deep_link(base_url, html):
    host = urlparse(base_url).hostname or ""
    root = host.removeprefix("www.")
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        u = urljoin(base_url, a["href"])
        p = urlparse(u)
        if p.scheme in ("http", "https") and p.hostname and p.hostname.removeprefix("www.").endswith(root):
            if p.path.count("/") >= 2 and len(p.path) > 8 and not re.search(r"\.(jpg|png|pdf|zip|css|js)$", p.path, re.I):
                return u
    return None


async def probe(client, url):
    t0 = time.time()
    try:
        r = await client.get(url)
        html = r.text if "html" in r.headers.get("content-type", "html") else r.text[:5000]
        verdict, cat, soft = classify(r.status_code, html)
        return {"url": url, "final_url": str(r.url), "status": r.status_code, "verdict": verdict, "category": cat,
                "soft": soft, "bytes": len(r.content), "ms": int((time.time() - t0) * 1000), "server": r.headers.get("server", "")}, html
    except Exception as e:
        kind = type(e).__name__
        cat = "unreachable" if kind in ("ConnectError", "UnsupportedProtocol") else ("timeout" if "Timeout" in kind else "error")
        return {"url": url, "status": 0, "verdict": "DEAD_END", "category": cat, "soft": None, "bytes": 0,
                "ms": int((time.time() - t0) * 1000), "error": f"{kind}: {str(e)[:120]}"}, ""


async def main(tranco_csv, out_path):
    rows = {}
    with open(tranco_csv, newline="") as f:
        for rank, domain in csv.reader(f):
            rank = int(rank)
            if rank > 100000:
                break
            rows[rank] = domain
    rng = random.Random(SEED)
    sample = []
    for tier, lo, hi, n in TIERS:
        for rank in sorted(rng.sample(range(lo, hi + 1), n)):
            sample.append((tier, rank, rows[rank]))
    sem = asyncio.Semaphore(CONCURRENCY)
    out = open(out_path, "w", encoding="utf-8")
    done = 0
    limits = httpx.Limits(max_connections=CONCURRENCY * 2)
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers={"User-Agent": UA}, limits=limits) as client:
        async def run(tier, rank, domain):
            nonlocal done
            async with sem:
                home, html = await probe(client, f"https://{domain}/")
                home.update(tier=tier, rank=rank, domain=domain, kind="homepage")
                out.write(json.dumps(home) + "\n")
                if home["verdict"] == "PASSABLE" and html:
                    deep_url = pick_deep_link(home["final_url"], html)
                    if deep_url:
                        await asyncio.sleep(1.0)  # be polite to the same host
                        deep, _ = await probe(client, deep_url)
                        deep.update(tier=tier, rank=rank, domain=domain, kind="deep")
                        out.write(json.dumps(deep) + "\n")
                out.flush()
                done += 1
                if done % 100 == 0:
                    print(f"{done}/{len(sample)} domains done", flush=True)
        await asyncio.gather(*(run(*s) for s in sample))
    out.close()
    print("FINISHED", len(sample), "domains", flush=True)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
