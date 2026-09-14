from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class FraudCheckRequest(BaseModel):
    amount: float
    from_account: str | None = None
    to_account: str | None = None

class FraudCheckResponse(BaseModel):
    flagged: bool
    reason: str | None = None

FRAUD_THRESHOLD = 50_000

@app.post("/fraud/check", response_model=FraudCheckResponse)
def check_fraud(request: FraudCheckRequest) -> FraudCheckResponse:
    if request.amount > FRAUD_THRESHOLD:
        return FraudCheckResponse(flagged=True, reason="Amount exceeds fraud threshold.")
    return FraudCheckResponse(flagged=False)