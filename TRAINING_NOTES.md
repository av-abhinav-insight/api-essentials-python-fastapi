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

---

## Step 3 — Input validation
**Tag:** `module1-step03-input-validation`

### The problem, live

`TransferRequest` currently accepts *any* string for `from_account`/`to_account` and *any* float for `amount` — including negative amounts, an account transferring to itself, or an account ID that isn't shaped like one of ours. The model shape is right; the model *content* isn't checked at all yet.

### The fix: constraints and validators on `TransferRequest`

```python
ACCOUNT_ID_PATTERN = r"^acc-\d{4}$"

class TransferRequest(BaseModel):
    from_account: str = Field(..., pattern=ACCOUNT_ID_PATTERN)
    to_account: str = Field(..., pattern=ACCOUNT_ID_PATTERN)
    amount: float = Field(..., gt=0)

    @model_validator(mode="after")
    def check_accounts_are_different(self):
        if self.from_account == self.to_account:
            raise ValueError("from_account and to_account must be different")
        return self
```

### Demo (Postman) — 5 pre-built bad requests, each a clean `422`

1. **Negative Amount** — `amount: -500` → fails `gt=0`
2. **Zero Amount** — `amount: 0` → fails `gt=0`
3. **Missing Field** — no `to_account` → "field required"
4. **Same Account** — `from_account == to_account` → the `model_validator` message
5. **Bad Account Format** — `from_account: "1001"` (no `acc-` prefix) → fails the pattern

Every one of these returns `422` with field-level (or, for the same-account case, request-level) detail — no `500`s, no silent acceptance.

### Key distinction to teach

**API/input validation** ("is this structurally and syntactically valid?") is everything we just added — shape, format, range. **Business validation** ("should this actually be allowed to happen?") is a different question entirely: is the account blocked? Does the customer have the money? Has today's transfer limit already been hit? Pydantic can't answer any of that — it doesn't know what a "blocked account" is. That's Step 4.

### Production note

> This layer only proves shape, never permission. A request that sails through every constraint here can still be one the business must refuse. Keeping the two concerns in separate layers — models vs. services — is what lets each be tested, and reasoned about, independently.

---

## Step 4 — Business rules
**Tag:** `module1-step04-business-rules`

### The problem, live

Send a request that passes every Step 3 check — well-formed accounts, positive amount, different accounts — from an account that's `BLOCKED`, or that would blow past a daily limit, or that simply doesn't have the money. Right now nothing stops it: the handler builds a `TransferResponse` and returns `200` regardless. Structurally valid isn't the same as *allowed*.

### The fix: a service layer for business rules

`app/services/transfer_service.py`:

```python
def check_account_status(account: dict) -> bool:
    return account["status"] == "ACTIVE"

def check_transaction_limit(account: dict, amount: float) -> bool:
    return amount <= account["daily_limit"]

def check_balance(account: dict, amount: float) -> bool:
    return account["balance"] >= amount
```

`ACCOUNTS` in `routers/accounts.py` gains `status` and `daily_limit` so a blocked account and a limit can actually be demoed — including one account, `acc-1003`, seeded as `BLOCKED`.

`routers/transfers.py` looks up the source account and runs all three checks before building a response. Every failure — account not found, blocked, over-limit, insufficient balance — currently returns the *same* generic `400 {"detail": "transfer rejected"}`. That's deliberate, not an oversight.

### Demo (Postman)

1. **Blocked Account** (`acc-1003`, status `BLOCKED`) → rejected
2. **Over Daily Limit** (`acc-1001`, limit 50,000, amount 60,000) → rejected
3. **Insufficient Balance** (`acc-1002`, balance 12,890, amount 20,000, under its limit) → rejected

All three come back identically shaped. Ask the class: "A customer calls support about a failed transfer. Support asks *why* it failed. What can we tell them right now?" The honest answer is "no idea, from the response alone" — that gap is exactly what Step 5 closes.

