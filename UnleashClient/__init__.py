import redis

from typing import Dict, Callable, Any, Optional

from UnleashClient.api import register_client
from UnleashClient.periodic_tasks import fetch_and_load_features
from UnleashClient.strategies import (
    ApplicationHostname, Default, GradualRolloutRandom,
    GradualRolloutSessionId, GradualRolloutUserId, UserWithId,
    RemoteAddress, FlexibleRollout, EnableForDomains
)
from UnleashClient import constants as consts
from UnleashClient.utils import LOGGER
from UnleashClient.deprecation_warnings import strategy_v2xx_deprecation_check, default_value_warning


class FeatureTogglesFromConst:
    def __init__(self):
        self.feature_toggles_dict = consts.FEATURE_TOGGLES_API_RESPONSE

    def is_enabled(self, feature_name,
                   app_context: Optional[Dict] = {}) -> bool:
        """
        Check if certain feature is enabled in const
        Args:
            feature_name(str): Name of the feature
            app_context(dict): App context to check when certain feature is enabled for given entity
                eg: {
                    "partner_names": "<partner_names>"
                }
        Returns(bool): True if feature is enabled else False
        """
        is_feature_enabled = feature_name in self.feature_toggles_dict

        # If Feature is not enabled then return is_feature_enabled Value
        if not is_feature_enabled:
            return is_feature_enabled

        if not app_context:  # If there's not any app_context then return is_feature_enabled value
            return is_feature_enabled

        app_context_parameter_key = list(app_context.keys())[0]
        app_context_parameter_value = list(app_context.values())[0]

        feature_data = self.feature_toggles_dict[feature_name]
        return app_context_parameter_value in feature_data.get(app_context_parameter_key, [])

    def fetch_feature_toggles(self) -> Dict[str, Any]:
        """
        Return Feature toggles from const
        """
        return self.feature_toggles_dict

    @staticmethod
    def is_enabled_for_partner(feature_name: str,
                               partner_name: Optional[str] = ''):
        context = {}
        if partner_name:
            context['partner_names'] = partner_name

        return FeatureTogglesFromConst().is_enabled(feature_name, context)

    @staticmethod
    def is_enabled_for_expert(feature_name: str,
                              expert_email: Optional[str] = ''):
        context = {}
        if expert_email:
            context['expert_emails'] = expert_email

        return FeatureTogglesFromConst().is_enabled(feature_name, context)

    @staticmethod
    def is_enabled_for_business(feature_name: str,
                                business_via_name: Optional[str] = ''):
        context = {}
        if business_via_name:
            context['business_via_names'] = business_via_name

        return FeatureTogglesFromConst().is_enabled(feature_name, context)

    @staticmethod
    def is_enabled_for_domain(feature_name: str,
                              domain_name: Optional[str] = ''):
        context = {}
        if domain_name:
            context['domain_names'] = domain_name

        return FeatureTogglesFromConst().is_enabled(feature_name, context)


