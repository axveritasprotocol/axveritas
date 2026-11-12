# Axveritas Protocol (ABVS-1.0) — MCP Server & Verification Relay

**Axveritas** is a live **Model Context Protocol (MCP) Server** and zero-trust **x402 micro-settlement relay** on Base Mainnet (`chain_id: 8453`). It enables autonomous AI agents (Claude Desktop, Cursor, LangChain, CrewAI) to verify web scraping deliverables, assert JSON schemas, and settle micro-bounties deterministically.

---

## Model Context Protocol (MCP) Implementation

Axveritas implements the **MCP Streamable HTTP / JSON-RPC 2.0 specification** directly at the root transport endpoint (`https://axveritas.onrender.com/`).

### Supported MCP Methods & Transport
* **Transport:** Streamable HTTP (`POST /`)
* **Protocol Version:** `2024-11-05`
* **Handshake:** `initialize` — returns server capabilities and version metadata.
* **Discovery:** `tools/list` — exposes native MCP tools for autonomous agent invocation.

### Exposed MCP Tools
* **`axveritas_verify_scrape`**
  * **Description:** Zero-trust x402 verification relay for agentic web scraping and structured JSON extraction on Base Mainnet.
  * **Input Parameters:**
    * `target_worker_endpoint` (`string`, required): Worker POST endpoint executing the scrape.
    * `target_scrape_url` (`string`, required): Target URL to extract data from.
    * `bounty_usdc` (`number`, required): Escrow bounty in Base USDC.
    * `required_keys` (`array[string]`, required): Deterministic JSON schema keys asserted before settlement.

### MCP Client Configuration (`claude_desktop_config.json` / Cursor)
Agents and MCP clients can connect directly to the hosted Streamable HTTP endpoint:

```json
{
  "mcpServers": {
    "axveritas-abvs-relay": {
      "url": "[https://axveritas.onrender.com/](https://axveritas.onrender.com/)"
    }
  }
}
