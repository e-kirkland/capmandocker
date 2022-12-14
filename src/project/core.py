import configparser
import logging
from typing import Tuple, List
import json
import decimal
import uuid

from werkzeug.local import LocalProxy
from flask import current_app, jsonify
from flask.wrappers import Response
from flask.json import JSONEncoder


# logger object for all views to use
logger = LocalProxy(lambda: current_app.logger)
core_logger = logging.getLogger("core")


class Mixin:
    """Utility Base Class for SQLAlchemy Models.

    Adds `to_dict()` to easily serialize objects to dictionaries.
    """

    def to_dict(self) -> dict:
        d_out = dict((key, val) for key, val in self.__dict__.items())
        d_out.pop("_sa_instance_state", None)
        d_out["_id"] = d_out.pop("id", None)  # rename id key to interface with response
        return d_out


class JsonEncoder(JSONEncoder):
    """Custom Json Encoder for responses.

    Handles decimals and uuids gracefully, passes all else to standard encoder
    """

    def default(self, obj):
        # Encode decimal
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        # Encode uuid
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return JSONEncoder.default(self, obj)


def create_response(
    data: dict = None, status: int = 200, message: str = ""
) -> Tuple[Response, int]:
    """Wraps response in a consistent format throughout the API.

    Format inspired by https://medium.com/@shazow/how-i-design-json-api-responses-71900f00f2db
    Modifications included:
    - make success a boolean since there's only 2 values
    - make message a single string since we will only use one message per response
    IMPORTANT: data must be a dictionary where:
    - the key is the name of the type of data
    - the value is the data itself
    :param data <str> optional data
    :param status <int> optional status code, defaults to 200
    :param message <str> optional message
    :returns tuple of Flask Response and int
    """
    if type(data) is not dict and data is not None:
        raise TypeError("Data should be a dictionary ????")

    current_app.json_encoder = JsonEncoder
    response = {"success": 200 <= status < 300, "message": message, "result": data}
    return jsonify(response), status


def serialize_list(items: List) -> List:
    """Serializes a list of SQLAlchemy Objects, exposing their attributes.

    :param items - List of Objects that inherit from Mixin
    :returns List of dictionaries
    """
    if not items or items is None:
        return []
    return [x.to_dict() for x in items]


def bad_request_error_handler(error: Exception) -> Tuple[Response, int]:
    return create_response(message=str(error), status=400)


def unauthorized_request_error_handler(error: Exception) -> Tuple[Response, int]:
    return create_response(message=str(error), status=401)


# add specific Exception handlers before this, if needed
# More info at http://flask.pocoo.org/docs/1.0/patterns/apierrors/
def all_exception_handler(error: Exception) -> Tuple[Response, int]:
    """Catches and handles all exceptions, add more specific error Handlers.
    :param Exception
    :returns Tuple of a Flask Response and int
    """
    return create_response(message=str(error), status=500)
