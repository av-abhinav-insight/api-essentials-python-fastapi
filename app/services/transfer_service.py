def check_account_status(account: dict) -> bool:
    return account["status"] == "ACTIVE"


def check_transaction_limit(account: dict, amount: float) -> bool:
    return amount <= account["daily_limit"]


def check_balance(account: dict, amount: float) -> bool:
    return account["balance"] >= amount
