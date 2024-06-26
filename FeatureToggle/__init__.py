# Python Imports

from redis.exceptions import LockError, BusyLoadingError, ConnectionError, RedisError
import pickle
from typing import Dict, Any, Optional

# Unleash Imports
from UnleashClient import constants as consts
from UnleashClient import UnleashClient
from UnleashClient.utils import LOGGER
from FeatureToggle.utils import timed_lru_cache
from FeatureToggle.redis_utils import RedisConnector


def split_and_strip(parameters: str):
    return [
        x.strip() for x in parameters.split(',')
    ]


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
    __sentinel_enabled = False
    __sentinels = None
    __sentinel_service_name = None
    __redis_auth_enabled = False
    __redis_password = None

    @staticmethod
    def initialize(url: str,
                   app_name: str,
                   instance_id: str,
                   cas_name: str,
                   environment: str,
                   redis_host: str,
                   redis_port: int,
                   redis_db: int,
                   enable_toggle_service: bool = True,
                   sentinel_enabled: bool = False,
                   sentinels: Optional[list] = None,
                   sentinel_service_name: Optional[str] = None,
                   redis_auth_enabled: bool = False,
                   redis_password: Optional[str] = None
                   ) -> None:
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
            FeatureToggles.__sentinel_enabled = sentinel_enabled
            FeatureToggles.__sentinels = sentinels
            FeatureToggles.__sentinel_service_name = sentinel_service_name
            FeatureToggles.__redis_auth_enabled = redis_auth_enabled
            FeatureToggles.__redis_password = redis_password
            FeatureToggles.__cache = FeatureToggles.__get_cache()
            LOGGER.info(f'Initializing Feature toggles')
        else:
            raise Exception("Client has been already initialized")

    @staticmethod
    def __get_cache():
        """
        Create redis connection
        """
        if FeatureToggles.__cache is None:
            if FeatureToggles.__sentinel_enabled:
                FeatureToggles.__cache = RedisConnector.get_sentinel_connection(
                    FeatureToggles.__sentinels, FeatureToggles.__sentinel_service_name, FeatureToggles.__redis_db,
                    FeatureToggles.__redis_auth_enabled, FeatureToggles.__redis_password
                )
            else:
                FeatureToggles.__cache = RedisConnector.get_non_sentinel_connection(
                    FeatureToggles.__redis_host, FeatureToggles.__redis_port, FeatureToggles.__redis_db,
                    FeatureToggles.__redis_auth_enabled, FeatureToggles.__redis_password
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
        except (LockError, BusyLoadingError, ConnectionError, RedisError) as redis_err:
            error_msg = f'Redis Exception occurred while updating the redis cache: {str(redis_err)}'
            LOGGER.info(error_msg)
            raise Exception(error_msg)
        except Exception as err:
            error_msg = f'Unknown Exception occurred while updating the redis cache: {str(err)}'
            LOGGER.info(error_msg)
            raise Exception(error_msg)
        LOGGER.info(f'[Feature Toggles] Cache Updated')

    @staticmethod
    def __get_unleash_client():
        """
        Initialize the client if client is None Else Return the established client
        """
        if FeatureToggles.__enable_toggle_service:
            FeatureToggles.__client = UnleashClient(
                url=FeatureToggles.__url,
                app_name=FeatureToggles.__app_name,
                instance_id=FeatureToggles.__instance_id,
                cas_name=FeatureToggles.__cas_name,
                environment=FeatureToggles.__environment,
                redis_host=FeatureToggles.__redis_host,
                redis_port=FeatureToggles.__redis_port,
                redis_db=FeatureToggles.__redis_db,
                sentinel_enabled=FeatureToggles.__sentinel_enabled,
                sentinels=FeatureToggles.__sentinels,
                sentinel_service_name= FeatureToggles.__sentinel_service_name,
                redis_auth_enabled=FeatureToggles.__redis_auth_enabled,
                redis_password=FeatureToggles.__redis_password
            )
            FeatureToggles.__client.initialize_client()

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
        feature_toggles = FeatureToggles.fetch_feature_toggles()
        LOGGER.info(f"Enable_for_domain_FT_cache_info: "
                    f"{FeatureToggles.fetch_feature_toggles.__wrapped__.cache_info()}")
        return domain_name in feature_toggles.get(feature_name, {}).get('domain_names', [])

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
        feature_toggles = FeatureToggles.fetch_feature_toggles()
        LOGGER.info(f"Enable_for_partner_FT_cache_info: "
                    f"{FeatureToggles.fetch_feature_toggles.__wrapped__.cache_info()}")
        return partner_name in feature_toggles.get(feature_name, {}).get('partner_names', [])

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
        feature_toggles = FeatureToggles.fetch_feature_toggles()
        LOGGER.info(f"Enable_for_business_FT_cache_info: "
                    f"{FeatureToggles.fetch_feature_toggles.__wrapped__.cache_info()}")
        return business_via_name in feature_toggles.get(feature_name, {}).get('business_via_names', [])

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
        feature_toggles = FeatureToggles.fetch_feature_toggles()
        LOGGER.info(f"Enable_for_expert_FT_cache_info: "
                    f"{FeatureToggles.fetch_feature_toggles.__wrapped__.cache_info()}")
        return expert_email in feature_toggles.get(feature_name, {}).get('expert_emails', [])

    @staticmethod
    def is_enabled_for_team(feature_name: str,
                            team_id: Optional[int] = None):
        """
        Util method to check whether given feature is enabled or not
        Args:
            feature_name(str): feature name
            team_id(Optional[str]): list of team IDs
        Returns:
            (bool): True if feature is enabled else False
        """
        feature_toggles = FeatureToggles.fetch_feature_toggles()
        LOGGER.info(f"Enable_for_team_FT_cache_info: "
                    f"{FeatureToggles.fetch_feature_toggles.__wrapped__.cache_info()}")
        return team_id in feature_toggles.get(feature_name, {}).get('team_ids', [])

    @staticmethod
    @timed_lru_cache(seconds=(60*60), maxsize=2048)
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
        response = {}
        LOGGER.info(f'Loading Feature Toggles from Redis')
        LOGGER.info(f"Fetch_feature_toggles_cache_info:"
                    f"{FeatureToggles.fetch_feature_toggles.__wrapped__.cache_info()}")
        if FeatureToggles.__cache is None:
            LOGGER.error('To update cache Feature Toggles class needs to be initialised')
            return response

        try:
            feature_toggles = pickle.loads(
                FeatureToggles.__cache.get(consts.FEATURES_URL)
            )
            """
            Sample output of feature_toggles
            [
                {
                "name": "devdanish.development.redis_auth", 
                "strategies": [
                                    {
                                        "name": "EnableForPartners",
                                        "parameters": {
                                                        "partner_names": "client1, client2"
                                        }
                                    }
                                ]
                }
            ]
            """
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
                    team_ids = []

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
                                partner_names = split_and_strip(parameters.get('partner_names', ''))
                            elif strategy_name == 'EnableForBusinesses':
                                business_via_names = split_and_strip(parameters.get('business_via_names', ''))
                            elif strategy_name == 'EnableForDomains':
                                domain_names = split_and_strip(parameters.get('domain_names', ''))
                            elif strategy_name == 'EnableForExperts':
                                expert_emails = split_and_strip(parameters.get('expert_emails', ''))
                            elif strategy_name == 'EnableForTeams':
                                team_ids = split_and_strip(parameters.get('team_ids', ''))

                                # Keep updating this list for new strategies which gets added

                        # Assign the strategies data to feature name
                        response[full_feature_name]['partner_names'] = partner_names
                        response[full_feature_name]['business_via_names'] = business_via_names
                        response[full_feature_name]['domain_names'] = domain_names
                        response[full_feature_name]['expert_emails'] = expert_emails
                        response[full_feature_name]['team_ids'] = team_ids
        except Exception as err:
            # Handle this exception from where this util gets called
            LOGGER.error(f'An error occurred while parsing the response: {str(err)}')
        return response
