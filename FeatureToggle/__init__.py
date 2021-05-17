# Python Imports
import redis
import pickle
from typing import Dict, Any, Optional

# Unleash Imports
from UnleashClient import constants as consts
from UnleashClient import UnleashClient
from UnleashClient.utils import LOGGER


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

    @staticmethod
    def fetch_feature_toggles() -> Dict[str, Any]:
        """
        Return Feature toggles from const
        """
        return consts.FEATURE_TOGGLES_API_RESPONSE

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
    __cache = None
    __enable_toggle_service = True

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
            FeatureToggles.__cache = FeatureToggles.__get_cache()
        else:
            raise Exception("Client has been already initialized")

    @staticmethod
    def __get_cache():
        """
        Create redis connection
        """
        if FeatureToggles.__cache is None:
            FeatureToggles.__cache = redis.Redis(
                host=FeatureToggles.__redis_host,
                port=FeatureToggles.__redis_port,
                db=FeatureToggles.__redis_db
            )

        return FeatureToggles.__cache

    @staticmethod
    def update_cache(data: Dict[str, Any]) -> None:
        """
        Update cache data
        Args:
            data(dict): Feature toggles Data
        Returns:
            None
        """
        if FeatureToggles.__cache is None:
            raise Exception(
                'To update cache Feature Toggles class needs to be initialised'
            )

        LOGGER.info(f'Updating the cache data: {data}')
        try:
            FeatureToggles.__cache.set(
                consts.FEATURES_URL, pickle.dumps(data)
            )
        except Exception as err:
            raise Exception(
                f'Exception occured while updating the redis cache: {str(err)}'
            )
        LOGGER.info(f'Cache Updatation is Done')

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
            (str): fully constructed feature name including cas and env name
                format => '{cas_name}.{environment}.{feature_name}'
                eg => 'haptik.production.enable_language_support'
        """
        try:
            full_feature_name = (
                f'{FeatureToggles.__cas_name}.'
                f'{FeatureToggles.__environment}.'
                f'{feature_name}'
            )
            return full_feature_name
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

    @staticmethod
    def fetch_feature_toggles():
        """
        Returns(Dict):
            Feature toggles data
            Eg: {
                "<CAS-Name>.<ENVIRONMENT>.<FeatureName>": {
                    "domain_names": [<Domain Names List>],
                    "business_via_names": [<List of Business Via Names>],
                    "partner_names": [<List Of Partner Names>]
                }
            }
        """
        # TODO: Remove the cas and environment name from the feature toggles while returning the response
        feature_toggles = pickle.loads(
            FeatureToggles.__cache.get(consts.FEATURES_URL)
        )
        response = {}
        try:
            if feature_toggles:
                for feature_toggle in feature_toggles:
                    full_feature_name = feature_toggle['name']
                    # split the feature and get compare the cas and environment name
                    feature = full_feature_name.split('.')
                    cas_name = feature[0]
                    environment = feature[1]

                    # Define empty list for empty values
                    domain_names = []
                    partner_names = []
                    business_via_names = []
                    expert_emails = []

                    if cas_name == FeatureToggles.__cas_name and environment == FeatureToggles.__environment:
                        # Strip CAS and ENV name from feature name
                        active_cas_env_name = f'{cas_name}.{environment}.'
                        full_feature_name = full_feature_name.replace(active_cas_env_name, '')
                        if full_feature_name not in response:
                            response[full_feature_name] = {}
                        strategies = feature_toggle.get('strategies', [])
                        for strategy in strategies:
                            strategy_name = strategy.get('name', '')
                            parameters = strategy.get('parameters', {})
                            if strategy_name == 'EnableForPartners':
                                partner_names = parameters.get('partner_names', '').replace(', ', ',').split(',')

                            elif strategy_name == 'EnableForBusinesses':
                                business_via_names = parameters.get('business_via_names', '').replace(', ', ',').split(',')
                            elif strategy_name == 'EnableForDomains':
                                domain_names = parameters.get('domain_names', '').replace(', ', ',').split(',')
                            elif strategy_name == 'EnableForExperts':
                                expert_emails = parameters.get('expert_emails', '').replace(', ', ',').split(',')

                                # Keep updating this list for new strategies which gets added

                        # Assign the strategies data to feature name
                        response[full_feature_name]['partner_names'] = partner_names
                        response[full_feature_name]['business_via_names'] = business_via_names
                        response[full_feature_name]['domain_names'] = domain_names
                        response[full_feature_name]['expert_emails'] = expert_emails
        except Exception as err:
            # Handle this exception from where this util gets called
            raise Exception(f'Error occured while parsing the response: {str(err)}')

        return response
