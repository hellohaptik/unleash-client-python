import logging
import mmh3  # pylint: disable=import-error
from requests import Response
from datetime import datetime, timedelta
from functools import lru_cache, wraps

LOGGER = logging.getLogger(__name__)


def normalized_hash(identifier: str,
                    activation_group: str,
                    normalizer: int = 100) -> int:
    return mmh3.hash("{}:{}".format(activation_group, identifier), signed=False) % normalizer + 1


def get_identifier(context_key_name: str, context: dict) -> str:
    if context_key_name in context.keys():
        value = context[context_key_name]
    elif 'properties' in context.keys() and context_key_name in context['properties'].keys():
        value = context['properties'][context_key_name]
    else:
        value = None

    return value


def log_resp_info(resp: Response) -> None:
    LOGGER.debug("HTTP status code: %s", resp.status_code)
    LOGGER.debug("HTTP headers: %s", resp.headers)
    LOGGER.debug("HTTP content: %s", resp.text)


def timed_lru_cache(seconds: int, maxsize: int = 128):
    LOGGER.info(f'timed_lru_cache was called')
    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = timedelta(seconds=seconds)
        func.expiration = datetime.utcnow() + func.lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if datetime.utcnow() >= func.expiration:
                func.cache_clear()
                func.expiration = datetime.utcnow() + func.lifetime
            return func(*args, **kwargs)

        return wrapped_func

    return wrapper_cache