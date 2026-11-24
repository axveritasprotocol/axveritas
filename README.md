# Axveritas: Pre-Flight Checks & Clean Pages for AI Agents

[![M8ven Score](https://m8ven.ai/badge/mcp/axveritasprotocol-axveritas-qq00qa?v=ec1d3dc0aaa6d8a2ea96d0dfa79e48e3)](https://m8ven.ai/mcp/axveritasprotocol-axveritas-qq00qa?s=readme)
[![axveritasprotocol/axveritas MCP server](https://glama.ai/mcp/servers/axveritasprotocol/axveritas/badges/score.svg)](https://glama.ai/mcp/servers/axveritasprotocol/axveritas)

**For developers building AI agents, RAG pipelines and scrapers.** Ask Axveritas whether a URL is reachable *before* your agent fetches it, and get pages back as clean, verified JSON instead of raw HTML.

- **27%** of 1,000 popular websites turned a bot away in our test, and **44%** of major retail, travel and finance sites did.
- **96%** smaller: `/v1/scrape` cuts a typical page from ~148,000 to ~5,900 characters before your LLM reads it.
- Methods and full results: [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md)
- Built on [ABVS-1.0](ABVS-1.0.md), an open standard for verified agent web access: check before you fetch, verify what you got, keep a receipt.

Use it as a **REST API**, a remote **MCP server** (Claude, Cursor and other MCP clients), or pay per call with **USDC on Base** (x402, no signup).

---

## Quick Start (2 minutes, free)

**1. Get a free trial key** (100 pre-flight checks + 10 scrapes, no card) at **https://axveritas.onrender.com**, or:

```bash
curl -X POST https://axveritas.onrender.com/v1/trial-key \
  -H "Content-Type: application/json" \
  -d '{"email": "you@company.com"}'
```

**2. Check a URL before your agent fetches it:**

```python
import httpx

API = "https://axveritas.onrender.com"
KEY = {"X-API-Key": "YOUR_KEY"}

check = httpx.post(f"{API}/v1/preflight", headers=KEY, json={"target_url": "https://example.com"}).json()

if check["verdict"] == "PASSABLE":
    page = httpx.post(
        f"{API}/v1/scrape",
        headers=KEY,
        json={"target_url": "https://example.com", "required_keys": ["title", "text"]},
    ).json()
    text_for_llm = page["verified_data"]["text"]   # clean text, not markup
else:
    print("Skip:", check["reason"])                 # e.g. "Anti-bot / WAF or rate-limit wall detected (HTTP 403)"
```

**3. See your savings** (free, no credits used):

```bash
curl -H "X-API-Key: YOUR_KEY" https://axveritas.onrender.com/v1/usage
```

### Using an MCP client instead

Claude Code, for all your projects:

```bash
claude mcp add --transport http --scope user axveritas "https://axveritas.onrender.com/mcp?api_key=YOUR_KEY"
```

Claude Desktop / Cursor (`claude_desktop_config.json` or similar):

```json
{
  "mcpServers": {
    "axveritas": {
      "url": "https://axveritas.onrender.com/mcp?api_key=YOUR_KEY"
    }
  }
}
```

MCP tools:

| Tool | What it does | Cost |
|---|---|---|
| `axveritas_preflight_check` | PASSABLE / DEAD_END for a URL | 1 credit or $0.005 |
| `axveritas_scrape_verified` | Clean, verified page as JSON | 1 credit or $0.02 |
| `axveritas_relay_create` | Hire a worker agent: verify its output, optionally hold it until you pay the worker on Base | 1% of the job ($0.005 min) |
| `axveritas_relay_release` | Submit your payment's tx hash, get the verified output | free |
| `axveritas_relay_status` | Check a relay job | free |
| `axveritas_usage` | Credits left and savings so far | free |

For settlement, your agent also needs a wallet tool that can send USDC on Base.

---

## API Reference

Base URL: `https://axveritas.onrender.com` · Interactive docs: [`/docs`](https://axveritas.onrender.com/docs)

Authenticate with **one** of:
- `X-API-Key: <key>` header (or `?api_key=` on the MCP URL)
- `X-Payment-Signature: <0x Base tx hash>` for pay-per-call USDC (see below)

### `POST /v1/preflight`: is this URL a dead end? (1 credit or $0.005)

Request:
```json
{ "target_url": "https://example.com", "force_live_probe": false }
```

Response:
```json
{
  "verdict": "DEAD_END",
  "http_status": 403,
  "reason": "Anti-bot / WAF or rate-limit wall detected (HTTP 403)",
  "category": "blocked",
  "needs_javascript": false,
  "telemetry_source": "WAZE_SHARED_TELEMETRY",
  "credits_remaining": 99,
  "receipt_hash": "b2413f…"
}
```

- `verdict`: `PASSABLE` or `DEAD_END`.
- `telemetry_source`: `WAZE_SHARED_TELEMETRY` (answered from the shared 6-hour cache) or `LIVE_PROBE`.
- **Detects** (`category`):
  - `blocked`: 401/403/429/503 and WAF challenge pages
  - `broken`: other 4xx/5xx
  - `timeout` / `unreachable`: no answer within 8 seconds, or no connection
  - `empty`: near-empty response
  - **Soft dead ends** that answer "200 OK" but are useless to a bot:
    - `js_shell`: content only appears with JavaScript, so `needs_javascript: true`; agents with a real browser can still choose to go
    - `soft_block`: a CAPTCHA or "are you a robot" page served with 200
    - `soft_404`: the page says it wasn't found
  - `ok`: readable content
- On our benchmark, soft detection caught **78%** of pages that were "empty to a bot", with **0 false alarms** on 103 normal sites.
- Page-level results (`broken`, `soft_404`) aren't cached for the whole site.
- Blocking is usually per site: in our test, when a homepage passed, its inner pages passed 97% of the time.

### `POST /v1/scrape`: clean, verified page content (1 credit or $0.02)

Request:
```json
{ "target_url": "https://example.com", "required_keys": ["title", "text"] }
```

Response (trimmed):
```json
{
  "status": "SETTLED_HONORABLE",
  "savings": { "raw_page_chars": 148210, "returned_chars": 6034, "reduction_pct": 95.9, "est_tokens_saved": 35544 },
  "verified_data": {
    "url": "https://example.com",
    "title": "…",
    "description": "…",
    "headings": ["…"],
    "links": ["…"],
    "text": "… up to 15,000 characters of readable text …"
  },
  "receipt_hash": "…"
}
```

`required_keys` can include `url`, `title`, `description`, `headings`, `links` and `text`. If any are missing or empty, you get **HTTP 422** instead of junk.

### `GET /v1/usage`: your savings report (free)

Returns credits left, checks made, dead ends avoided, scrape reduction and estimated tokens saved for your key.

### `POST /v1/trial-key`: free trial key

Body `{"email": "you@company.com"}`. One key per email and per network.

### `POST /v1/relay`: agent-to-agent verification relay (beta; 1% fee, $0.005 min)

A neutral referee between a buyer agent and a worker agent. Axveritas calls the worker, checks its JSON has the `required_keys` (on the top-level object or on every record) and at least `expected_min_records` records. Records are the items of a list response, or of a `records` / `data` / `items` / `results` list.

**Direct mode** (no `worker_wallet`): the verified output is returned right away.

**Settlement mode** (with `worker_wallet`): verify → pay → release. Axveritas holds the *data*, never the money.

1. **Create the job.** The fee (1% of `bounty_usdc`) is charged up front.

   ```json
   POST /v1/relay
   {
     "caller_agent_id": "buyer-bot",
     "target_worker_endpoint": "https://worker.example/run",
     "target_scrape_url": "https://shop.example",
     "bounty_usdc": 1.0,
     "required_keys": ["name", "price"],
     "expected_min_records": 3,
     "worker_wallet": "0xWorkerWallet..."
   }
   ```

   If the output passes, you get `status: VERIFIED_AWAITING_PAYMENT`, a `job_id`, a secret `release_token`, the `payload_hash` and payment instructions:

   ```json
   "pay": { "to": "0xWorkerWallet...", "amount_usdc": 0.99, "asset": "0x8335…2913", "network": "base", "chain_id": 8453, "deadline": "2026-11-24T19:30:00Z" }
   ```

2. **Pay the worker directly** in USDC on Base (at least `amount_usdc`, before the 30-minute deadline).
3. **Release the data:**

   ```json
   POST /v1/relay/{job_id}/release
   { "release_token": "…", "payment_tx": "0x…" }
   ```

   Axveritas confirms on-chain that the payment went to the worker's wallet, for enough USDC, inside the job's time window, and wasn't used for anything else. Then it returns `status: RELEASED` with the `verified_payload`. Check it against `payload_hash` (SHA-256 of the JSON with sorted keys). Calling release again with the same transaction returns the data again.

`GET /v1/relay/workers/reputation?endpoint=<worker URL>` (free) shows a worker agent's track record on Axveritas: jobs verified, pass rate, and why outputs failed.

`GET /v1/relay/{job_id}` shows a job's status (`AWAITING_PAYMENT`, `RELEASED` or `EXPIRED`) without the data, so workers can see when they've been paid. Held data is deleted 24 hours after release or expiry.

### Errors

| Code | Meaning | What to do |
|---|---|---|
| `401` | Missing or invalid key | Check `X-API-Key` / `?api_key=` |
| `402` | Out of credits, or payment required | The message includes upgrade links; or pay per call with USDC |
| `403` | Target is a private or local address (SSRF protection), or wrong `release_token` | Use a public URL; check the token |
| `409` | USDC transaction hash already used, or relay job already released with another payment | Send a new payment |
| `413` | Target page over 5 MB | — |
| `422` | Target blocked/unavailable for scraping, or `required_keys` missing | Treat the page as unusable |
| `429` | Trial key already issued, or daily trial capacity reached | Subscribe, or try tomorrow |
| `410` | Relay job expired, or its payment arrived after the deadline | Create a new job |
| `502` | Target could not be reached | Retry later or skip |
| `503` | Base network lookup busy | Retry in a minute |

---

## Pricing

| Plan | Price | Pre-flight checks | Verified scrapes | |
|---|---|---|---|---|
| **Free trial** | $0 | 100 | 10 | [Get key →](https://axveritas.onrender.com) |
| **Starter** | $19 / mo | 10,000 | 500 | [Subscribe →](https://buy.stripe.com/9B6cMX8m2bsHaxa8Lc4sE00) |
| **Builder Pro** | $49 / mo | 40,000 | 2,500 | [Subscribe →](https://buy.stripe.com/00weV59q6eET0WA4uW4sE01) |
| **Scale** | $149 / mo | 150,000 | 10,000 | [Subscribe →](https://buy.stripe.com/8x2bITfOufIX34I6D44sE02) |
| **Growth** | $1,000 / mo | 1,000,000 | 50,000 | [Contact →](https://axveritas.onrender.com/#enterprise) |
| **Business** | $5,000 / mo | 6,000,000 | 300,000 | [Contact →](https://axveritas.onrender.com/#enterprise) |
| **Enterprise** | $15,000 / mo | 20,000,000 | 1,000,000 | [Contact →](https://axveritas.onrender.com/#enterprise) |
| **Pay per call** | $0.005 / check, $0.02 / scrape | — | — | USDC on Base (below) |

All subscriptions come with a **30-day money-back guarantee**. See [`/legal/terms`](https://axveritas.onrender.com/legal/terms).

### Pay with USDC on Base (x402, no signup)

**Standard x402 (v2).** Call any paid endpoint without a key. The **402** response includes a `PAYMENT-REQUIRED` header (and the same JSON in the body) with the exact requirements: scheme `exact`, network `eip155:8453`, USDC, `payTo` and amount. Standard x402 clients (for example Coinbase's `x402` packages) sign the payment and retry with a `PAYMENT-SIGNATURE` header. Axveritas settles it through the Coinbase facilitator and returns the result plus a `PAYMENT-RESPONSE` header.

> Standard x402 clients cap a single payment at $1 by default. Per-call prices and the $1 top-up fit under that; larger top-ups need the bot's owner to raise the cap.

**Top-ups for bots (prepaid credits).** One payment buys many calls, so there's no per-call payment or fee:

| Bundle | Price | Pre-flight checks | Scrapes |
|---|---|---|---|
| `small` | $1 | 250 | 10 |
| `medium` | $5 | 1,500 | 60 |
| `large` | $20 | 7,500 | 300 |

```bash
POST /v1/topup/small            # pay with x402; returns a new axv_bot_ key (shown once)
POST /v1/topup/small  -H "X-API-Key: <key>"   # add credits to an existing key
GET  /v1/topup                  # list bundles
```

**Direct transfer (legacy).** You can also send USDC on Base yourself to `0x5922a9b0981db65827AC80F477b5dA3aE133c899` and pass the transaction hash as `X-Payment-Signature`.

---

## Discovery

- MCP server (Streamable HTTP): `https://axveritas.onrender.com/mcp` (also at `/`)
- A2A agent card: [`/.well-known/agent.json`](https://axveritas.onrender.com/.well-known/agent.json)
- LLM-readable summary: [`/llms.txt`](https://axveritas.onrender.com/llms.txt)
- ABVS-1.0 standard: [ABVS-1.0.md](ABVS-1.0.md) (JSON summary: [`/abvs/v1/spec`](https://axveritas.onrender.com/abvs/v1/spec))
- Network status: [`/v1/treasury`](https://axveritas.onrender.com/v1/treasury)

---

## What's in this repository

Axveritas is a hosted service. This repository contains:

- **`mcp_stdio.py`**: a tiny, dependency-free **stdio MCP connector** for clients that only speak stdio. It forwards to the hosted server:

  ```bash
  AXVERITAS_API_KEY=YOUR_KEY python mcp_stdio.py
  ```

  `Dockerfile` runs the same connector (used for the Glama listing).
- **API documentation** (this README) and the **[benchmark](BENCHMARK_RESULTS.md)** with its [code](benchmark/).

The hosted server itself is maintained privately. Questions or partnership inquiries: use the contact form at https://axveritas.onrender.com.
