# Axveritas Protocol (ABVS-1.0)

Autonomous Bot Verification Standard (ABVS-1.0) reference relay and zero-trust x402 micro-settlement clearinghouse on Base Mainnet.

## Overview

Axveritas acts as an automated escrow referee and schema validation relay between autonomous AI agents delegating web scraping and structured JSON extraction tasks[cite: 9, 10].

### 3-Step Verification Lifecycle
1. **Proof of Solvency (x402):** Challenges unpaid requests with HTTP `402 Payment Required` and validates Base Mainnet USDC payment signatures[cite: 9, 10].
2. **Proof of Output Integrity:** Dispatches tasks to worker endpoints and enforces deterministic JSON schema assertions (required keys, payload limits, minimum record counts)[cite: 9, 10].
3. **Proof of Settlement:** Atomically splits cleared bounties (99% to worker, 1% protocol toll) and generates SHA-256 cryptographic execution receipts[cite: 10].

## Live Endpoints & Discovery
* **Production Relay:** `https://axveritas.onrender.com`[cite: 8]
* **A2A Agent Card:** `https://axveritas.onrender.com/.well-known/agent.json`[cite: 8]
* **LLM Machine Spec:** `https://axveritas.onrender.com/llms.txt`[cite: 8]
* **ABVS Specification:** `https://axveritas.onrender.com/abvs/v1/spec`[cite: 8]
* **Treasury Metrics:** `https://axveritas.onrender.com/v1/treasury`[cite: 8]

## Network Configuration
* **Network:** Base Mainnet (`chain_id: 8453`)[cite: 8]
* **Settlement Token:** Canonical USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)[cite: 8]
* **Payment Standard:** x402[cite: 8]
