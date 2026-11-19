# Axveritas MCP Server & ABVS-1.0 Gateway

[![M8ven Score](https://m8ven.ai/badge/mcp/axveritasprotocol-axveritas-qq00qa?v=ec1d3dc0aaa6d8a2ea96d0dfa79e48e3)](https://m8ven.ai/mcp/axveritasprotocol-axveritas-qq00qa?s=readme)
[![axveritasprotocol/axveritas MCP server](https://glama.ai/mcp/servers/axveritasprotocol/axveritas/badges/score.svg)](https://glama.ai/mcp/servers/axveritasprotocol/axveritas)

Open-source Python **Model Context Protocol (MCP)** server and `ABVS-1.0` verification gateway (`main.py`) for autonomous AI agents on Base Mainnet (Chain ID: 8453)[cite: 7, 8].

## Live Endpoints & Discovery
- **Remote MCP Server (Streamable HTTP):** `[https://axveritas.onrender.com/mcp](https://axveritas.onrender.com/mcp)`
- **A2A Agent Card:** `[https://axveritas.onrender.com/.well-known/agent.json](https://axveritas.onrender.com/.well-known/agent.json)`[cite: 8]
- **LLM Specification:** `[https://axveritas.onrender.com/llms.txt](https://axveritas.onrender.com/llms.txt)`[cite: 8]
- **Live Treasury & Ledger:** `[https://axveritas.onrender.com/v1/treasury](https://axveritas.onrender.com/v1/treasury)`[cite: 8]

## Tools Provided
- **`axveritas_preflight_check`** (`POST /v1/preflight`): Pre-flight dead-end URL health check using shared domain-health telemetry (`USDC` or `X-API-Key`)[cite: 7, 8].
- **`axveritas_scrape_verified`** (`POST /v1/scrape`): Direct schema-verified web extraction returning clean JSON and an `ABVS-1.0` SHA-256 receipt (`USDC` or `X-API-Key`)[cite: 7, 8].
- **`axveritas_verify_relay`** (`POST /v1/relay`): Non-custodial schema verification relay between buyer and worker agents (`1%` protocol toll)[cite: 7, 8].

---

## Credit Card Subscriptions (`X-API-Key` for Claude, Cursor, Grok & n8n)

Prefer paying by credit card instead of Base Mainnet USDC? Subscribe to a monthly plan to receive an active `X-API-Key` that works across `/v1/preflight`, `/v1/scrape`, and `/v1/relay`:

| Plan | Monthly Price | Included Monthly Quota | Subscribe |
| :--- | :--- | :--- | :--- |
| **Starter** | **$19 / month** | 10,000 Pre-Flight Checks + 500 Verified Scrapes | **[Get Starter Key →](https://buy.stripe.com/9B6cMX8m2bsHaxa8Lc4sE00)**[cite: 7] |
| **Builder Pro** | **$49 / month** | 40,000 Pre-Flight Checks + 2,500 Verified Scrapes | **[Get Builder Pro Key →](https://buy.stripe.com/00weV59q6eET0WA4uW4sE01)**[cite: 7] |
| **Scale** | **$149 / month** | 150,000 Pre-Flight Checks + 10,000 Verified Scrapes | **[Get Scale Key →](https://buy.stripe.com/8x2bITfOufIX34I6D44sE02)**[cite: 7] |

### Quickstart with `X-API-Key` (Python)

```python
import httpx

# 1. Pre-flight check ("Dead-End Sign" — prevents wasted LLM tokens)
check = httpx.post(
    "https://axveritas.onrender.com/v1/preflight",
    headers={"X-API-Key": "axv_live_your_key_here"},
    json={"target_url": "https://example.com"}
).json()

# 2. Direct schema-verified extraction (returns 422 instead of junk HTML if fields are missing)
if check["verdict"] == "PASSABLE":
    data = httpx.post(
        "https://axveritas.onrender.com/v1/scrape",
        headers={"X-API-Key": "axv_live_your_key_here"},
        json={"target_url": "https://example.com", "required_keys": ["title", "text"]}
    ).json()