### Production note

> Business rules typically live in a rules engine or a config table in a real bank, not hardcoded in a Python function — a limit or a blocked-status flag needs to change without a deploy. We're hardcoding here to keep the teaching focus on the *layering* (models vs. services vs. routing), not on rules-engine design.

---

## Step 5 — Structured error handling
**Tag:** `module1-step05-error-handling`

### The problem, live

Every business-rule rejection from Step 4 comes back as the same generic shape. A frontend developer receiving `400 {"detail": "..."}` has to string-match the message to know what actually went wrong — brittle, and it breaks the moment someone rewords a message.

### The fix: one exception per failure, one consistent error shape

`app/exceptions/handlers.py` defines four exceptions — `AccountNotFoundException`, `AccountBlockedException`, `InsufficientBalanceException`, `TransactionLimitExceededException` — and a FastAPI exception handler per exception, each returning:

```json
{"error_code": "ACCOUNT_BLOCKED", "message": "...", "request_id": null}
```

(`request_id` stays `null` — it gets wired up in Step 10.)

`routers/transfers.py` now `raise`s the matching exception instead of a generic `HTTPException`, and each maps to a distinct status code:

| Exception | Status | `error_code` |
|---|---|---|
| `AccountNotFoundException` | 404 | `ACCOUNT_NOT_FOUND` |
| `InsufficientBalanceException` | 400 | `INSUFFICIENT_BALANCE` |
| `AccountBlockedException` | 409 | `ACCOUNT_BLOCKED` |
| `TransactionLimitExceededException` | 422 | `TRANSACTION_LIMIT_EXCEEDED` |

### Demo (Postman)

Re-run the Step 4 rejection calls — Blocked Account, Over Daily Limit, Insufficient Balance — and this time each comes back with a *different*, meaningful status code and an `error_code` a frontend can safely branch on, instead of one indistinguishable `400`.

### Production note

> The error response is part of the API contract — frontend teams build UI off `error_code` ("this account is blocked, show this specific banner"), never off the Python exception class name or a hardcoded message string that might get reworded next sprint.

---

## Step 7 — Authentication
**Tag:** `module1-step07-authentication`

### The problem, live

Anyone can currently call `GET /accounts/{id}/balance` or `POST /transfers` with no proof of who they are. Fire the "Get Account Balance" request from Postman with no headers at all — it happily returns someone else's balance. There's no concept of a *caller* yet, only a URL.

### Ask the class

"Right now, what stops me from checking *your* balance?" Let the answer be "nothing" before moving on.

### The fix: a signed JWT issued at login, verified on every protected call

Two things get built:

1. **A `POST /auth/login` endpoint** that accepts a `username`/`password` and — deliberately — never checks the password. It exists to demonstrate *issuing* a token, not to be a real login system:

   ```python
   @router.post("/auth/login", response_model=LoginResponse)
   def login(credentials: LoginRequest):
       user = authenticate_user(credentials.username)   # password ignored on purpose
       token = create_access_token(user)
       return LoginResponse(access_token=token)
   ```

   `app/auth.py` holds a hardcoded `USERS` dict (username → `user_id`, `account_id`, `role`) — the same "hardcoded dict" pattern as `ACCOUNTS`. `create_access_token` builds a JWT payload (`sub`, `account_id`, `role`, `exp`) and signs it with `PyJWT` using a secret from a new `AUTH_TOKEN_SECRET` setting in `config.py` (plus `AUTH_TOKEN_EXPIRE_MINUTES`, default 30).

