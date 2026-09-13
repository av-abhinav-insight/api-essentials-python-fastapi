from pydantic import BaseModel, Field, model_validator

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


class TransferResponse(BaseModel):
    transaction_id: str
    from_account: str
    to_account: str
    amount: float
    status: str
