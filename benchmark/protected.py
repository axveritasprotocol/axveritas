"""Protected-sites benchmark: well-known retail, travel and finance sites (homepage + one inner page).

Usage: python -I protected.py <out_jsonl>
"""
import asyncio, json, sys
import httpx
import bench  # same verdict rules, UA and timeout as the Tranco benchmark

SITES = {
    "retail": "amazon.com walmart.com target.com bestbuy.com ebay.com etsy.com homedepot.com lowes.com costco.com macys.com "
              "nordstrom.com kohls.com wayfair.com chewy.com zappos.com nike.com adidas.com ikea.com sephora.com ulta.com "
              "gap.com hm.com zara.com asos.com newegg.com bhphotovideo.com samsclub.com kroger.com cvs.com walgreens.com "
              "aliexpress.com temu.com shein.com overstock.com williams-sonoma.com rei.com dickssportinggoods.com staples.com "
              "officedepot.com apple.com",
    "travel": "booking.com expedia.com hotels.com airbnb.com tripadvisor.com kayak.com priceline.com vrbo.com marriott.com "
              "hilton.com hyatt.com ihg.com delta.com united.com aa.com southwest.com jetblue.com alaskaair.com "
              "britishairways.com lufthansa.com emirates.com ryanair.com easyjet.com skyscanner.net trip.com agoda.com "
              "hertz.com enterprise.com avis.com amtrak.com",
    "finance": "chase.com bankofamerica.com wellsfargo.com citi.com capitalone.com americanexpress.com discover.com usbank.com "
               "pnc.com schwab.com fidelity.com vanguard.com etrade.com robinhood.com paypal.com venmo.com coinbase.com "
               "kraken.com bloomberg.com wsj.com ft.com reuters.com marketwatch.com finance.yahoo.com morningstar.com "
               "nerdwallet.com bankrate.com creditkarma.com sofi.com ally.com",
    "other_high_value": "ticketmaster.com stubhub.com zillow.com realtor.com redfin.com indeed.com glassdoor.com linkedin.com "
                        "yelp.com craigslist.org",
}


async def main(out_path):
    sem = asyncio.Semaphore(8)
    out = open(out_path, "w", encoding="utf-8")
    async with httpx.AsyncClient(timeout=bench.TIMEOUT, follow_redirects=True, headers={"User-Agent": bench.UA}) as client:
        async def run(cat, domain):
            async with sem:
                home, html = await bench.probe(client, f"https://{domain}/")
                home.update(tier=cat, domain=domain, kind="homepage")
                out.write(json.dumps(home) + "\n")
                if home["verdict"] == "PASSABLE" and html:
                    deep_url = bench.pick_deep_link(home["final_url"], html)
                    if deep_url:
                        await asyncio.sleep(1.0)
                        deep, _ = await bench.probe(client, deep_url)
                        deep.update(tier=cat, domain=domain, kind="deep")
                        out.write(json.dumps(deep) + "\n")
                out.flush()
        await asyncio.gather(*(run(c, d) for c, s in SITES.items() for d in s.split()))
    out.close()
    print("FINISHED", flush=True)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
