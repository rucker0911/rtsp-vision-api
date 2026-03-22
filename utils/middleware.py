import time

from utils.logManager import LogManager

log = LogManager("request")

_SKIP_PATHS = {"/health/"}


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in _SKIP_PATHS:
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        msg = f"{request.method} {request.path} {response.status_code} {elapsed_ms}ms"

        if response.status_code >= 500:
            log.error(msg)
        elif response.status_code >= 400:
            log.warning(msg)
        else:
            log.info(msg)

        return response
