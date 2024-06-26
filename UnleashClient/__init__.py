from typing import Dict, Callable, Optional

from UnleashClient.periodic_tasks import fetch_and_load_features
from UnleashClient.strategies import (
    ApplicationHostname, Default, GradualRolloutRandom, GradualRolloutSessionId, GradualRolloutUserId, UserWithId,
    RemoteAddress, FlexibleRollout, EnableForDomains, EnableForBusinesses, EnableForPartners, EnableForExperts
)
from UnleashClient import constants as consts
from UnleashClient.strategies.EnableForTeamStrategy import EnableForTeams
from UnleashClient.utils import LOGGER
from UnleashClient.loader import load_features
from UnleashClient.deprecation_warnings import strategy_v2xx_deprecation_check, default_value_warning


# pylint: disable=dangerous-default-value
class UnleashClient:
    """
    Client implementation.
    """
    def __init__(self,
                 url: str,
                 app_name: str,
                 environment: str,
                 cas_name: str,
                 redis_host: str,
                 redis_port: int,
                 redis_db: int,
                 instance_id: str = "unleash-client-python",
                 refresh_interval: int = 15,
                 metrics_interval: int = 60,
                 disable_metrics: bool = False,
                 disable_registration: bool = False,
                 custom_headers: dict = {},
                 custom_options: dict = {},
                 custom_strategies: dict = {},
                 cache_directory: str = None,
                 sentinel_enabled: bool = False,
                 sentinels: Optional[list] = None,
                 sentinel_service_name: Optional[str] = None,
                 redis_auth_enabled: bool = False,
                 redis_password: Optional[str] = None
                 ) -> None:
        """
        A client for the Unleash feature toggle system.
        :param url: URL of the unleash server, required.
        :param app_name: Name of the application using the unleash client, required.
        :param environment: Name of the environment using the unleash client, optinal & defaults to "default".
        :param instance_id: Unique identifier for unleash client instance, optional & defaults to "unleash-client-python"
        :param refresh_interval: Provisioning refresh interval in ms, optional & defaults to 15 seconds
        :param metrics_interval: Metrics refresh interval in ms, optional & defaults to 60 seconds
        :param disable_metrics: Disables sending metrics to unleash server, optional & defaults to false.
        :param custom_headers: Default headers to send to unleash server, optional & defaults to empty.
        :param custom_options: Default requests parameters, optional & defaults to empty.
        :param custom_strategies: Dictionary of custom strategy names : custom strategy objects
        :param cache_directory: Location of the cache directory. When unset, FCache will determine the location
        """
        # Configuration
        self.unleash_url = url.rstrip('\\')
        self.unleash_app_name = app_name
        self.unleash_environment = f'{cas_name}|{environment}'
        self.unleash_instance_id = instance_id
        self.unleash_refresh_interval = refresh_interval
        self.unleash_metrics_interval = metrics_interval
        self.unleash_disable_metrics = disable_metrics
        self.unleash_disable_registration = disable_registration
        self.unleash_custom_headers = custom_headers
        self.unleash_custom_options = custom_options
        self.unleash_static_context = {
            "appName": self.unleash_app_name,
            "environment": self.unleash_environment
        }
        from FeatureToggle.redis_utils import RedisConnector
        if sentinel_enabled:
            self.cache = RedisConnector.get_sentinel_connection(sentinels, sentinel_service_name, redis_db,
                                                                redis_auth_enabled, redis_password)
        else:
            self.cache = RedisConnector.get_non_sentinel_connection(redis_host, redis_port, redis_db,
                                                                    redis_auth_enabled, redis_password)

        self.features = {}  # type: Dict

        # Mappings
        default_strategy_mapping = {
            "applicationHostname": ApplicationHostname,
            "default": Default,
            "gradualRolloutRandom": GradualRolloutRandom,
            "gradualRolloutSessionId": GradualRolloutSessionId,
            "gradualRolloutUserId": GradualRolloutUserId,
            "remoteAddress": RemoteAddress,
            "userWithId": UserWithId,
            "flexibleRollout": FlexibleRollout,
            "EnableForDomains": EnableForDomains,
            "EnableForExperts": EnableForExperts,
            "EnableForPartners": EnableForPartners,
            "EnableForBusinesses": EnableForBusinesses,
            "EnableForTeams": EnableForTeams
        }

        if custom_strategies:
            strategy_v2xx_deprecation_check([x for x in custom_strategies.values()])  # pylint: disable=R1721

        self.strategy_mapping = {**custom_strategies, **default_strategy_mapping}

        # Client status
        self.is_initialized = False

    def initialize_client(self) -> None:
        """
        Initializes client and starts communication with central unleash server(s).
        This kicks off:
        * Client registration
        * Provisioning poll
        * Stats poll
        :return:
        """
        # Setup
        fl_args = {
            "url": self.unleash_url,
            "app_name": self.unleash_app_name,
            "instance_id": self.unleash_instance_id,
            "custom_headers": self.unleash_custom_headers,
            "custom_options": self.unleash_custom_options,
            "cache": self.cache,
            "features": self.features,
            "strategy_mapping": self.strategy_mapping
        }

        # Disabling the first API call
        # fetch_and_load_features(**fl_args)
        load_features(self.cache, self.features, self.strategy_mapping)

        self.is_initialized = True

    def destroy(self):
        """
        Gracefully shuts down the Unleash client by stopping jobs, stopping the scheduler, and deleting the cache.
        You shouldn't need this too much!
        :return:
        """
        self.cache.delete()

    @staticmethod
    def _get_fallback_value(fallback_function: Callable, feature_name: str, context: dict) -> bool:
        if fallback_function:
            fallback_value = fallback_function(feature_name, context)
        else:
            fallback_value = False

        return fallback_value

    # pylint: disable=broad-except
    def is_enabled(self,
                   feature_name: str,
                   context: dict = {},
                   default_value: bool = False,
                   fallback_function: Callable = None) -> bool:
        """
        Checks if a feature toggle is enabled.
        Notes:
        * If client hasn't been initialized yet or an error occurs, flat will default to false.
        :param feature_name: Name of the feature
        :param context: Dictionary with context (e.g. IPs, email) for feature toggle.
        :param default_value: Allows override of default value. (DEPRECIATED, used fallback_function instead!)
        :param fallback_function: Allows users to provide a custom function to set default value.
        :return: True/False
        """
        context.update(self.unleash_static_context)

        if default_value:
            default_value_warning()

        if self.is_initialized:
            try:
                return self.features[feature_name].is_enabled(context, default_value)
            except Exception as excep:
                LOGGER.warning("Returning default value for feature: %s", feature_name)
                LOGGER.warning("Error checking feature flag: %s", excep)
                return self._get_fallback_value(fallback_function, feature_name, context)
        else:
            LOGGER.warning("Returning default value for feature: %s", feature_name)
            LOGGER.warning("Attempted to get feature_flag %s, but client wasn't initialized!", feature_name)
            return self._get_fallback_value(fallback_function, feature_name, context)

    # pylint: disable=broad-except
    def get_variant(self,
                    feature_name: str,
                    context: dict = {}) -> dict:
        """
        Checks if a feature toggle is enabled.  If so, return variant.
        Notes:
        * If client hasn't been initialized yet or an error occurs, flat will default to false.
        :param feature_name: Name of the feature
        :param context: Dictionary with context (e.g. IPs, email) for feature toggle.
        :return: Dict with variant and feature flag status.
        """
        context.update(self.unleash_static_context)

        if self.is_initialized:
            try:
                return self.features[feature_name].get_variant(context)
            except Exception as excep:
                LOGGER.warning("Returning default flag/variation for feature: %s", feature_name)
                LOGGER.warning("Error checking feature flag variant: %s", excep)
                return consts.DISABLED_VARIATION
        else:
            LOGGER.warning("Returning default flag/variation for feature: %s", feature_name)
            LOGGER.warning("Attempted to get feature flag/variation %s, but client wasn't initialized!", feature_name)
            return consts.DISABLED_VARIATION
