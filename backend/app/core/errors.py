"""Business errors. `code` is stable so the frontend can translate it."""
from fastapi import HTTPException


class ApiError(HTTPException):
    def __init__(self, status: int, code: str, message: str, **params):
        super().__init__(status_code=status, detail={"code": code, "message": message, "params": params})


def not_found(what: str) -> ApiError:
    return ApiError(404, "not_found", f"{what} not found", what=what)


def conflict(code: str, message: str, **params) -> ApiError:
    return ApiError(409, code, message, **params)


def bad(code: str, message: str, **params) -> ApiError:
    return ApiError(422, code, message, **params)
