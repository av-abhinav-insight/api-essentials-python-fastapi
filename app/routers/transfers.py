import uuid

from fastapi import APIRouter

from app.models.transfer import TransferRequest, TransferResponse

router = APIRouter()


@router.post("/transfers", response_model=TransferResponse)
def create_transfer(transfer: TransferRequest):
    return TransferResponse(
        transaction_id=str(uuid.uuid4()),
        from_account=transfer.from_account,
        to_account=transfer.to_account,
        amount=transfer.amount,
        status="PENDING",
    )
