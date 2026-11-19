# Axveritas MCP Server & ABVS-1.0 Gateway

[![M8ven Score](https://m8ven.ai/badge/mcp/axveritasprotocol-axveritas-qq00qa?v=ec1d3dc0aaa6d8a2ea96d0dfa79e48e3)](https://m8ven.ai/mcp/axveritasprotocol-axveritas-qq00qa?s=readme)

Open-source Python Model Context Protocol (MCP) server and `ABVS-1.0` verification gateway (`main.py`) for autonomous AI agents on Base Mainnet (Chain ID: 8453).

## Tools Provided
- **`axveritas_preflight_check`** (`POST /v1/preflight`): Pre-flight dead-end URL health check using shared domain-health telemetry (`$0.001 USDC`).
- **`axveritas_scrape_verified`** (`POST /v1/scrape`): Direct schema-verified web extraction returning clean JSON and an `ABVS-1.0` SHA-256 receipt (`$0.015 USDC`).
- **`axveritas_verify_relay`** (`POST /v1/relay`): Non-custodial schema verification relay between buyer and worker agents (`1%` protocol toll).

## Self-Hosting & Local Installation

This repository contains the complete FastAPI + MCP JSON-RPC server implementation (`main.py`).

### 1. Clone and Install Dependencies
```bash
git clone [https://github.com/axveritasprotocol/axveritas.git](https://github.com/axveritasprotocol/axveritas.git)
cd axveritas
pip install -r requirements.txt
