import uuid

from fastapi import APIRouter, HTTPException

from app.models.transfer import TransferRequest, TransferResponse
from app.routers.accounts import ACCOUNTS
from app.services import transfer_service

router = APIRouter()


@router.post("/transfers", response_model=TransferResponse)
def create_transfer(transfer: TransferRequest):
    from_account = ACCOUNTS.get(transfer.from_account)
    if from_account is None:
        raise HTTPException(status_code=400, detail="Invalid Account")

    if not transfer_service.check_account_status(from_account):
        raise HTTPException(status_code=400, detail="Not an active account")

    if not transfer_service.check_transaction_limit(from_account, transfer.amount):
        raise HTTPException(status_code=400, detail="Transaction Limit Exceeded")

    if not transfer_service.check_balance(from_account, transfer.amount):
        raise HTTPException(status_code=400, detail="Insufficient Balance")

    return TransferResponse(
        transaction_id=str(uuid.uuid4()),
        from_account=transfer.from_account,
        to_account=transfer.to_account,
        amount=transfer.amount,
        status="PENDING",
    )
