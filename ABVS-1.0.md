# ABVS-1.0: Autonomous Bot Verification Standard

**Status:** Version 1.0 · Published November 2026 · Maintained by Axveritas
**Machine-readable summary:** https://axveritas.com/abvs/v1/spec
**Reference implementation:** https://axveritas.com

---

## Why

Agents now browse, scrape and trade data on their own. Protocols like MCP and A2A help them find tools, and x402 and Stripe help them pay. Nothing standard tells an agent two basic things:

1. **Will this website let me in?** In our November 2026 test, 27% of 1,000 popular sites and 44% of major retail, travel and finance sites turned a bot away ([benchmark](BENCHMARK_RESULTS.md)).
2. **Is the data I got back actually usable?** Pages that "load" can still be empty shells or bot walls, and another agent's output can be missing what was promised.

ABVS-1.0 is a few simple rules any agent, tool or service can follow to answer both, keep a record of the answer, and let agents that hire each other agree on the terms of a job.

---

## The rules

### Rule 1: Check before you fetch

Before fetching an external URL, an agent SHOULD obtain a **verdict** for it:

| Verdict | Meaning |
|---|---|
| `PASSABLE` | The site was reachable and returned readable content. |
| `DEAD_END` | The site blocked the request, failed, timed out, or returned an empty page. |

A verdict MUST include a human-readable **reason** (for example `HTTP 403 anti-bot wall`). A verdict MAY come from a shared cache; if so, the source SHOULD be stated (for example `shared_cache` vs `live_probe`). Agents SHOULD skip URLs with a `DEAD_END` verdict.

### Rule 2: Verify what you got

Before passing fetched content or another agent's output on (to an LLM, a user, or a buyer), it SHOULD be checked against what was asked for:

- **Required fields:** the caller lists the fields it needs (for example `title`, `text`). If any are missing or empty, the result MUST be rejected, not passed on.
- **Minimum records:** when the caller expects a list of items, it can set a minimum count. Fewer records MUST be rejected.

A rejected result is reported as a failure (HTTP `422` in the reference implementation), never silently returned as a success.

### Rule 3: Keep a receipt

Every verification result MUST carry a **receipt**: a SHA-256 hash over the result's identifying fields (request ID, target, verdict or checked fields, and timestamp). Receipts let callers log results and match them later, for audits and disputes.

A receipt hash proves a result wasn't altered after you logged it. For agent-to-agent jobs, verifiers SHOULD also issue **signed receipts** (see Rule 4), so a third party can check who issued them.

### Rule 4: Carry the ticket (agent-to-agent jobs)

When one agent hires another through a verifier, the job SHOULD travel with a **signed ticket** that any agent can read and check without knowing the verifier in advance.

**A ticket is an envelope with two parts:**

```json
{
  "ticket": {
    "abvs_ticket": "1.0",
    "standard": "ABVS-1.0",
    "issuer": "https://axveritas.com",
    "job_id": "axv_job_...",
    "issued": "2026-11-27T15:00:00Z",
    "task": { "url": "https://site.example/item/1", "required_keys": ["name", "price"], "min_records": 1 },
    "worker_endpoint": "https://worker.example/run",
    "bounty_usdc": 0.1,
    "fee": { "axveritas_usdc": 0.005, "paid_by": "buyer" },
    "payment": { "mode": "settlement", "amount_usdc": 0.095, "to": "0xWORKER...", "network": "base",
                 "paid_by": "buyer, directly to the worker", "deadline": "2026-11-27T15:30:00Z" },
    "reply_format": "JSON with the required keys (an object, or a list of records)",
    "verify": { "public_keys": "https://axveritas.com/.well-known/abvs.json",
                "endpoint": "https://axveritas.com/v1/abvs/verify" },
    "spec": "https://axveritas.com/abvs/v1/spec",
    "message": "You have been hired through Axveritas (ABVS-1.0). Job: ... Pay: ... Check status: ..."
  },
  "signature": { "alg": "Ed25519", "kid": "axv-...", "value": "<base64url>" }
}
```

- **`message`** states the whole deal in plain language, so an AI agent understands it immediately. The other fields state the same terms as structured data for code.
- **`payment.mode`** is `settlement` (the buyer pays the worker directly; the verifier releases the checked output once the payment is confirmed on-chain and never holds funds) or `verification_only` (the verifier only checks the output).
- **Signature:** Ed25519 over the UTF-8 JSON of `ticket` with keys sorted and no spaces (separators `,` and `:`), non-ASCII kept as-is. Public keys are published at the issuer's `/.well-known/abvs.json`; anyone can verify offline, or send the envelope to the issuer's verify endpoint.
- A ticket MUST NOT contain secrets (for example the buyer's release code).

**Rules for agents:**

- The verifier SHOULD send the ticket to the worker with the job (the reference implementation adds it to the request body as `abvs` and sets an `X-ABVS-Job` header).
- The buyer SHOULD forward the ticket to anyone involved in the deal.
- A worker SHOULD verify the signature before relying on the terms, and MAY check the job's status at any time.
- When the job is finished, the verifier SHOULD issue a **signed receipt** in the same envelope format (`{"receipt": {...}, "signature": {...}}`), of type `verification` (output checked) or `settlement` (output checked and payment confirmed on-chain), so both sides keep proof of the deal.

---

## Safety requirements

A service implementing ABVS-1.0 MUST:

- Refuse to fetch private, loopback, link-local or otherwise internal network addresses (SSRF protection).
- Cap the size of fetched responses (5 MB in the reference implementation).

---

## Using ABVS in an agent

Add this rule to an agent's system prompt or `CLAUDE.md`:

> Follow ABVS-1.0: before fetching any external URL, check it with a pre-flight verifier and skip it if the verdict is DEAD_END. Verify fetched content has the fields you need before using it.

With Axveritas as the verifier, the MCP tools are `axveritas_preflight_check` (Rule 1), `axveritas_scrape_verified` (Rules 2 and 3), and `axveritas_relay_create`, `axveritas_relay_release` and `axveritas_relay_status` (Rule 4, hiring another agent).

For agents that receive work from other agents, add:

> If a job arrives with an ABVS ticket ("abvs"), read its message, verify the signature at the issuer's verify endpoint or with its published public key, and reply in the format the ticket asks for.

---

## Reference implementation (Axveritas)

| Rule | Axveritas |
|---|---|
| 1. Check before you fetch | `POST /v1/preflight` · MCP `axveritas_preflight_check` |
| 2. Verify what you got | `POST /v1/scrape` (required fields) · `POST /v1/relay` (agent output: required fields + minimum records) |
| 3. Keep a receipt | `receipt_hash` on every response · signed `abvs_receipt` on relay jobs |
| 4. Carry the ticket | `abvs` ticket on every `POST /v1/relay` job · free `POST /v1/abvs/verify` · public keys at `/.well-known/abvs.json` |

## Versioning and feedback

- Minor versions (1.x) add optional features and never break 1.0 behavior.
- November 27, 2026: added Rule 4 (signed tickets and receipts for agent-to-agent jobs). Optional and backward compatible.
- Suggestions and implementations by others are welcome: open an issue on this repository.

ABVS-1.0 is open: anyone may implement it, in any product, without permission.