2. **A `get_current_user` dependency** that reads `Authorization: Bearer <token>` (via FastAPI's `HTTPBearer`), verifies the JWT signature and expiry, and returns the decoded claims. Applied to `GET /accounts/{id}/balance` and `POST /transfers`:

   ```python
   @router.get("/accounts/{account_id}/balance")
   def get_balance(account_id: str, user: dict = Depends(get_current_user)):
       ...
   ```

   A missing token, a garbage string, or a tampered/expired JWT all raise a new `AuthenticationException`, wired into `exceptions/handlers.py` exactly like the Step 5 exceptions:

   ```json
   {"error_code": "UNAUTHORIZED", "message": "Missing or invalid authentication token.", "request_id": null}
   ```

   An unknown username at `/auth/login` gets its own exception, `InvalidCredentialsException` → `401 {"error_code": "INVALID_CREDENTIALS", ...}` — a different `error_code` from a bad token, because they're different problems for a frontend to handle.

### Demo (Postman)

1. **Login - Asha** → `200`, returns a JWT. A Postman test script on this request stores it in the `access_token` collection variable automatically.
2. **Get Account Balance - No Token** → `401 UNAUTHORIZED`.
3. **Get Account Balance** (now sends `Authorization: Bearer {{access_token}}`) → `200`.
4. **Login - Unknown User** → `401 INVALID_CREDENTIALS`.
5. Re-run any of the Step 3/4 transfer requests — they now carry the same bearer token and still succeed/fail on the same rules as before; auth is a layer *in front of* everything already built, not a replacement for it.

### Teach

**Authentication** ("who are you?") is everything built today — proving identity via a credential. **Authorization** ("what are you allowed to do?") is the next question entirely: today, Asha's token can read *anyone's* balance, not just `acc-1001`. That gap is Step 8.

### Production note

> Real systems don't hand-roll JWT issuance like this — they delegate to an identity provider over OIDC/OAuth2 (Auth0, Okta, Azure AD, Google Identity...), so the API only ever *verifies* tokens it didn't create, against keys it fetches from the provider. We're signing and verifying with our own secret here to keep the demo self-contained and focused on the concept — the mechanics (JWT structure, signature verification, expiry) transfer directly to the real thing.

---

## Step 8 — Authorization (RBAC)
**Tag:** `module1-step08-authorization`

### The problem, live

Step 7 proves *who* is calling, but says nothing about what they're allowed to do. Log in as Asha and transfer money out of Ravi's account, or check anyone's balance with anyone's token — every authenticated caller is currently equally powerful. Fire a transfer from Asha's token against `acc-1002` (not her account) from Postman — it succeeds. That's the gap.

### Ask the class

"Asha's token is valid. Should that mean Asha can touch *any* account, or just her own? And should every valid token be allowed to move money at all?"

### The fix: two independent checks — role permission, then resource ownership

The class has defined two roles beyond `ADMIN`: **`LITE_CUSTOMER`** (read-only) and **`STD_CUSTOMER`** (can also transfer). `app/auth.py` maps each role to what it's allowed to *do*, independent of *which* account:

```python
ROLE_PERMISSIONS = {
    "LITE_CUSTOMER": {"account:read"},
    "STD_CUSTOMER": {"account:read", "transfer:create"},
    "ADMIN": {"account:read", "transfer:create"},
}

ADMIN_ROLES = {"ADMIN"}
```

Two RBAC primitives sit on top of Step 7's `get_current_user`:

1. **`require_permission(permission)`** — a dependency *factory*. `Depends(require_permission("transfer:create"))` on a route means: run `get_current_user` first, then check the resulting role actually has that permission. `LITE_CUSTOMER` has no `transfer:create`, so it's rejected before the handler body ever runs — a new `PermissionDeniedException` → `403 {"error_code": "PERMISSION_DENIED", ...}`.

2. **`ensure_account_access(user, account_id)`** — called inside the handler once we know *which* account is being touched (the path param for balance, `from_account` for a transfer). A `LITE_CUSTOMER`/`STD_CUSTOMER` may only act on their own `account_id`; `ADMIN` bypasses this entirely. Mismatch → a new `AccountAccessForbiddenException` → `403 {"error_code": "ACCOUNT_ACCESS_FORBIDDEN", ...}`.

```python
@router.get("/accounts/{account_id}/balance")
def get_balance(account_id: str, user: dict = Depends(require_permission("account:read"))):
    ensure_account_access(user, account_id)
    ...

@router.post("/transfers", response_model=TransferResponse)
def create_transfer(transfer: TransferRequest, user: dict = Depends(require_permission("transfer:create"))):
    ensure_account_access(user, transfer.from_account)
    ...
```

Two different 403s on purpose: `PERMISSION_DENIED` means "your role can't do this action, on any account." `ACCOUNT_ACCESS_FORBIDDEN` means "you *can* do this action, just not on this account." A frontend needs to tell those apart — one might mean "show an upgrade prompt," the other "you searched for the wrong account."

### Demo (Postman)

1. **Login - Asha (LITE_CUSTOMER)**, then **RBAC - Lite Customer Reads Own Balance** → `200`.
2. **RBAC - Lite Customer Reads Others Balance (403)** (`acc-1002` with Asha's token) → `403 ACCOUNT_ACCESS_FORBIDDEN`.
3. **RBAC - Lite Customer Attempts Transfer (403 Permission Denied)** → `403 PERMISSION_DENIED` — rejected on role alone, before account ownership is even checked.
4. **Login - Ravi (STD_CUSTOMER)**, then **RBAC - Std Customer Transfers Own Account** → `200`.
5. **RBAC - Std Customer Transfers Others Account (403)** (`from_account: acc-1001` with Ravi's token) → `403 ACCOUNT_ACCESS_FORBIDDEN` — Ravi *has* the permission, just not on someone else's account.
6. **Login - Admin**, then **RBAC - Admin Transfers Any Account** and **RBAC - Admin Reads Any Balance** → both `200` — `ADMIN` has every permission and bypasses ownership.

### Production note

> At scale, authorization decisions live in a centralized policy layer or permissions table — not scattered `if` checks copy-pasted across every route — so a rule change ships without touching route code, and every service enforces the same policy consistently. `ROLE_PERMISSIONS` here is that same idea in miniature: a hardcoded table now, a policy service later.

---

## Step 9 — Logging
**Tag:** `module1-step09-logging`

### Framing

"Yesterday a customer said their ₹10,000 transfer failed. How do we find out what happened?" Right now: we can't. The API returns an answer to the caller and then remembers nothing.

### The fix: structured log lines through the transfer flow

`app/main.py` configures `logging.basicConfig()` using a new `LOG_LEVEL` setting in `config.py` (defaults to `INFO`, override with the `LOG_LEVEL` env var).

`routers/transfers.py` emits one log line at each meaningful point in the flow — `transaction_started`, `account_not_found`, `account_blocked`, `account_validation_success`, `transaction_limit_exceeded`, `insufficient_balance`, `transaction_completed` — each carrying `transaction_id`, `account_id`, and `status`:

```
transaction_started transaction_id=... account_id=acc-1003 status=STARTED
account_blocked transaction_id=... account_id=acc-1003 status=REJECTED
```

Notice what's *not* logged: the transfer `amount`, and never the full `account_number` — only the logical `account_id`. That's deliberate, not an omission (see the production note).

The `transaction_id` is now generated once, at the very start of `create_transfer`, before any validation runs — so every log line for one request, successful or rejected, shares the same id.

### Demo

Run the server in one terminal, tail its console output, and fire the "Transfer - Blocked Account" (or any other rejection) request from Postman in another window. Point at the `account_blocked ... status=REJECTED` line that appears the instant the request lands — the log line is the answer to the customer-support question from the framing.

### Production note

> Never log tokens, PINs, full account numbers, or full transfer amounts if policy requires masking — this is a real audit/compliance concern in banking, not a style preference. Logging the logical `account_id` (`acc-1003`) instead of the real account number, and omitting `amount` entirely, is the smallest version of that discipline.
