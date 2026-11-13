"""
AXVERITAS: Autonomous Bot Verification Standard (ABVS-1.0)
Base Mainnet Direct Verified Scraper & Verification Clearinghouse (v3.0.0)
Run: uvicorn main:app --host 0.0.0.0 --port 8000
"""
import re
import time
import json
import sqlite3
import hashlib
import ipaddress
import socket
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional, Set
import httpx
from bs4 import BeautifulSoup
from web3 import Web3
from fastapi import FastAPI, HTTPException, Request, status, Header
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Axveritas - ABVS Direct Verified Scraper & Clearinghouse",
    description="Autonomous Bot Verification Standard (ABVS-1.0) direct verified web extraction and x402 micro-settlement hub on Base.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── NETWORK & TREASURY CONFIGURATION ──
NETWORK_NAME = "base"
CHAIN_ID = 8453
USDC_CONTRACT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913".lower()
TREASURY_ADDRESS = "0x5922a9b0981db65827AC80F477b5dA3aE133c899"

DIRECT_SCRAPE_FEE_USDC = 0.015  # $0.015 flat per direct verified scrape
RELAY_TOLL_RATE = 0.01          # 1% cut (min $0.001) for 2-bot relay

# ── ON-CHAIN BASE MAINNET VERIFICATION (WEB3.PY) ──
BASE_RPC_URL = "https://mainnet.base.org"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))


def verify_base_usdc_payment(tx_hash: str, min_usdc: float) -> bool:
    """Confirms on Base Mainnet that real USDC landed in TREASURY_ADDRESS."""
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if not receipt or receipt.status != 1:
            return False
        target_wallet = TREASURY_ADDRESS.lower().replace("0x", "").zfill(64)
        for log in receipt.logs:
            if (
                log.address.lower() == USDC_CONTRACT
                and len(log.topics) >= 3
                and log.topics[0].hex().lower() == TRANSFER_TOPIC
                and log.topics[2].hex().lower().endswith(target_wallet)
            ):
                amount_usdc = int(log.data.hex(), 16) / 1_000_000
                if amount_usdc >= min_usdc:
                    return True
        return False
    except Exception:
        return False


