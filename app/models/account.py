from pydantic import BaseModel


class AccountResponse(BaseModel):
    account_id: str
    account_number: int
    account_holder: str
    balance: float
