# Module 1: Building a Production-Style Banking API
**Instructor script — narrative, demo steps, and production notes per stage.**

This document is the live instructor script for the module. Each step below corresponds to a git tag (`module1-stepNN-name`). Update it as you go — it should always read as the story you tell the class, not just a changelog.

---

## Step 0 — Understand the problem before coding
**Tag:** `module1-step00-problem`

### No code in this step.

Today we don't write a single line of code. Before we build anything, we need to agree on *what* we're building and *why* it needs to be an API at all.

### The requirement given to the class

> "Build a banking service where a customer can check balance, view account details, transfer money, and check transaction status."

Read this out loud. Resist the urge to jump into design — sit with it for a minute. It sounds simple. It is not simple once real users, real money, and real failure modes are involved. That gap is the entire subject of this module.

### Discussion prompts (talk through these with the class, no code)

- **What is the client? What is the server?**
  Who initiates the request — a mobile app, a web app, another bank's system? Who owns and runs the logic that actually moves money?

- **What does the client send? What does the API return?**
  If a customer wants to transfer ₹5,000, what information must the client provide, and what should come back — just "success," or something more?

- **HTTP request vs. response.**
  Walk through the shape of an HTTP request (method, URL, headers, body) and a response (status code, headers, body) using the transfer example above.

- **Endpoint, method, status code, JSON.**
  Introduce these as vocabulary, not implementation. An *endpoint* is a URL the client can call. A *method* (GET, POST, ...) says what kind of action it is. A *status code* tells the client what happened, without it having to read a message. *JSON* is the shared language both sides agree to speak.

### Target operations (for reference — not built yet)

These are the operations implied by the requirement above. We will build toward these over the coming steps, one at a time:

- Get account (details)
- Get balance
- List transactions
- Create transfer
- Check transfer status
- Check transaction limit
- Check account status

Do not build any of this yet. The point of this step is that a team should be able to look at this list and agree on it *before* anyone opens an editor.

### Production note

> Every API starts as an agreed contract between teams before it's code. In a real organization, the list of operations above would be hashed out between backend, frontend/mobile, and often a business analyst — before a single endpoint exists. Skipping this conversation is how teams end up rebuilding APIs three times.

---

## Step 1 — Simplest FastAPI app, with correct structure and config from day one
**Tag:** `module1-step01-basic-api`

### What we build

Only two endpoints today — `GET /health` and `GET /accounts/{account_id}/balance` — both backed by a hardcoded dict. But we lay out the **full** project structure now, even though most of it is empty:

```
app/
 ├── main.py
 ├── config.py
 ├── routers/
 │    ├── accounts.py       ← built today
 │    └── transfers.py      ← placeholder, Step 2
 ├── models/
 │    ├── account.py        ← placeholder, Step 2
 │    └── transfer.py       ← placeholder, Step 2
 ├── services/
 │    └── transfer_service.py  ← placeholder, Step 4
 └── exceptions/
      └── handlers.py       ← placeholder, Step 5
requirements.txt
postman/banking-api.postman_collection.json
```

`main.py` does nothing but assemble the app:

```python
app = FastAPI()
app.include_router(accounts.router)
```

`config.py` starts as small as possible — one environment-driven setting:

```python
import os
class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "local")
settings = Settings()
```

### Demo

1. `pip install -r requirements.txt`
2. `uvicorn app.main:app --reload`
3. Open `http://127.0.0.1:8000/health` in the browser → `{"status": "ok"}`
4. Open `http://127.0.0.1:8000/accounts/acc-1001/balance` → balance JSON
5. Repeat both calls from the "Health Check" and "Get Account Balance" requests in the Postman collection.

### Ask the class

Before revealing the folder structure, ask: "We're building two endpoints. Why would we need `routers/`, `models/`, `services/`, and `exceptions/` folders for that?" Let them sit with the apparent overkill — it sets up the production note.

### Production note

> This looks like more ceremony than two endpoints need — that's intentional. Real teams decide structure and config discipline *before* the first feature, because retrofitting them onto a live production codebase later is expensive and risky. We're paying that cost now, once, while it's cheap.

---

## Step 2 — Request and response models
**Tag:** `module1-step02-request-response-models`

### The problem, live

Add `POST /transfers` first with the crudest possible signature — accept a raw `dict` body and echo it back:

```python
@router.post("/transfers")
def create_transfer(transfer: dict):
    return transfer
```

Hit it from Postman with a well-formed body first — it works. Then send it something malformed: a missing field, or `"amount": "not-a-number"`. Depending on what the handler does with the dict, this either throws an unhandled `500` or silently accepts garbage. Either way, it's a bad outcome, and it's *silent* — nothing told the caller their request was wrong in a way they could act on.

### Ask the class

"Whose job is it to know what a valid transfer request looks like — mobile app? backend? Both, separately, and hope they agree?"

### The fix: typed models

Introduce `models/transfer.py`:

```python
class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float

class TransferResponse(BaseModel):
    transaction_id: str
    from_account: str
    to_account: str
    amount: float
    status: str
```

And `models/account.py`:

```python
class AccountResponse(BaseModel):
    account_id: str
    account_number: int
    account_holder: str
    balance: float
```

Rewire `routers/transfers.py` to take a `TransferRequest` and return a `TransferResponse` via `response_model=`. `AccountResponse` is introduced now but not wired into an endpoint yet — that lands in Step 6 when `GET /accounts/{id}` is added.

### Demo (Postman)

1. "Create Transfer - Malformed Body" → clean `422` with field-by-field detail (which field, what was expected) instead of a `500` or silent garbage.
2. "Create Transfer - Valid" → `200` with a `TransferResponse` body, including a generated `transaction_id` and `status: "PENDING"`.

### Production note

> Contracts are how frontend/backend/mobile teams stay decoupled — each team codes against the shape of `TransferRequest`/`TransferResponse`, not against each other's implementation. In enterprises, this pays off further: FastAPI's generated OpenAPI schema can drive auto-generated client SDKs, so a mobile team never hand-writes a request struct that could drift from what the backend actually expects.