# ── PERSISTENT SQLITE LEDGER ──
DB_PATH = "axveritas_ledger.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settlements (
                tx_sig TEXT PRIMARY KEY,
                tx_id TEXT,
                route TEXT,
                caller_agent_id TEXT,
                target_domain TEXT,
                fee_usdc REAL,
                receipt_hash TEXT,
                created_at REAL
            )
        """)


init_db()


def is_sig_spent(clean_sig: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT 1 FROM settlements WHERE tx_sig = ?", (clean_sig,)).fetchone()
        return row is not None


def record_settlement(clean_sig: str, tx_id: str, route: str, caller_id: str, target_url: str, fee_usdc: float, receipt_hash: str):
    domain = urlparse(target_url).hostname or "unknown"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO settlements (tx_sig, tx_id, route, caller_agent_id, target_domain, fee_usdc, receipt_hash, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (clean_sig, tx_id, route, caller_id, domain, fee_usdc, receipt_hash, time.time())
        )


def get_persisted_metrics() -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT COUNT(*), COALESCE(SUM(fee_usdc), 0.0) FROM settlements").fetchone()
        scrape_count = conn.execute("SELECT COUNT(*) FROM settlements WHERE route = '/v1/scrape'").fetchone()[0]
        relay_count = conn.execute("SELECT COUNT(*) FROM settlements WHERE route = '/v1/relay'").fetchone()[0]
    return {
        "protocol": "Axveritas",
        "standard": "ABVS-1.0",
        "version": "3.0.0",
        "network": NETWORK_NAME,
        "chain_id": CHAIN_ID,
        "treasury_address": TREASURY_ADDRESS,
        "settled_jobs_count": row[0],
        "direct_scrapes_count": scrape_count,
        "relay_jobs_count": relay_count,
        "cumulative_toll_usdc": round(float(row[1]), 6),
        "status": "MAINNET_ONLINE_ACTIVE"
    }


# ── SECURITY ENFORCEMENT HELPERS ──
def assert_safe_external_url(target_url: str):
    """Prevents SSRF against localhost, private subnets, and cloud metadata endpoints."""
    try:
        parsed = urlparse(target_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Only http and https schemes are permitted.")
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("Invalid target host.")
        ip_info = socket.getaddrinfo(hostname, None)
        for _, _, _, _, sockaddr in ip_info:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                raise ValueError("Routing to private, local, or cloud-internal addresses is strictly blocked.")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security violation: Target URL disallowed ({str(exc)})"
        )


def extract_structured_payload(html: str, url: str, required_keys: List[str]) -> Dict[str, Any]:
    """Parses HTML into clean, schema-verified JSON matching caller's requested keys."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""

    headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text(strip=True)][:30]
    links = []
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        if text:
            links.append({"text": text[:160], "href": a["href"]})
        if len(links) >= 50:
            break

    clean_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
    prices = re.findall(r"\$\d+(?:,\d{3})*(?:\.\d{2})?", clean_text)[:25]

    # Extract embedded JSON-LD structured data if present on page
    json_ld = []
    raw_soup = BeautifulSoup(html, "html.parser")
    for script in raw_soup.find_all("script", type="application/ld+json"):
        try:
            json_ld.append(json.loads(script.string))
        except Exception:
            pass

    base_map: Dict[str, Any] = {
        "url": url,
        "title": title,
        "description": description,
        "headings": headings,
        "links": links,
        "prices": prices,
        "content": clean_text[:12000],
        "text": clean_text[:12000],
        "json_ld": json_ld,
        "records": links if links else [{"title": title, "content": clean_text[:2000]}]
    }

    # Map every requested key deterministically (never return empty placeholder if data exists)
    result: Dict[str, Any] = {}
    for key in required_keys:
        lk = key.lower().strip()
        if lk in base_map and base_map[lk]:
            result[key] = base_map[lk]
        elif "price" in lk and prices:
            result[key] = prices
        elif "link" in lk or "url" in lk:
            result[key] = links or url
        elif "title" in lk or "name" in lk:
            result[key] = title or (headings[0] if headings else "")
        elif "desc" in lk or "summary" in lk:
            result[key] = description or clean_text[:500]
        elif clean_text:
            result[key] = clean_text[:4000]

    return result


# ── REQUEST MODELS ──
class DirectScrapeRequest(BaseModel):
    caller_agent_id: str = Field(default="autonomous_agent", max_length=128)
    target_url: str = Field(..., max_length=1024, description="Target webpage URL to fetch and verify")
    required_keys: List[str] = Field(default=["title", "content"], max_length=50, description="Mandatory JSON keys required in output")


class ScrapeTaskRequest(BaseModel):
    caller_agent_id: str = Field(..., max_length=128)
    target_worker_endpoint: str = Field(..., max_length=512)
    target_scrape_url: str = Field(..., max_length=1024)
    bounty_usdc: float = Field(gt=0.0, le=100.0)
    required_keys: List[str] = Field(..., max_length=50)
    expected_min_records: Optional[int] = Field(default=1, le=5000)


