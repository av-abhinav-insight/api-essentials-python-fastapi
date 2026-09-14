import httpx
from app.config import settings
def check_account_status(account: dict) -> bool:
    return account["status"] == "ACTIVE"


def check_transaction_limit(account: dict, amount: float) -> bool:
    return amount <= account["daily_limit"]


def check_balance(account: dict, amount: float) -> bool:
    return account["balance"] >= amount

FRAUD_THRESHOLD = 50_000

def check_fraud(amount: float) -> bool:
    if amount < FRAUD_THRESHOLD:
        return True
    response = httpx.post(
        f"{settings.FRAUD_SERVICE_URL}/fraud/check", json={"amount": amount}, timeout=5.0
    )
    response.raise_for_status()
    return not response.json()["flagged"]

