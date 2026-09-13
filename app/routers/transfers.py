import logging
import uuid

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.exceptions.handlers import (
    AccountBlockedException,
    AccountNotFoundException,
    InsufficientBalanceException,
    TransactionLimitExceededException,
)
from app.models.transfer import TransferRequest, TransferResponse
from app.routers.accounts import ACCOUNTS
from app.services import transfer_service

router = APIRouter()
logger = logging.getLogger("app.transfers")


def _log(event: str, level: int, transaction_id: str, account_id: str, status: str) -> None:
    logger.log(
        level,
        "%s transaction_id=%s account_id=%s status=%s",
        event,
        transaction_id,
        account_id,
        status,
    )


@router.post("/transfers", response_model=TransferResponse)
def create_transfer(transfer: TransferRequest, user: dict = Depends(get_current_user)):
    transaction_id = str(uuid.uuid4())
    _log("transaction_started", logging.INFO, transaction_id, transfer.from_account, "STARTED")

    from_account = ACCOUNTS.get(transfer.from_account)
    if from_account is None:
        _log("account_not_found", logging.WARNING, transaction_id, transfer.from_account, "REJECTED")
        raise AccountNotFoundException(transfer.from_account)

    if not transfer_service.check_account_status(from_account):
        _log("account_blocked", logging.WARNING, transaction_id, transfer.from_account, "REJECTED")
        raise AccountBlockedException(transfer.from_account)

    _log("account_validation_success", logging.INFO, transaction_id, transfer.from_account, "VALIDATED")

    if not transfer_service.check_transaction_limit(from_account, transfer.amount):
        _log("transaction_limit_exceeded", logging.WARNING, transaction_id, transfer.from_account, "REJECTED")
        raise TransactionLimitExceededException(transfer.from_account)

    if not transfer_service.check_balance(from_account, transfer.amount):
        _log("insufficient_balance", logging.WARNING, transaction_id, transfer.from_account, "REJECTED")
        raise InsufficientBalanceException(transfer.from_account)

    _log("transaction_completed", logging.INFO, transaction_id, transfer.from_account, "PENDING")

    return TransferResponse(
        transaction_id=transaction_id,
        from_account=transfer.from_account,
        to_account=transfer.to_account,
        amount=transfer.amount,
        status="PENDING",
    )