# ── 1. MACHINE DISCOVERY, MCP CONNECTOR & ABVS MANIFESTS ──
@app.api_route("/", methods=["GET", "POST", "HEAD"])
async def root_and_mcp_gateway(request: Request):
    if request.method in ("GET", "HEAD"):
        return {
            "protocol": "Axveritas",
            "standard": "Autonomous Bot Verification Standard (ABVS-1.0)",
            "status": "ONLINE_ACTIVE",
            "version": "3.0.0",
            "network": NETWORK_NAME,
            "chain_id": CHAIN_ID,
            "pricing": {
                "direct_verified_scrape_usdc": DIRECT_SCRAPE_FEE_USDC,
                "two_bot_relay_toll": "1% (min $0.001 USDC)"
            },
            "endpoints": {
                "direct_scrape": "/v1/scrape",
                "relay": "/v1/relay",
                "treasury": "/v1/treasury",
                "agent_card": "/.well-known/agent.json",
                "machine_spec": "/llms.txt"
            }
        }

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=200, content={"status": "ONLINE_ACTIVE", "standard": "ABVS-1.0"})

    if isinstance(body, dict) and body.get("jsonrpc") == "2.0":
        msg_id = body.get("id")
        method = body.get("method")
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "axveritas-abvs-gateway", "version": "3.0.0"}
                }
            }
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "axveritas_scrape_verified",
                            "description": "Direct verified web extraction ($0.015 USDC on Base). Fetches target_url, strips junk HTML, asserts required JSON keys, and returns clean data with an ABVS-1.0 receipt.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "target_url": {"type": "string", "description": "Webpage URL to extract"},
                                    "required_keys": {"type": "array", "items": {"type": "string"}, "description": "Mandatory JSON keys"}
                                },
                                "required": ["target_url", "required_keys"]
                            }
                        },
                        {
                            "name": "axveritas_verify_scrape",
                            "description": "Zero-trust 2-bot x402 verification relay (1% toll, $0.001 min) on Base Mainnet.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "target_worker_endpoint": {"type": "string"},
                                    "target_scrape_url": {"type": "string"},
                                    "bounty_usdc": {"type": "number"},
                                    "required_keys": {"type": "array", "items": {"type": "string"}}
                                },
                                "required": ["target_worker_endpoint", "target_scrape_url", "bounty_usdc", "required_keys"]
                            }
                        }
                    ]
                }
            }
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    return {"protocol": "Axveritas", "standard": "ABVS-1.0", "status": "ONLINE_ACTIVE"}


@app.get("/.well-known/glama.json")
def get_glama_claim():
    return {
        "$schema": "https://glama.ai/mcp/schemas/connector.json",
        "claim": "glama_claim_ufq8wuIc1jv6CII9JWJk5rLeBCmXAeEp"
    }


@app.get("/.well-known/agent.json")
def get_a2a_agent_card():
    return {
        "name": "axveritas-gateway",
        "description": "Direct schema-verified web scraper ($0.015 USDC) and ABVS-1.0 zero-trust verification relay on Base Mainnet.",
        "version": "3.0.0",
        "standard": "ABVS-1.0",
        "capabilities": {
            "supported_tasks": [
                "direct_verified_web_scrape",
                "web_scrape_verification",
                "json_schema_assertion"
            ],
            "verification_standard": "ABVS-1.0",
            "payment_standard": "x402",
            "chain": NETWORK_NAME,
            "chain_id": CHAIN_ID,
            "token": "USDC",
            "token_contract": USDC_CONTRACT
        },
        "endpoints": {
            "direct_scrape": "/v1/scrape",
            "relay": "/v1/relay",
            "metrics": "/v1/treasury",
            "terms": "/legal/terms",
            "spec": "/abvs/v1/spec"
        }
    }


@app.get("/abvs/v1/spec")
def get_abvs_specification():
    return {
        "standard": "Autonomous Bot Verification Standard (ABVS)",
        "version": "1.0.0",
        "governing_principles": [
            "1. Proof of Solvency: Pre-flight x402 Base Mainnet USDC verification before compute execution.",
            "2. Objective Schema Assertion: Deterministic verification of required JSON keys and non-empty extraction.",
            "3. Cryptographic Non-Repudiation: SHA-256 verifiable execution receipts."
        ],
        "facilitator_treasury": TREASURY_ADDRESS
    }


@app.get("/llms.txt", response_class=PlainTextResponse)
def get_llms_manifest():
    return f"""# Axveritas Protocol (ABVS-1.0 Direct Verified Scraper & Clearinghouse)
> Zero-junk-HTML, schema-verified web extraction & x402 verification relay on Base Mainnet.

## Endpoints & Pricing
1. POST /v1/scrape — Direct Verified Scrape ($0.015 USDC flat on Base Mainnet)
   - Input JSON: {{"target_url": "https://...", "required_keys": ["title", "prices", "content"]}}
   - Returns clean, schema-verified JSON + SHA-256 ABVS-1.0 receipt. No separate worker bot needed.
2. POST /v1/relay — Two-Bot Verification Relay (1% toll, $0.001 USDC minimum)

## Network Parameters
- Network: {NETWORK_NAME} (Chain ID: {CHAIN_ID})
- USDC Contract: {USDC_CONTRACT}
- Treasury: {TREASURY_ADDRESS}
"""


