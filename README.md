# api-essentials-python-fastapi

A production-style banking API, built up one training step at a time. See [TRAINING_NOTES.md](TRAINING_NOTES.md) for the instructor script and [plan.md](plan.md) for the full module plan.

## Requirements

- Python 3.11+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

The API is now available at `http://127.0.0.1:8000`.

- `GET /health` — health check
- `GET /accounts/{account_id}/balance` — account balance (try `acc-1001` or `acc-1002`)

Interactive API docs (Swagger UI) are auto-generated at `http://127.0.0.1:8000/docs`.

## Testing the API

No automated test suite — every step is verified manually via Postman and/or the browser. Import the collection at [postman/banking-api.postman_collection.json](postman/banking-api.postman_collection.json) into Postman to exercise the endpoints.
