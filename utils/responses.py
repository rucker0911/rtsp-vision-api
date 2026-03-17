from rest_framework.response import Response

INVALID_FIELD_NAME_SENT_422 = {
    "http_code": 422,
    "code": "invalidField",
    "message": "Invalid fields found",
}

INVALID_INPUT_422 = {
    "http_code": 422,
    "code": "invalidInput",
    "message": "Invalid input",
}

MISSING_PARAMETERS_422 = {
    "http_code": 422,
    "code": "missingParameter",
    "message": "Missing parameters.",
}

BAD_REQUEST_400 = {
    "http_code": 400,
    "code": "badRequest",
    "message": "Bad request",
}

SERVER_ERROR_500 = {
    "http_code": 500,
    "code": "serverError",
    "message": "Server error",
}

NOT_FOUND_404 = {
    "http_code": 404,
    "code": "notFound",
    "message": "data not found",
}

FORBIDDEN_403 = {
    "http_code": 403,
    "code": "notAuthorized",
    "message": "You are not authorised to execute this.",
}

UNAUTHORIZED_401 = {
    "http_code": 401,
    "code": "notAuthorized",
    "message": "Invalid authentication.",
}

SUCCESS_200 = {
    "http_code": 200,
    "code": "success",
}

SUCCESS_201 = {
    "http_code": 201,
    "code": "success",
}

SUCCESS_204 = {
    "http_code": 204,
    "code": "success",
}


def response_with(response, value=None, error=None, pagination=None) -> Response:
    result = {}

    if value is not None:
        result.update(value)

    if response.get("message") is not None:
        result["message"] = response["message"]

    result["code"] = response["code"]

    if error is not None:
        result["errors"] = error

    if pagination is not None:
        result["pagination"] = pagination

    return Response(result, status=response["http_code"])