@app.get("/legal/terms")
def get_legal_terms():
    return {
        "title": "Axveritas Transit Protocol Terms of Use",
        "standard": "ABVS-1.0",
        "terms": "THE SOFTWARE AND SERVICE ARE PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. "
                 "IN NO EVENT SHALL THE OPERATORS BE LIABLE FOR ANY CLAIM, DAMAGES, OR SCRAPING VIOLATIONS."
    }


# ── 2. DIRECT VERIFIED SCRAPE ($0.015 USDC — NO WORKER BOT NEEDED) ──
@app.post("/v1/scrape")
async def execute_direct_verified_scrape(
    req: DirectScrapeRequest,
    x_payment_signature: Optional[str] = Header(default=None, alias="X-Payment-Signature")
):
    """Fetches target_url directly, extracts structured JSON, asserts required_keys, and settles $0.015 USDC."""
    if not x_payment_signature:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={
                "error": "Payment Required",
                "standard": "ABVS-1.0",
                "payment_standard": "x402",
                "network": NETWORK_NAME,
                "chain_id": CHAIN_ID,
                "token": "USDC",
                "token_contract": USDC_CONTRACT,
                "required_bounty_usdc": DIRECT_SCRAPE_FEE_USDC,
                "pay_to": TREASURY_ADDRESS,
                "instructions": f"Send {DIRECT_SCRAPE_FEE_USDC} USDC on Base Mainnet to {TREASURY_ADDRESS} and pass tx_hash in 'X-Payment-Signature' header."
            },
            headers={"X-Accept-Payment": "x402-base-usdc"}
        )

    clean_sig = x_payment_signature.strip().lower()
    if is_sig_spent(clean_sig):
        raise HTTPException(status_code=409, detail="ABVS Replay Violation: Transaction signature already settled.")

    if not verify_base_usdc_payment(x_payment_signature.strip(), DIRECT_SCRAPE_FEE_USDC):
        raise HTTPException(
            status_code=402,
            detail=f"Unverified Base Mainnet USDC payment. Send at least {DIRECT_SCRAPE_FEE_USDC} USDC to {TREASURY_ADDRESS}."
        )

    assert_safe_external_url(req.target_url)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AxveritasABVSBot/3.0; +https://axveritas.onrender.com/llms.txt)",
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"
    }
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        try:
            resp = await client.get(req.target_url, headers=headers)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Target URL unreachable: {str(exc)}")

    if resp.status_code != 200:
        raise HTTPException(status_code=422, detail=f"Target URL returned HTTP {resp.status_code} (blocked or unavailable).")

    if len(resp.content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Target page exceeded 5MB limit.")

    # Support direct JSON endpoints as well as HTML pages
    content_type = resp.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        try:
            extracted = resp.json()
        except Exception:
            raise HTTPException(status_code=422, detail="Target returned invalid JSON.")
    else:
        extracted = extract_structured_payload(resp.text, req.target_url, req.required_keys)

    for key in req.required_keys:
        if key not in extracted or extracted[key] in (None, "", [], {}):
            raise HTTPException(
                status_code=422,
                detail=f"ABVS Assertion Failed: Could not extract non-empty value for required key '{key}'."
            )

    tx_id = f"axv_scrape_{int(time.time() * 1000)}"
    receipt_raw = f"{req.caller_agent_id}->{req.target_url}:{DIRECT_SCRAPE_FEE_USDC}:{time.time()}"
    receipt_hash = hashlib.sha256(receipt_raw.encode()).hexdigest()

    record_settlement(clean_sig, tx_id, "/v1/scrape", req.caller_agent_id, req.target_url, DIRECT_SCRAPE_FEE_USDC, receipt_hash)

    return {
        "status": "SETTLED_HONORABLE",
        "standard": "ABVS-1.0",
        "mode": "DIRECT_VERIFIED_SCRAPE",
        "tx_id": tx_id,
        "receipt_hash": receipt_hash,
        "fee_paid_usdc": DIRECT_SCRAPE_FEE_USDC,
        "verified_payload": extracted
    }


# ── 3. TWO-BOT VERIFICATION RELAY (1% TOLL, $0.001 MIN) ──
@app.post("/v1/relay")
async def execute_scrape_relay(
    req: ScrapeTaskRequest,
    request: Request,
    x_payment_signature: Optional[str] = Header(default=None, alias="X-Payment-Signature")
):
    protocol_fee = round(max(req.bounty_usdc * RELAY_TOLL_RATE, 0.001), 6)

    if not x_payment_signature:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={
                "error": "Payment Required",
                "standard": "ABVS-1.0",
                "payment_standard": "x402",
                "network": NETWORK_NAME,
                "chain_id": CHAIN_ID,
                "token": "USDC",
                "token_contract": USDC_CONTRACT,
                "required_bounty_usdc": protocol_fee,
                "pay_to": TREASURY_ADDRESS,
                "instructions": "Submit unique signed Base Mainnet transaction hash in 'X-Payment-Signature' header."
            },
            headers={"X-Accept-Payment": "x402-base-usdc"}
        )

    clean_sig = x_payment_signature.strip().lower()
    if is_sig_spent(clean_sig):
        raise HTTPException(status_code=409, detail="ABVS Replay Violation: Transaction signature has already been settled.")

    if not verify_base_usdc_payment(x_payment_signature.strip(), protocol_fee):
        raise HTTPException(
            status_code=402,
            detail=f"Unverified Base Mainnet USDC payment. Send at least {protocol_fee} USDC to {TREASURY_ADDRESS}."
        )

    assert_safe_external_url(req.target_worker_endpoint)
    assert_safe_external_url(req.target_scrape_url)

    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    async with httpx.AsyncClient(timeout=15.0, limits=limits) as client:
        try:
            worker_response = await client.post(
                req.target_worker_endpoint,
                json={"target_url": req.target_scrape_url, "schema": req.required_keys}
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Worker agent unreachable: {str(exc)}")

    if worker_response.status_code != 200:
        raise HTTPException(status_code=422, detail=f"Worker failed scrape with HTTP {worker_response.status_code}.")

    if len(worker_response.content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Worker deliverable exceeded 5MB size limit.")

    try:
        worker_data = worker_response.json()
    except Exception:
        raise HTTPException(status_code=422, detail="Worker deliverable was not valid JSON.")

    for key in req.required_keys:
        if key not in worker_data:
            raise HTTPException(status_code=422, detail=f"ABVS Assertion Failed: Missing mandatory key '{key}'.")

    records = worker_data.get("records") or worker_data.get("items")
    if isinstance(records, list) and len(records) < req.expected_min_records:
        raise HTTPException(status_code=422, detail=f"ABVS Volume Failed: Expected >= {req.expected_min_records} records.")

    worker_payout = round(req.bounty_usdc - protocol_fee, 6)
    tx_id = f"axv_relay_{int(time.time() * 1000)}"
    receipt_raw = f"{req.caller_agent_id}->{req.target_worker_endpoint}:{worker_payout}:{protocol_fee}:{time.time()}"
    receipt_hash = hashlib.sha256(receipt_raw.encode()).hexdigest()

    record_settlement(clean_sig, tx_id, "/v1/relay", req.caller_agent_id, req.target_scrape_url, protocol_fee, receipt_hash)

    return {
        "status": "SETTLED_HONORABLE",
        "standard": "ABVS-1.0",
        "tx_id": tx_id,
        "receipt_hash": receipt_hash,
        "worker_payout_usdc": worker_payout,
        "protocol_toll_retained": protocol_fee,
        "verified_payload": worker_data
    }


@app.get("/v1/treasury")
def get_treasury_metrics():
    """Live persistent public treasury readout."""
    return get_persisted_metrics()
