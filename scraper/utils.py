import hashlib
import json
import logging
import re
import string
import time


def parse_numbers(text):
    return re.findall(r'\d+', text)


def is_formattable(text):
    return any(
        [
            tup[1] for tup in string.Formatter().parse(text)
            if tup[1] is not None
        ]
    )


def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start + len(needle))
        n -= 1
    return start


def get_attribute_by_path(dictionary, attribute_path, default=None):
    current_attr = dictionary
    for key in list(filter(lambda x: x, attribute_path.split('.'))):
        current_attr = current_attr.get(key)
        if current_attr is None:
            return default
    else:
        return current_attr


def set_hash(obj, keys=None):
    keys = keys or obj.keys()
    hash = hashlib.md5()
    content = [obj.get(key) for key in keys]
    encoded = json.dumps(content, sort_keys=True).encode()
    hash.update(encoded)
    obj['hash'] = hash.hexdigest()


def log_time(log_args=True, log_kwargs=True, log_response=False,
             fake_args=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            res = func(*args, **kwargs)
            taken_time = time.time() - start
            logging.info(
                "%s take %s seconds to finish." % (func.__name__, taken_time)
            )
            if fake_args and len(args) > 0 and isinstance(args[0], object):
                _fake_args = [getattr(args[0], attr) for attr in fake_args]
                logging.info(
                    "%s, given fake args= %s" % (func.__name__, _fake_args)
                )
            if log_args:
                _args = args
                if isinstance(log_args, list) and all((
                        lambda x: isinstance(x, int) and x <= len(log_args) - 1,
                        log_args
                )):
                    _args = [args[i] for i in log_args]
                logging.info("%s, given args= %s" % (func.__name__, _args))
            if log_kwargs:
                _kwargs = kwargs.copy()
                if isinstance(log_kwargs, list):
                    _kwargs = [kwargs.get(i) for i in log_kwargs]
                logging.info("%s, given kwargs= %s" % (func.__name__, _kwargs))
            if log_response:
                logging.info("%s, response= %s" % (func.__name__, res))
            return res

        return wrapper

    return decorator
