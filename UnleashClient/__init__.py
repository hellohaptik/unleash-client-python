import redis
import pickle
from datetime import datetime, timezone
from typing import Dict, Callable, Any, Optional, List
import copy
from fcache.cache import FileCache
from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from UnleashClient.api import register_client
from UnleashClient.periodic_tasks import fetch_and_load_features, aggregate_and_send_metrics
from UnleashClient.strategies import ApplicationHostname, Default, GradualRolloutRandom, \
    GradualRolloutSessionId, GradualRolloutUserId, UserWithId, RemoteAddress, FlexibleRollout, EnableForDomains
from UnleashClient import constants as consts
from .utils import LOGGER
from .deprecation_warnings import strategy_v2xx_deprecation_check, default_value_warning


class FeatureTogglesFromConst:
    def __init__(self):
        self.feature_toggles_dict = {
            "haptik.development.enable_smart_skills": {
                "domain_names": ["test_pvz_superman", "priyanshisupermandefault"],
                "business_via_names": ["testpvzsupermanchannel", "priyanshisupermandefaultchannel"],
                "partner_names": ["Platform Demo"]
            },
            "prestaging.staging.enable_smart_skills": {
                "domain_names": ["test_pvz_superman", "priyanshisupermandefault"],
                "business_via_names": ["testpvzsupermanchannel", "priyanshisupermandefaultchannel"],
                "partner_names": ["Platform Demo"]
            },
            "haptik.staging.enable_smart_skills": {
                "domain_names": ["test_pvz_superman", "priyanshisupermandefault"],
                "business_via_names": ["testpvzsupermanchannel", "priyanshisupermandefaultchannel"],
                "partner_names": ["Platform Demo"]
            },
            "haptik.production.enable_smart_skills": {
                "domain_names": ["test_pvz_superman", "priyanshisupermandefault"],
                "business_via_names": ["testpvzsupermanchannel", "priyanshisupermandefaultchannel"],
                "partner_names": ["Platform Demo"]
            }
        }

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

        if not is_feature_enabled:  # If Feature is not enabled then return is_feature_enabled Value
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
    __custom_strategies = {}
    __redis_host = None
    __redis_port = None
    __redis_db = None
    __is_unleash_available = False

    def __init__(self):
        """Initialize a class"""
        if FeatureToggles.__client is None:
            print(
                "FeatureFlag class not initialized!, Initializing the Unleash Client"
            )
        else:
            return FeatureToggles.__client

    @staticmethod
    def get_unleash_client():
        """ Static access method. """
        if FeatureToggles.client is None:
            FeatureToggles.client = UnleashClient(
                FeatureToggles.__url,                                      FeatureToggles.__app_name,
                FeatureToggles.__instance_id,
                FeatureToggles.__redis_host,
                FeatureToggles.__redis_port,
                FeatureToggles.__redis_db,
                FeatureToggles.__custom_strategies
            )
            FeatureToggles.__client.initialize_client()

        return FeatureToggles.__client

    @staticmethod
    def initialize(url: str,
                   app_name: str,
                   instance_id: str,
                   redis_host: str,
                   redis_port: str,
                   redis_db: str,
                   custom_strategies: Optional[Dict] = {},):
        """ Static access method. """
        if __is_unleash_available:
            FeatureToggles.__url = url
            FeatureToggles.__app_name = app_name
            FeatureToggles.__redis_host = redis_host
            FeatureToggles.__redis_port = redis_port
            FeatureToggles.__redis_db = redis_db
            FeatureToggles.__instance_id = instance_id
        else:
            FeatureToggles.__client = FeatureTogglesFromConst()


# pylint: disable=dangerous-default-value
class UnleashClient():
    """
    Client implementation.

    """
    def __init__(self,
                 url: str,
                 app_name: str,
                 environment: str = "default",
                 instance_id: str = "unleash-client-python",
                 refresh_interval: int = 15,
                 metrics_interval: int = 60,
                 disable_metrics: bool = False,
                 disable_registration: bool = False,
                 custom_headers: dict = {},
                 custom_options: dict = {},
                 custom_strategies: dict = {},
                 cache_directory: str = None,
                 redis_host: str,
                 redis_port: str,
                 redis_db: str) -> None:
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
        self.unleash_environment = environment
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
        self.cache =  redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db
        )
        self.features = {}  # type: Dict
        #self.scheduler = BackgroundScheduler()
        self.fl_job = None  # type: Job
        self.metric_job = None  # type: Job
        #self.cache.set(
        #    consts.METRIC_LAST_SENT_TIME,
        #    pickle.dumps(datetime.now(timezone.utc))
        #)

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
        #fl_args = {
        #    "url": self.unleash_url,
        #    "app_name": self.unleash_app_name,
        #    "instance_id": self.unleash_instance_id,
        #    "custom_headers": self.unleash_custom_headers,
        #    "custom_options": self.unleash_custom_options,
        #    "cache": self.cache,
        #    "features": self.features,
        #    "strategy_mapping": self.strategy_mapping
        #}
#
        #metrics_args = {
        #    "url": self.unleash_url,
        #    "app_name": self.unleash_app_name,
        #    "instance_id": self.unleash_instance_id,
        #    "custom_headers": self.unleash_custom_headers,
        #    "custom_options": self.unleash_custom_options,
        #    "features": self.features,
        #    "ondisk_cache": self.cache
        #}
#
        # Register app
        if not self.unleash_disable_registration:
            register_client(
                self.unleash_url, self.unleash_app_name, self.unleash_instance_id,
                self.unleash_metrics_interval, self.unleash_custom_headers,
                self.unleash_custom_options, self.strategy_mapping
            )

        #fetch_and_load_features(**fl_args)

        # Start periodic jobs
        #self.scheduler.start()
        #self.fl_job = self.scheduler.add_job(
        #    fetch_and_load_features,
        #    trigger=IntervalTrigger(seconds=int#(self.unleash_refresh_interval)),
        #    kwargs=fl_args
        #)

        # if not self.unleash_disable_metrics:
        #     self.metric_job = self.scheduler.add_job(
        #         aggregate_and_send_metrics,
        #         trigger=IntervalTrigger(seconds=int#( self.unleash_metrics_interval)),
        #         kwargs=metrics_args
        #     )

        self.is_initialized = True

    def destroy(self):
        """
        Gracefully shuts down the Unleash client by stopping jobs, stopping the scheduler, and deleting the cache.

        You shouldn't need this too much!

        :return:
        """
        self.fl_job.remove()
        if self.metric_job:
            self.metric_job.remove()
        self.scheduler.shutdown()
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

    def is_enabled_for_domain(self, feature_name: str,
                              domain_name: Optional[str] = ''):
        """ Static access method. """
        context = {}
        if domain_name:
            context['domain_names'] = domain_name

        return self.is_enabled(feature_name, context)

    def is_enabled_for_business(self, feature_name: str,
                                business_via_name: Optional[str] = ''):
        context = {}
        if business_via_name:
            context['business_via_names'] = business_via_name

        return self.is_enabled(feature_name, context)

    def is_enabled_for_partner(self, feature_name: str,
                               partner_name: Optional[str]=''):
        if partner_name:
            context['partner_names'] = partner_name

        return self.is_enabled(feature_name, context)

    def is_enabled_for_expert(self, feature_name: str,
                              expert_email: Optional[str] = ''):
        context = {}
        if expert_email:
            context['expert_emails'] = expert_email

        return self.is_enabled(feature_name, context)