class FeatureToggles:
    __client = None
    __url = None
    __app_name = None
    __instance_id = None
    __redis_host = None
    __redis_port = None
    __redis_db = None
    __cas_name = None
    __environment = None
    __enable_toggle_service = True

    def __init__(self):
        """Initialize a class"""
        if FeatureToggles.__client is None:
            print(
                "FeatureFlag class not initialized!, Initializing the Unleash Client"
            )
        else:
            return FeatureToggles.__client

    @staticmethod
    def initialize(url: str,
                   app_name: str,
                   instance_id: str,
                   cas_name: str,
                   environment: str,
                   redis_host: str,
                   redis_port: str,
                   redis_db: str,
                   enable_toggle_service: bool = True) -> None:
        """ Static access method. """
        if FeatureToggles.__client is None:
            FeatureToggles.__url = url
            FeatureToggles.__app_name = app_name
            FeatureToggles.__instance_id = instance_id
            FeatureToggles.__cas_name = cas_name
            FeatureToggles.__environment = environment
            FeatureToggles.__redis_host = redis_host
            FeatureToggles.__redis_port = redis_port
            FeatureToggles.__redis_db = redis_db
            FeatureToggles.__enable_toggle_service = enable_toggle_service
        else:
            raise Exception("Client has been already initialized")

    @staticmethod
    def __get_unleash_client():
        """
        Initialize the client if client is None Else Return the established client
        """
        if FeatureToggles.__enable_toggle_service:
            if FeatureToggles.__client is None:
                FeatureToggles.__client = UnleashClient(
                    url=FeatureToggles.__url,
                    app_name=FeatureToggles.__app_name,
                    instance_id=FeatureToggles.__instance_id,
                    cas_name=FeatureToggles.__cas_name,
                    environment=FeatureToggles.__environment,
                    redis_host=FeatureToggles.__redis_host,
                    redis_port=FeatureToggles.__redis_port,
                    redis_db=FeatureToggles.__redis_db
                )
                FeatureToggles.__client.initialize_client()
        else:
            FeatureToggles.__client = FeatureTogglesFromConst()

        return FeatureToggles.__client

    @staticmethod
    def __get_full_feature_name(feature_name: str):
        """
        construct full feature name

        Args:
            feature_name(str): Feature Name
            eg: `enable_language_support`

        Returns:
            (str): fully constructed feature name
                eg: 'haptik.production.enable_language_support'
        """
        try:
            feature_name = (
                f'{FeatureToggles.__cas_name}.'
                f'{FeatureToggles.__environment}.'
                f'{feature_name}'
            )
            return feature_name
        except Exception as err:
            raise Exception(f'Error while forming the feature name: {str(err)}')

    @staticmethod
    def is_enabled_for_domain(feature_name: str,
                              domain_name: Optional[str] = ''):
        """
        Util method to check whether given feature is enabled or not

        Args:
            feature_name(str): Name of the feature
            domain_name(Optional[str]): Name of the domain

        Returns:
            (bool): True if Feature is enabled else False
        """
        feature_name = FeatureToggles.__get_full_feature_name(feature_name)

        context = {}
        if domain_name:
            context['domain_names'] = domain_name

        return FeatureToggles.__get_unleash_client().is_enabled(feature_name,
                                                                context)

    @staticmethod
    def is_enabled_for_partner(feature_name: str,
                               partner_name: Optional[str] = ''):
        """
        Util method to check whether given feature is enabled or not

        Args:
            feature_name(str): Name of the feature
            partner_name(Optional[str]): Name of the Partner

        Returns:
            (bool): True if Feature is enabled else False
        """
        feature_name = FeatureToggles.__get_full_feature_name(feature_name)

        context = {}
        if partner_name:
            context['partner_names'] = partner_name

        return FeatureToggles.__get_unleash_client().is_enabled(feature_name,
                                                                context)

    @staticmethod
    def is_enabled_for_business(feature_name: str,
                                business_via_name: Optional[str] = ''):
        """
        Util method to check whether given feature is enabled or not

        Args:
            feature_name(str): Name of the feature
            business_via_name(Optional[str]): Business Via Name

        Returns:
            (bool): True if Feature is enabled else False
        """
        feature_name = FeatureToggles.__get_full_feature_name(feature_name)

        context = {}
        if business_via_name:
            context['business_via_names'] = business_via_name

        return FeatureToggles.__get_unleash_client().is_enabled(feature_name,
                                                                context)

    @staticmethod
    def is_enabled_for_expert(feature_name: str,
                              expert_email: Optional[str] = ''):
        """
        Util method to check whether given feature is enabled or not

        Args:
            feature_name(str): Name of the feature
            expert_email(Optional[str]): Expert Emails

        Returns:
            (bool): True if Feature is enabled else False
        """
        feature_name = FeatureToggles.__get_full_feature_name(feature_name)

        context = {}
        if expert_email:
            context['expert_emails'] = expert_email

        return FeatureToggles.__get_unleash_client().is_enabled(feature_name,
                                                                context)


# pylint: disable=dangerous-default-value
class UnleashClient():
    """
    Client implementation.

    """
    def __init__(self,
                 url: str,
                 app_name: str,
                 environment: str,
                 cas_name: str,
                 redis_host: str,
                 redis_port: str,
                 redis_db: str,
                 instance_id: str = "unleash-client-python",
                 refresh_interval: int = 15,
                 metrics_interval: int = 60,
                 disable_metrics: bool = False,
                 disable_registration: bool = False,
                 custom_headers: dict = {},
                 custom_options: dict = {},
                 custom_strategies: dict = {},
                 cache_directory: str = None) -> None:
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

        # Class objects
        self.cache = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db
        )
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
            "EnableForDomains": EnableForDomains
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
        # Register app
        if not self.unleash_disable_registration:
            register_client(
                self.unleash_url, self.unleash_app_name, self.unleash_instance_id,
                self.unleash_metrics_interval, self.unleash_custom_headers,
                self.unleash_custom_options, self.strategy_mapping
            )

        fetch_and_load_features(**fl_args)

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
