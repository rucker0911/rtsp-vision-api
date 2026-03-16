from flask import jsonify, make_response
from json import JSONEncoder
from flask.json.provider import JSONProvider
from datetime import datetime
from typing import Union
import json


class CustomJSONProvider(JSONProvider):
    ensure_ascii = False

    def dumps(self, obj, **kwargs):
        kwargs.setdefault("ensure_ascii", self.ensure_ascii)
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder, indent=4)

    def loads(self, s: Union[str, bytes], **kwargs):
        return json.loads(s, **kwargs)


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


INVALID_FIELD_NAME_SENT_422 = {
    "http_code": 422,
    "code": "invalidField",
    "message": "Invalid fields found"
}

INVALID_INPUT_422 = {
    "http_code": 422,
    "code": "invalidInput",
    "message": "Invalid input"
}

MISSING_PARAMETERS_422 = {
    "http_code": 422,
    "code": "missingParameter",
    "message": "Missing parameters."
}

BAD_REQUEST_400 = {
    "http_code": 400,
    "code": "badRequest",
    "message": "Bad request"
}

SERVER_ERROR_500 = {
    "http_code": 500,
    "code": "serverError",
    "message": "Server error"
}

SERVER_ERROR_404 = {
    "http_code": 404,
    "code": "notFound",
    "message": "Resource not found"
}

FORBIDDEN_403 = {
    "http_code": 403,
    "code": "notAuthorized",
    "message": "You are not authorised to execute this."
}

SERVER_ERROR_401 = {
    "http_code": 401,
    "code": "notAuthorized",
    "message": "Invalid authentication."
}

UNAUTHORIZED_401 = {
    "http_code": 401,
    "code": "notAuthorized",
    "message": "Invalid authentication."
}

NOT_FOUND_HANDLER_404 = {
    "http_code": 404,
    "code": "notFound",
    "message": "route not found"
}

NOT_FOUND_404 = {
    "http_code": 404,
    "code": "notFound",
    "message": "data not found"
}

SUCCESS_200 = {
    'http_code': 200,
    'code': 'success'
}

SUCCESS_201 = {
    'http_code': 201,
    'code': 'success'
}

SUCCESS_204 = {
    'http_code': 204,
    'code': 'success'
}

DATA_NOT_EQUALS = {
    'http_code': 200,
    'code': 'error',
}

COMMAND_TIME_OUT = {
    'http_code': 200,
    'code': 'error',
}

TIME_PLAN_IS_NULL = {
    'http_code': 200,
    'code': 'error',
}

ASSIGN_SUCCESS = {
    'http_code': 200,
    'code': 'success',
}


def response_with(response, value=None, message=None, error=None, dataTime=None, command=None, uuid=None, device_id=None, plan_id=None, fail_list=None, success_list=None, headers={}, pagination=None):
    result = {}
    if value is not None:
        result.update(value)

    if response.get('message', None) is not None:
        result.update({'message': response['message']})

    result.update({'code': response['code']})

    if error is not None:
        result.update({'errors': error})

    if pagination is not None:
        result.update({'pagination': pagination})
        
    if dataTime is not None:
        result.update({'receiveTime': dataTime})
        
    if command is not None:
        result.update({'command': command})
        
    if uuid is not None:
        result.update({'uuid': uuid})
        
    if device_id is not None:
        result.update({'deviceId': device_id})        
        
    if plan_id is not None:
        result.update({'planId': plan_id})
        
    if fail_list is not None:
        result.update({'fail': fail_list})
        
    if success_list is not None:
        result.update({'success': success_list})
    
    headers.update({'Access-Control-Allow-Origin': '*'})
    headers.update({'server': 'Flask REST API'})
    result.update({'dataTime': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')})
    res = make_response(jsonify(result), response['http_code'], headers)
    # if 'access_token' in value:
    #     res.set_cookie('Authorization', 'Bearer '+value['access_token'], max_age=3600)

    return res
