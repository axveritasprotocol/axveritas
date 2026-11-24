"""Re-check protected sites that timed out or errored, one at a time with a 15-second timeout.

Run after protected.py so slow-but-working sites aren't counted as dead ends.
Usage: python retry_timeouts.py protected.jsonl protected_retry.json
"""
import asyncio, collections, json, sys
import httpx
import bench


async def main(src, out_path):
    rows = [json.loads(l) for l in open(src, encoding="utf-8")]
    todo = [r for r in rows if r["kind"] == "homepage" and r["category"] in ("timeout", "error")]
    sem, results = asyncio.Semaphore(3), []
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers={"User-Agent": bench.UA}) as client:
        async def one(r):
            async with sem:
                res, _ = await bench.probe(client, r["url"])
                res.update(domain=r["domain"], tier=r["tier"], kind="homepage")
                results.append(res)
        await asyncio.gather(*(one(r) for r in todo))
    json.dump(results, open(out_path, "w"))
    print("retried", len(results), dict(collections.Counter(r["category"] for r in results)))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
