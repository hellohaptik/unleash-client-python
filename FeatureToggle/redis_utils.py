from typing import Optional

import redis
from redis.sentinel import Sentinel


class RedisConnector:
    """
        Utility Redis connector class to help with generating Redis sentinel and non-sentinel connection
    """
    @staticmethod
    def get_sentinel_connection(sentinels: list, sentinel_service_name: str, redis_db: int,
                                redis_auth_enabled: Optional[bool] = False, redis_password: Optional[str] = None):
        """
            Generates the Redis sentinel connection
        :param sentinels:
        :param sentinel_service_name:
        :param redis_auth_enabled:
        :param redis_password:
        :param redis_db:
        :return: Redis<SentinelConnectionPool<service=service-name>
        """
        if not all([sentinels, sentinel_service_name]):
            raise ValueError(
                "[get_sentinel_connection] Mandatory args for Redis Sentinel are missing."
                "Required Args: (sentinels, sentinel_service_name)"
            )
        if redis_auth_enabled and not redis_password:
            raise ValueError("[get_sentinel_connection] Redis Auth enabled but Redis Password not provided.")

        if redis_auth_enabled and redis_password:
            sentinel = Sentinel(sentinels, sentinel_kwargs={"password": redis_password})
            sentinel_connection_pool = sentinel.master_for(sentinel_service_name, password=redis_password, db=redis_db)
        else:
            sentinel = Sentinel(sentinels)
            sentinel_connection_pool = sentinel.master_for(sentinel_service_name, db=redis_db)
        return sentinel_connection_pool

    @staticmethod
    def get_non_sentinel_connection(redis_host: str, redis_port: int, redis_db: int,
                                    redis_auth_enabled: Optional[bool] = False,
                                    redis_password: Optional[str] = None):
        """
             Generates the Redis non-sentinel connection
        :param redis_host:
        :param redis_port:
        :param redis_db:
        :param redis_auth_enabled:
        :param redis_password:
        :return: Redis<ConnectionPool<Connection<host=,port=,db=>>>
        """
        if redis_auth_enabled and not redis_password:
            raise ValueError("[get_non_sentinel_connection] Redis Auth enabled but Redis Password not provided.")

        if redis_auth_enabled and redis_password:
            non_sentinel_connection_pool = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password
            )
        else:
            non_sentinel_connection_pool = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db
            )
        return non_sentinel_connection_pool
