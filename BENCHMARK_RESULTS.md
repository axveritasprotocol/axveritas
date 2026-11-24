# Axveritas Dead-End Benchmark — November 2026

**Question:** How often does a bot hit a dead end when it visits a website?

**Headline:** **About 1 in 4 websites (27%) turned our bot away at the front door.** Most of them were blocked by Cloudflare.

## How we tested

- **Sites:** 1,000 domains randomly sampled from the public **Tranco top-sites list (list ID Q2464)**: 350 from the top 1,000, 350 from ranks 1,001–10,000, and 300 from ranks 10,001–100,000. Fixed random seed, so anyone can repeat it.
- **Visits:** one visit to each homepage. For homepages that loaded, one inner page (like an article or product page) linked from it, 451 in total.
- **Bot:** an honest bot identity (`AxveritasPreflight/3.5`), using the same rules as the Axveritas `/v1/preflight` check, with an 8-second timeout.
- **From:** a home internet connection on 2026-11-23. **Cloud servers, where most AI agents run, usually get blocked more**, so these numbers are likely on the low side.
- **Left out:** 250 domains that have no website (back-end services like CDNs and APIs) are not counted in the percentages.

## Results: homepages (750 real websites)

| Result | Share |
|---|---|
| ✅ Loaded fine | 72.8% |
| 🚫 **Blocked** (mostly 403 "forbidden") | **19.3%** |
| ⏱️ Timed out | 4.0% |
| 💔 Broken (404 and similar) | 2.0% |
| 📭 Empty page | 1.5% |
| ⚠️ Other connection errors | 0.4% |
| **Total dead ends** | **27.2%** |

- **Who blocks:** Cloudflare (about 6 in 10 blocks), then Akamai, Pantheon and CloudFront.
- **By popularity:** top 1,000 sites 28.7%, ranks 1k–10k 30.0%, ranks 10k–100k 22.6%.
- **Hidden dead ends:** another **10%** of sites "loaded fine" but had almost no readable content (pages that need JavaScript, or soft "are you a robot?" walls). Axveritas doesn't flag these yet.

## Results: inner pages (451 pages)

- Only **3.3%** were dead ends, because **if a site lets the bot in at the homepage, it usually lets it in everywhere.** Blocking is decided per website, which is why Axveritas caches verdicts by domain.
- Another **6.9%** were near-empty JavaScript pages.

## What a dead end costs

- **Time:** a bot takes about **0.9 seconds** (median) to discover a dead end on its own.
- **Size:** block pages are small, around **4.5 KB** median (about **1,100 tokens** if fed raw to an AI).
- **Pages that do load are big:** around **142 KB** median of raw HTML. That's where cleaning the page (`/v1/scrape`) saves the most tokens.

## Protected sites: retail, travel and finance

A second test on 110 well-known high-value sites (Amazon, Walmart, Booking.com, Delta, Chase, Zillow and others), homepage plus one inner page. Sites that timed out were re-checked one at a time with a 15-second wait, so slow-but-working sites aren't counted as dead ends. 2 sites with no reachable website were left out (108 counted).

| Category | Dead ends | Plus "loaded but empty to a bot" |
|---|---|---|
| Retail (40 sites) | **50%** | +10% |
| Travel (29 sites) | **45%** | +28% |
| Finance (29 sites) | **31%** | +3% |
| Tickets, real estate, jobs (10 sites) | **60%** | +10% |
| **All protected sites (108)** | **44%** | **+13%** |

- **Who blocks:** mostly Akamai here, then Cloudflare and DataDome.
- **Bottom line:** on the sites businesses most want to scrape, **close to half block bots outright**, and more than half are unusable for a bot once empty pages are counted.

## Page cleaning: what `/v1/scrape` saves

We re-fetched 197 pages that loaded fine and ran them through the exact `/v1/scrape` cleaning (remove scripts, styles and markup; keep the readable text).

- **Raw page:** about **148,000 characters** (median).
- **After cleaning:** about **5,900 characters** (median).
- **Reduction:** **96%** (median). Half of the pages fall between 92% and 98%, and 99% of pages shrank by more than 60%.

In plain terms, an AI reading the cleaned page instead of the raw HTML reads roughly **25 times less**.

## Honest takeaways

1. **"1 in 4 websites block bots" is real and defensible** (27%), and on protected retail, travel and finance sites it's **44%**. Both numbers are probably higher from cloud servers.
2. **The cost of a blocked page itself is small** (about 1,100 tokens). The bigger costs are wasted time, retries, the agent reasoning about the failure, and getting your server's IP flagged.
3. **The biggest token savings are on pages that do load:** cleaning cuts a page by **96%** before the AI reads it.
4. **Now detected (v3.13, Nov 2026):** 10–13% of "loaded" pages are really empty or soft-blocked. Axveritas now flags these "soft dead ends" (JavaScript-only pages, CAPTCHA walls served as 200, soft 404s). Re-checking this benchmark's pages, it caught **78%** of those "empty to a bot" pages, with **0 false alarms** on a sample of 90 normal pages and 13 well-known sites.

*All tests ran from one home internet connection on 2026-11-23 and are a snapshot; results change as sites update their bot defenses. The code is in [`benchmark/`](benchmark/), so anyone can re-run it.*
