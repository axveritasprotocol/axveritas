"""Page-cleaning test: raw HTML size vs the clean text Axveritas /v1/scrape returns.

Re-fetches up to 200 pages that loaded fine in the Tranco benchmark and applies the
exact /v1/scrape extraction (strip script/style/noscript/svg, collapse whitespace, 15,000-char cap).
Usage: python -I cleaning.py <results_jsonl> <out_jsonl>
"""
import asyncio, json, random, re, sys
import httpx
from bs4 import BeautifulSoup
import bench


def extract(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    full = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    return full


async def main(src, out_path):
    rows = [json.loads(l) for l in open(src, encoding="utf-8")]
    ok = [r for r in rows if r["verdict"] == "PASSABLE" and not r.get("soft")]
    random.Random(bench.SEED).shuffle(ok)
    ok = ok[:200]
    sem = asyncio.Semaphore(10)
    out = open(out_path, "w", encoding="utf-8")
    async with httpx.AsyncClient(timeout=bench.TIMEOUT, follow_redirects=True, headers={"User-Agent": bench.UA}) as client:
        async def run(r):
            async with sem:
                try:
                    resp = await client.get(r.get("final_url") or r["url"])
                    if resp.status_code >= 400:
                        return
                    raw = resp.text
                    full = extract(raw)
                    out.write(json.dumps({"url": r["url"], "kind": r["kind"], "raw_chars": len(raw),
                                          "clean_chars_full": len(full), "clean_chars_capped": min(len(full), 15000)}) + "\n")
                    out.flush()
                except Exception:
                    return
        await asyncio.gather(*(run(r) for r in ok))
    out.close()
    print("FINISHED", flush=True)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
