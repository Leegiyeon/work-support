from typing import TypedDict

from fastapi import HTTPException


class ErrorDetail(TypedDict):
    code: str
    message: str


def error_detail(code: str, message: str) -> ErrorDetail:
    """Return the stable application error payload used outside validation errors."""

    return {"code": code, "message": message}


def http_error(status_code: int, code: str, message: str) -> HTTPException:
    """Build a FastAPI HTTPException with the stabilized error detail shape."""

    return HTTPException(status_code=status_code, detail=error_detail(code, message))
