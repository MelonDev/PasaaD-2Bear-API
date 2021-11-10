import uuid
from datetime import datetime
import datetime as dt
from uuid import UUID

import pytz
from flask import abort, json


def verify_return(data=None, code=None, message=None, content=None):
    if data is not None:
        if code is not None:
            return data, code
        return data
    if code is not None:
        if message is not None:
            return {"message": message}, code
        if content is not None:
            return {"content": content}, code
        return abort(code)
    return abort(500)


def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError  # evil ValueError that doesn't tell you what the wrong value was


def current_datetime_with_timezone():
    d = dt.datetime.now()
    dtz = add_timezone(d)
    return dtz


def convert_to_utc(datetime):
    utc = pytz.UTC
    return datetime.replace(tzinfo=utc)


def add_timezone(datetime):
    tz = pytz.timezone('Asia/Bangkok')
    dt = datetime.astimezone(tz)
    return dt


def convert_datetime_to_string(date_raw):
    date_format = "%a %b %d %H:%M:%S %z %Y"
    tz = pytz.timezone('Asia/Bangkok')
    dt = date_raw.astimezone(tz)
    result = dt.strftime(date_format)
    return result


def convert_datetime_to_string_for_export(date_raw):
    date_format = "%Y-%m-%d %H:%M:%S.%f%z"
    result = date_raw.strftime(date_format)
    return result


def convert_datetime(date_str):
    date_format = "%a %b %d %H:%M:%S %z %Y"
    dt = datetime.strptime(date_str, date_format)
    tz = pytz.timezone('Asia/Bangkok')
    dt = dt.astimezone(tz)
    return dt


def convert_string_to_datetime(date_str):
    date_object = datetime.strptime(date_str, '%d-%m-%Y')
    tz = pytz.timezone('Asia/Bangkok')
    date_object = date_object.astimezone(tz)
    return date_object


def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def generate_uuid():
    return uuid.uuid4()


def list_to_set_original(data):
    return set(data) if data is not None else None


def list_to_set(data):
    return str(set(data)).replace("'", "") if data is not None else None


def verify_parameters(value, is_empty: bool = None):
    if value is None:
        return False
    if type(value) is int:
        return True
    if type(value) is str:
        if is_empty is None:
            return True
        if is_empty and len(value) >= 0:
            return True
        if not is_empty and len(value) > 0:
            return True

    return False
