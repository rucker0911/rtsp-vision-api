import traceback

from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from utils.logManager import LogManager
from utils.responses import (
    FORBIDDEN_403,
    INVALID_INPUT_422,
    NOT_FOUND_404,
    SERVER_ERROR_500,
    UNAUTHORIZED_401,
    response_with,
)

log = LogManager("exceptions")

_DRF_STATUS_MAP = {
    status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_401,
    status.HTTP_403_FORBIDDEN: FORBIDDEN_403,
    status.HTTP_404_NOT_FOUND: NOT_FOUND_404,
}


def custom_exception_handler(exc, context) -> Response:
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()

    response = exception_handler(exc, context)

    if response is not None:
        return _handle_drf_exception(exc, response)

    return _handle_unexpected_exception(exc, context)


def _handle_drf_exception(exc, response: Response) -> Response:
    if isinstance(exc, exceptions.ValidationError):
        return response_with(INVALID_INPUT_422, error=response.data)

    mapped = _DRF_STATUS_MAP.get(response.status_code)
    if mapped:
        return response_with(mapped)

    return Response(
        {"code": "serverError", "message": str(exc)},
        status=response.status_code,
    )


def _handle_unexpected_exception(exc, context) -> Response:
    view = context.get("view")
    log.error(
        f"Unhandled exception in {view.__class__.__name__ if view else 'unknown'}: "
        f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
    )
    return response_with(SERVER_ERROR_500)
