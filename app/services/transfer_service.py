import logging

import httpx

from app.config import settings
from app.exceptions.handlers import FraudServiceUnavailableException

logger = logging.getLogger("app.transfer_service")


def check_account_status(account: dict) -> bool:
    return account["status"] == "ACTIVE"


def check_transaction_limit(account: dict, amount: float) -> bool:
    return amount <= account["daily_limit"]


def check_balance(account: dict, amount: float) -> bool:
    return account["balance"] >= amount

FRAUD_THRESHOLD = 50_000

def check_fraud(amount: float) -> bool:
    """Return True if the transfer is approved (not flagged by the fraud service).

    Fails closed: if the fraud service is unreachable or errors, raise
    FraudServiceUnavailableException so the transfer is NOT executed.
    """
    if amount < FRAUD_THRESHOLD:
        return True
    try:
        response = httpx.post(
            f"{settings.FRAUD_SERVICE_URL}/fraud/check",
            json={"amount": amount},
            timeout=settings.FRAUD_SERVICE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
        logger.error("fraud_service_unavailable error=%s", exc)
        raise FraudServiceUnavailableException() from exc
    return not response.json()["flagged"]

