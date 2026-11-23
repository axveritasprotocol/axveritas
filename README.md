# Axveritas MCP Server & ABVS-1.0 Gateway

[![M8ven Score](https://m8ven.ai/badge/mcp/axveritasprotocol-axveritas-qq00qa?v=ec1d3dc0aaa6d8a2ea96d0dfa79e48e3)](https://m8ven.ai/mcp/axveritasprotocol-axveritas-qq00qa?s=readme)
[![axveritasprotocol/axveritas MCP server](https://glama.ai/mcp/servers/axveritasprotocol/axveritas/badges/score.svg)](https://glama.ai/mcp/servers/axveritasprotocol/axveritas)

Open-source Python **Model Context Protocol (MCP)** server and `ABVS-1.0` verification gateway (`main.py`) for autonomous AI agents on Base Mainnet (Chain ID: 8453).

## Quick Start: Free Trial Key (No Card Required)

1. Go to **https://axveritas.onrender.com** and click **Get Free Test Key (100 Checks)**. You get 100 pre-flight checks and 10 verified scrapes, one key per network.
2. Install it in Claude Code for all your projects:

```bash
claude mcp add --transport http --scope user axveritas "https://axveritas.onrender.com/mcp?api_key=YOUR_KEY"
```

3. Ask Claude: *"Use axveritas to pre-flight check https://example.com"*

## Model Context Protocol (MCP) & Live Endpoints

Axveritas is a remote **MCP Streamable HTTP / JSON-RPC 2.0** server (protocol versions `2025-06-18`, `2025-03-26` and `2024-11-05`). It supports `initialize`, `ping`, `tools/list` and **`tools/call`**, so MCP clients can run both tools directly. Authenticate with `?api_key=` in the server URL, an `X-API-Key` header, or an `X-Payment-Signature` Base USDC transaction hash.

- **Remote MCP Server (Streamable HTTP):** `https://axveritas.onrender.com/mcp` (also aliased at `/`)
- **A2A Agent Card:** `https://axveritas.onrender.com/.well-known/agent.json`
- **LLM Specification:** `https://axveritas.onrender.com/llms.txt`
- **Live Network Status:** `https://axveritas.onrender.com/v1/treasury`

### MCP Tools

- **`axveritas_preflight_check`**: Pre-flight dead-end URL check. Returns `PASSABLE` or `DEAD_END` with a reason (Cloudflare/WAF, 4xx/5xx, rate limit, empty JS shell), using a shared 6-hour domain cache. 1 preflight credit or $0.001 USDC.
- **`axveritas_scrape_verified`**: Schema-verified web extraction. Returns clean JSON plus an `ABVS-1.0` SHA-256 receipt, or an error if any `required_keys` are missing or empty. 1 scrape credit or $0.015 USDC.

### REST API

- `POST /v1/preflight` and `POST /v1/scrape`: the same two operations over plain HTTP.
- `POST /v1/relay`: two-bot schema verification relay between buyer and worker agents (1% protocol toll, $0.001 minimum). REST only.
- `POST /v1/trial-key`: mints a free trial key (one per network).

### MCP Client Configuration (`claude_desktop_config.json` / Cursor)

```json
{
  "mcpServers": {
    "axveritas": {
      "url": "https://axveritas.onrender.com/mcp?api_key=YOUR_KEY"
    }
  }
}
```

---

## Credit Card Subscriptions (`X-API-Key` for Claude, Cursor, Grok & n8n)

Prefer paying by credit card instead of Base Mainnet USDC? Subscribe to a monthly plan to receive an active `X-API-Key` that works across `/v1/preflight`, `/v1/scrape`, and `/v1/relay`:

| Plan | Monthly Price | Included Monthly Quota | Subscribe |
| :--- | :--- | :--- | :--- |
| **Starter** | **$19 / month** | 10,000 Pre-Flight Checks + 500 Verified Scrapes | **[Get Starter Key →](https://buy.stripe.com/9B6cMX8m2bsHaxa8Lc4sE00)** |
| **Builder Pro** | **$49 / month** | 40,000 Pre-Flight Checks + 2,500 Verified Scrapes | **[Get Builder Pro Key →](https://buy.stripe.com/00weV59q6eET0WA4uW4sE01)** |
| **Scale** | **$149 / month** | 150,000 Pre-Flight Checks + 10,000 Verified Scrapes | **[Get Scale Key →](https://buy.stripe.com/8x2bITfOufIX34I6D44sE02)** |

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
```

---

## Autonomous Crypto Rail (`x402` Base Mainnet USDC)

Autonomous agents with funded Base Mainnet wallets (`Chain ID: 8453`) can pay per call with canonical USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`) to `0x5922a9b0981db65827AC80F477b5dA3aE133c899` and pass the transaction hash in the `X-Payment-Signature` header.

---

## Self-Hosting & Local Installation

This repository contains the complete FastAPI + MCP JSON-RPC server implementation (`main.py`).

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/axveritasprotocol/axveritas.git
cd axveritas
pip install -r requirements.txt
```

### 2. Run the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
