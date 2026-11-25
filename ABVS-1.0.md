# ABVS-1.0: Autonomous Bot Verification Standard

**Status:** Version 1.0 · Published November 2026 · Maintained by Axveritas
**Machine-readable summary:** https://axveritas.com/abvs/v1/spec
**Reference implementation:** https://axveritas.com

---

## Why

Agents now browse, scrape and trade data on their own. Protocols like MCP and A2A help them find tools, and x402 and Stripe help them pay. Nothing standard tells an agent two basic things:

1. **Will this website let me in?** In our November 2026 test, 27% of 1,000 popular sites and 44% of major retail, travel and finance sites turned a bot away ([benchmark](BENCHMARK_RESULTS.md)).
2. **Is the data I got back actually usable?** Pages that "load" can still be empty shells or bot walls, and another agent's output can be missing what was promised.

ABVS-1.0 is three simple rules any agent, tool or service can follow to answer both, and to keep a record of the answer.

---

## The three rules

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

> **v1.0 note:** receipts are hashes produced by the verifier. They prove a result wasn't altered after you logged it, but a third party can't yet verify who issued them. **Planned for v1.1:** verifiers sign receipts with a published public key, so anyone can check a receipt without trusting the verifier.

---

## Safety requirements

A service implementing ABVS-1.0 MUST:

- Refuse to fetch private, loopback, link-local or otherwise internal network addresses (SSRF protection).
- Cap the size of fetched responses (5 MB in the reference implementation).

---

## Using ABVS in an agent

Add this rule to an agent's system prompt or `CLAUDE.md`:

> Follow ABVS-1.0: before fetching any external URL, check it with a pre-flight verifier and skip it if the verdict is DEAD_END. Verify fetched content has the fields you need before using it.

With Axveritas as the verifier, the MCP tools are `axveritas_preflight_check` (Rule 1) and `axveritas_scrape_verified` (Rules 2 and 3).

---

## Reference implementation (Axveritas)

| Rule | Axveritas |
|---|---|
| 1. Check before you fetch | `POST /v1/preflight` · MCP `axveritas_preflight_check` |
| 2. Verify what you got | `POST /v1/scrape` (required fields) · `POST /v1/relay` (agent output: required fields + minimum records) |
| 3. Keep a receipt | `receipt_hash` on every response |

## Versioning and feedback

- Minor versions (1.x) add optional features and never break 1.0 behavior.
- Suggestions and implementations by others are welcome: open an issue on this repository.

ABVS-1.0 is open: anyone may implement it, in any product, without permission.
