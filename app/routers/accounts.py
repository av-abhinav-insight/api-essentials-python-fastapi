from fastapi import APIRouter

router = APIRouter()

ACCOUNTS = {
    "acc-1001": {
        "account_id": "acc-1001",
        "account_number": 1234355753,
        "account_holder": "Asha Rao",
        "balance": 45230.50,
        "status": "ACTIVE",
        "daily_limit": 50000,
    },
    "acc-1002": {
        "account_id": "acc-1002",
        "account_number": 1234355754,
        "account_holder": "Ravi Kumar",
        "balance": 12890.00,
        "status": "ACTIVE",
        "daily_limit": 50000,
    },
    "acc-1003": {
        "account_id": "acc-1003",
        "account_number": 1234355755,
        "account_holder": "Meera Iyer",
        "balance": 100000.00,
        "status": "BLOCKED",
        "daily_limit": 50000,
    },
}


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/accounts/{account_id}/balance")
def get_balance(account_id: str):
    account = ACCOUNTS.get(account_id)
    if account is None:
        return {"error": "account not found"}
    return {"account_id": account["account_id"], "balance": account["balance"]}
