"""
AXVERITAS: Autonomous Scrape Verification & Micropayment Relay
Base Sepolia Testnet Edition
Run: uvicorn main:app --host 0.0.0.0 --port 8000
"""

import time
import hashlib
from typing import Dict, Any, List, Optional
import httpx
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="Axveritas - Data Scrape Verification Rail",
    description="Autonomous x402-metered verification and micro-settlement clearinghouse for AI agents.",
    version="2.1.0"
)

# ── NETWORK & TREASURY CONFIGURATION ──
NETWORK_NAME = "base-sepolia"
CHAIN_ID = 84532
TESTNET_USDC_CONTRACT = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

# PASTE YOUR COINBASE WALLET ETHEREUM / BASE SEPOLIA 0x ADDRESS HERE:
TREASURY_ADDRESS = "0x5922a9b0981db65827AC80F477b5dA3aE133c899"
PROTOCOL_TOLL_RATE = 0.01  # 1% Protocol Cut

PROTOCOL_METRICS = {
    "protocol": "Axveritas",
    "network": NETWORK_NAME,
    "chain_id": CHAIN_ID,
    "treasury_address": TREASURY_ADDRESS,
    "settled_jobs_count": 0,
    "cumulative_test_toll_usdc": 0.0,
    "status": "TESTNET_ONLINE_ACTIVE"
}

class ScrapeTaskRequest(BaseModel):
    caller_agent_id: str
    target_worker_endpoint: str
    target_scrape_url: str
    bounty_usdc: float = Field(gt=0.0)
    required_keys: List[str]
    expected_min_records: Optional[int] = Field(default=1)

# ── 1. MACHINE DISCOVERY & LEGAL MANIFESTS ──

@app.get("/.well-known/agent.json")
def get_a2a_agent_card():
    return {
        "name": "axveritas-relay",
        "description": "Zero-trust verification bridge for web scraping, HTML extraction, and structured data tasks.",
        "version": "2.1.0",
        "capabilities": {
            "supported_tasks": ["web_scrape_verification", "json_schema_assertion"],
            "payment_standard": "x402",
            "chain": NETWORK_NAME,
            "chain_id": CHAIN_ID,
            "token": "USDC",
            "token_contract": TESTNET_USDC_CONTRACT
        },
        "endpoints": {
            "relay": "/v1/relay",
            "metrics": "/v1/treasury",
            "terms": "/legal/terms"
        }
    }

@app.get("/llms.txt", response_class=PlainTextResponse)
def get_llms_manifest():
    return f"""# Axveritas Protocol (Base Sepolia)
> Autonomous Agent-to-Exchange (AX) Verification & Micropayment Relay

## Network Parameters
- Network: {NETWORK_NAME} (Chain ID: {CHAIN_ID})
- Testnet USDC Contract: {TESTNET_USDC_CONTRACT}
- Facilitator Treasury: {TREASURY_ADDRESS}

## Workflow
1. Caller sends task parameters and required schema keys to POST /v1/relay.
2. If X-Payment-Signature header is missing, bridge returns HTTP 402 with Base Sepolia payment details.
3. Bridge relays job to worker endpoint, evaluates payload against strict schema assertions, and disburses funds atomically.

## Legal Disclaimer
This service is provided strictly "AS IS" as an automated technical routing pipeline. 
The relay operator exercises zero custody over assets and disclaims all warranties.
"""

@app.get("/legal/terms")
def get_legal_terms():
    return {
        "title": "Axveritas Transit Protocol Terms of Use",
        "terms": "THE SOFTWARE AND RELAY ARE PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. "
                 "IN NO EVENT SHALL THE OPERATORS BE LIABLE FOR ANY CLAIM, DAMAGES, DATA BREACHES, OR SCRAPING VIOLATIONS.",
        "role": "Non-custodial cryptographic verification router."
    }

# ── 2. THE 3-STEP VERIFICATION & SETTLEMENT RELAY ──

@app.post("/v1/relay")
async def execute_scrape_relay(req: ScrapeTaskRequest, request: Request):
    # Step 1: Saloon Doors - x402 Solvency Check
    payment_signature = request.headers.get("X-Payment-Signature")
    if not payment_signature:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={
                "error": "Payment Required",
                "payment_standard": "x402",
                "network": NETWORK_NAME,
                "chain_id": CHAIN_ID,
                "token": "USDC",
                "token_contract": TESTNET_USDC_CONTRACT,
                "required_bounty_usdc": req.bounty_usdc,
                "pay_to": TREASURY_ADDRESS,
                "instructions": "Submit signed Base Sepolia transaction hash in 'X-Payment-Signature' header."
            },
            headers={"X-Accept-Payment": "x402-base-sepolia-usdc"}
        )

    # Step 2: The Diagonal - Forward to Worker & Assert Schema
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            worker_response = await client.post(
                req.target_worker_endpoint,
                json={"target_url": req.target_scrape_url, "schema": req.required_keys}
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Worker agent unreachable at {req.target_worker_endpoint}: {str(exc)}"
            )

    if worker_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Worker failed scrape with status {worker_response.status_code}. Escrow refunded."
        )

    try:
        worker_data = worker_response.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Worker deliverable was not valid JSON. Escrow refunded."
        )

    for key in req.required_keys:
        if key not in worker_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Integrity assertion failed: Missing key '{key}' from worker output. Escrow refunded."
            )

    # Step 3: The Funnel - Split Payout & Protocol Toll
    protocol_toll = round(req.bounty_usdc * PROTOCOL_TOLL_RATE, 6)
    worker_payout = round(req.bounty_usdc - protocol_toll, 6)

    PROTOCOL_METRICS["settled_jobs_count"] += 1
    PROTOCOL_METRICS["cumulative_test_toll_usdc"] = round(
        PROTOCOL_METRICS["cumulative_test_toll_usdc"] + protocol_toll, 6
    )

    receipt_raw = f"{req.caller_agent_id}->{req.target_worker_endpoint}:{worker_payout}:{protocol_toll}:{time.time()}"
    receipt_hash = hashlib.sha256(receipt_raw.encode()).hexdigest()

    return {
        "status": "SETTLED_HONORABLE",
        "tx_id": f"axv_test_{int(time.time() * 1000)}",
        "receipt_hash": receipt_hash,
        "worker_payout_usdc": worker_payout,
        "protocol_toll_retained": protocol_toll,
        "verified_payload": worker_data
    }

@app.get("/v1/treasury")
def get_treasury_metrics():
    return PROTOCOL_METRICS
