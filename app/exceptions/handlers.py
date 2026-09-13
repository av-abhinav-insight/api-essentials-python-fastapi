from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AccountNotFoundException(Exception):
    def __init__(self, account_id: str):
        self.account_id = account_id


class AccountBlockedException(Exception):
    def __init__(self, account_id: str):
        self.account_id = account_id


class InsufficientBalanceException(Exception):
    def __init__(self, account_id: str):
        self.account_id = account_id


class TransactionLimitExceededException(Exception):
    def __init__(self, account_id: str):
        self.account_id = account_id


class AuthenticationException(Exception):
    pass


class InvalidCredentialsException(Exception):
    pass


class PermissionDeniedException(Exception):
    def __init__(self, role: str, permission: str):
        self.role = role
        self.permission = permission


class AccountAccessForbiddenException(Exception):
    def __init__(self, account_id: str):
        self.account_id = account_id


def _error_response(status_code: int, error_code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error_code": error_code, "message": message, "request_id": None},
    )


async def account_not_found_handler(request: Request, exc: AccountNotFoundException) -> JSONResponse:
    return _error_response(404, "ACCOUNT_NOT_FOUND", f"Account {exc.account_id} was not found.")


async def account_blocked_handler(request: Request, exc: AccountBlockedException) -> JSONResponse:
    return _error_response(409, "ACCOUNT_BLOCKED", f"Account {exc.account_id} is blocked.")


async def insufficient_balance_handler(request: Request, exc: InsufficientBalanceException) -> JSONResponse:
    return _error_response(
        400, "INSUFFICIENT_BALANCE", f"Account {exc.account_id} has insufficient balance for this transfer."
    )


async def transaction_limit_exceeded_handler(request: Request, exc: TransactionLimitExceededException) -> JSONResponse:
    return _error_response(
        422, "TRANSACTION_LIMIT_EXCEEDED", f"Transfer amount exceeds the daily limit for account {exc.account_id}."
    )


async def authentication_handler(request: Request, exc: AuthenticationException) -> JSONResponse:
    return _error_response(401, "UNAUTHORIZED", "Missing or invalid authentication token.")


async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsException) -> JSONResponse:
    return _error_response(401, "INVALID_CREDENTIALS", "Username or password is incorrect.")


async def permission_denied_handler(request: Request, exc: PermissionDeniedException) -> JSONResponse:
    return _error_response(
        403, "PERMISSION_DENIED", f"Role {exc.role} does not have permission '{exc.permission}'."
    )


async def account_access_forbidden_handler(request: Request, exc: AccountAccessForbiddenException) -> JSONResponse:
    return _error_response(403, "ACCOUNT_ACCESS_FORBIDDEN", f"You do not have access to account {exc.account_id}.")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AccountNotFoundException, account_not_found_handler)
    app.add_exception_handler(AccountBlockedException, account_blocked_handler)
    app.add_exception_handler(InsufficientBalanceException, insufficient_balance_handler)
    app.add_exception_handler(TransactionLimitExceededException, transaction_limit_exceeded_handler)
    app.add_exception_handler(AuthenticationException, authentication_handler)
    app.add_exception_handler(InvalidCredentialsException, invalid_credentials_handler)
    app.add_exception_handler(PermissionDeniedException, permission_denied_handler)
    app.add_exception_handler(AccountAccessForbiddenException, account_access_forbidden_handler)
