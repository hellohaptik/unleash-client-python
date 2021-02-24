from typing import Dict, Any, Optional
from UnleashClient import constants as consts
from UnleashClient import UnleashClient


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

