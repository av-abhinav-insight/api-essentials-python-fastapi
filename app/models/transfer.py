from pydantic import BaseModel


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
