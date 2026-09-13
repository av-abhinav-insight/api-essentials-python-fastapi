Here's the full, consolidated plan — folder structure fixed from Step 1, config baked in as-you-go, no refactor step. This is written as a direct build spec for Claude Code.

---

# Module 1: Building a Production-Style Banking API
**Audience:** Fresh graduates, new joiners at Insight Enterprises
**Goal:** Understand why APIs exist and how they're engineered in enterprise settings — by evolving one banking demo, one small step at a time
**Stack:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2
**Testing approach:** No unit/integration tests. Every step is verified manually via Postman and/or browser. A Postman collection is maintained and updated alongside the code.
**Git approach:** One commit + one tag per step. Tags let the instructor `git checkout module1-stepNN-name` live during training and diff forward to show exactly what changed.

---

## Fixed project structure (established in Step 1, never restructured)

```
app/
 ├── main.py                # FastAPI() instance + router registration only
 ├── config.py               # environment-driven settings, extended incrementally
 ├── routers/
 │    ├── accounts.py
 │    └── transfers.py
 ├── models/
 │    ├── account.py
 │    └── transfer.py
 ├── services/
 │    └── transfer_service.py
 └── exceptions/
      └── handlers.py
requirements.txt
postman/banking-api.postman_collection.json
TRAINING_NOTES.md            # instructor script: narrative, demo steps, production notes per stage
```

This structure does not change for the rest of the module. Every step adds files into these folders — it never gets reorganized.

---

## Step 0 — Understand the problem before coding
**Tag:** `module1-step00-problem`

**Build:** Nothing. Only `TRAINING_NOTES.md` with the business requirement and discussion prompts.

**Requirement given to the class:**
> "Build a banking service where a customer can check balance, view account details, transfer money, and check transaction status."

**Discuss (no code):**
- What is the client? What is the server?
- What does the client send? What does the API return?
- HTTP request vs. response
- Endpoint, method, status code, JSON

**Target operations (for reference, not built yet):** get account, get balance, list transactions, create transfer, check transfer status, check transaction limit, check account status.

**Production note:** Every API starts as an agreed contract between teams before it's code.

---

## Step 1 — Simplest FastAPI app, with correct structure and config from day one
**Tag:** `module1-step01-basic-api`

**Build:**
- Full folder structure above, created now — even though today's logic is tiny.
- `app/config.py` created with just:
  ```python
  import os
  class Settings:
      APP_ENV: str = os.getenv("APP_ENV", "local")
  settings = Settings()
  ```
- `routers/accounts.py`: `GET /health`, `GET /accounts/{account_id}/balance`, hardcoded dict data.
- `main.py` only does `app = FastAPI()` and `app.include_router(...)`.

**Demo:** `uvicorn app.main:app --reload`; hit both endpoints in browser, then Postman.

**Production note:** "This looks like more ceremony than two endpoints need — that's intentional. Real teams decide structure and config discipline *before* the first feature, because retrofitting them onto a live production codebase later is expensive and risky. We're paying that cost now, once, while it's cheap."

---

## Step 2 — Request and response models
**Tag:** `module1-step02-request-response-models`

**Build:**
- Add `POST /transfers` to `routers/transfers.py`, first accepting a raw `dict` — show it break live with malformed JSON.
- Introduce `models/transfer.py` (`TransferRequest`, `TransferResponse`) and `models/account.py` (`AccountResponse`).

**Demo (Postman):** malformed body against the dict version (crashes/500) → same body against the model version (clean 422).

**Production note:** Contracts are how frontend/backend/mobile teams stay decoupled. Mention OpenAPI-driven client generation as the enterprise payoff.

---

## Step 3 — Input validation
**Tag:** `module1-step03-input-validation`

**Build:** Pydantic constraints/validators on `TransferRequest`: `amount > 0`, account ID format, `from_account != to_account`, required fields.

**Demo (Postman):** 5 pre-built "bad request" calls — negative amount, zero, missing field, same account, bad format — each returns a clean 422 with field-level detail.

**Key distinction to teach:** API/input validation ("is this structurally valid?") vs. business validation ("should this actually be allowed?") — kept separate on purpose, sets up Step 4.

**Production note:** This layer only proves shape, never permission.

---

## Step 4 — Business rules
**Tag:** `module1-step04-business-rules`

**Build:** `services/transfer_service.py` with `check_account_status()`, `check_balance()`, `check_transaction_limit()`. Add `status` and `daily_limit` fields to hardcoded account data so a `BLOCKED` account can be demoed.

**Demo (Postman):** valid-shape request against a blocked account → rejection; over-limit amount → rejection; insufficient balance → rejection. Responses are still generic at this point (deliberate gap, closed in Step 5).

**Production note:** Business rules typically live in a rules engine or config table in real banks, not hardcoded — flag it, don't build it.

---

## Step 5 — Structured error handling
**Tag:** `module1-step05-error-handling`

**Build:**
- `exceptions/handlers.py`: custom exceptions (`AccountNotFoundException`, `InsufficientBalanceException`, `AccountBlockedException`, `TransactionLimitExceededException`) + FastAPI exception handlers mapping each to the right status code and a consistent error JSON shape, e.g.:
  ```json
  {"error_code": "ACCOUNT_BLOCKED", "message": "...", "request_id": null}
  ```
  (`request_id` stays `null` for now — wired up in Step 10.)

**Demo (Postman):** re-run the Step 3/4 bad-request calls, now showing distinct 400/404/409/422 instead of generic 500s.

**Production note:** The error response is part of the API contract — frontend teams build UI off `error_code`, not the Python exception class name.

---

## Step 6 — REST semantics cleanup
**Tag:** `module1-step06-rest-design`

**Build:** No new logic. Confirm `GET`/`POST` usage; add `GET /accounts/{id}`, `GET /accounts/{id}/transactions`, `GET /transfers/{transaction_id}`; decide 200 vs. 201 for a successful transfer.

**Demo:** Ask the class live — "GET or POST here? 200 or 201 there?" — before revealing the answer. Glance at `/docs` (not formally taught yet).

**Production note:** Idempotency — a naive retry of `POST /transfers` could double-charge. Name it as a real concern; don't solve it here.

---

## Step 7 — Authentication
**Tag:** `module1-step07-authentication`

**Build:**
- Simple static Bearer token check as a FastAPI dependency (hardcoded token → user map, or a dummy signed JWT for extra realism), applied to `GET /accounts/{id}/balance` and the transfer endpoints.
- Extend `config.py`: `AUTH_TOKEN_SECRET`.

**Demo (Postman):** call without header → 401; with header → 200.

**Teach:** Authentication (who are you?) vs. authorization (what are you allowed to do?).

**Production note:** Real systems use OIDC/OAuth2 with an identity provider, not static tokens — name-drop, don't implement.

---

## Step 8 — Authorization
**Tag:** `module1-step08-authorization`

**Build:** Attach a role (`CUSTOMER` / `BANK_EMPLOYEE` / `ADMIN`) to the dummy token map; enforce that a `CUSTOMER` token can only access its own `account_id`.

**Demo (Postman):** User A's token against User A's account → 200; against User B's account → 403.

**Production note:** At scale, authorization decisions live in a centralized policy layer or permissions table, not scattered `if` checks.

---

## Step 9 — Logging
**Tag:** `module1-step09-logging`

**Build:**
- Python `logging` config; structured log lines through the transfer flow (`transaction_started`, `account_validation_success`, `transaction_limit_exceeded`, etc.) including `account_id`, `transaction_id`, `status`.
- Extend `config.py`: `LOG_LEVEL`.

**Framing:** "Yesterday a customer said their ₹10,000 transfer failed. How do we find out what happened?"

**Demo:** tail console/log output while making a Postman call; point at the matching log line for a rejection.

**Production note:** Never log tokens, PINs, full account numbers, or full amounts if policy requires masking — a real audit/compliance concern in banking.

---

## Step 10 — Request/correlation IDs
**Tag:** `module1-step10-request-tracing`

**Build:** Middleware that generates/accepts `X-Request-ID`, injects it into every log line and into the `request_id` field of the error response body (from Step 5).

**Demo:** Send a request that fails business rules; show the same `req-id` across 3–4 consecutive log lines.

**Production note:** This is the seed of distributed tracing — correlation IDs are how a multi-service call chain gets debugged in production.

---

## Step 11 — API documentation (Swagger/OpenAPI)
**Tag:** `module1-step11-api-documentation`

**Build:** No new logic. Add `summary`/`description`/`response_model` metadata to routes so `/docs` reads well.

**Demo:** Execute a call directly from Swagger UI, including the Bearer token. Reveal that FastAPI has been generating this all along.

**Production note:** The OpenAPI spec is what enterprises use to auto-generate client SDKs and drive contract testing between teams.

---

## Step 12 — Call an external service
**Tag:** `module1-step12-external-service`

**Build:**
- Second tiny FastAPI app: `fraud_service/main.py` with `POST /fraud/check` (trivial rule, e.g. amount > 50,000 → flagged).
- Banking API calls it via an HTTP client for transfers above the threshold.
- Extend `config.py`: `FRAUD_SERVICE_URL`.

**Demo:** Run both apps; Postman call above the threshold shows the fraud check firing; below it, the check is skipped.

**Production note:** Service-to-service calls introduce a new dependency and failure mode — sets up Step 13.

---

## Step 13 — Handle external-service failures
**Tag:** `module1-step13-external-failure-handling`

**Build:**
- Connection error / timeout handling around the fraud-service call; on failure, do **not** execute the transaction — return a controlled error response instead.
- Extend `config.py`: `FRAUD_SERVICE_TIMEOUT_SECONDS`.

**Demo:** Kill the fraud service, then hit `/transfers` above the threshold from Postman — show a clean, controlled error instead of a crash.

**Framing:** "Our code is correct. Why is the application still failing?"

**Production note:** Basic retry can be mentioned conceptually; deeper resilience (circuit breakers, backoff) is out of scope for this module — flag it as a later topic.

---

## Suggested Git tag sequence (14 steps total)

```
module1-step00-problem
module1-step01-basic-api
module1-step02-request-response-models
module1-step03-input-validation
module1-step04-business-rules
module1-step05-error-handling
module1-step06-rest-design
module1-step07-authentication
module1-step08-authorization
module1-step09-logging
module1-step10-request-tracing
module1-step11-api-documentation
module1-step12-external-service
module1-step13-external-failure-handling
```

## Delivery pattern for every step (keep this consistent)

**Requirement → Problem → Demonstrate the failure → Ask the class what's wrong → Introduce the concept → Change the code → Test again in Postman.**

Never frame a step as "today we learn X" — always let the previous step's gap motivate the next one.