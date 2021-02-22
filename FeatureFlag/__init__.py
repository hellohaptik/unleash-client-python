class FeatureFlag:
    __instance = None
    __client = None

    __url = None
    __app_name = None
    __environment = None
    __cas_name = None
    __redis_host = None
    __redis_port = None
    __redis_db = None

    def __init__(self):
        """ Virtually private constructor. """
        if FeatureFlag.__instance is None:
            raise Exception("FeatureFlag class not initialized!")
        else:
            return FeatureFlag.__instance

    @staticmethod
    def initialize(url: str, app_name: str, environment: str, cas_name: str,
                   redis_host: str, redis_port: int, redis_db: int):
        """ Static access method. """
        if FeatureFlag.__instance is None:
            FeatureFlag.__instance = FeatureFlag()

        FeatureFlag.__url = url
        FeatureFlag.__app_name = app_name
        FeatureFlag.__environment = environment
        FeatureFlag.__cas_name_name = cas_name

        FeatureFlag.__redis_host = redis_host
        FeatureFlag.__redis_port = redis_port
        FeatureFlag.__redis_db = redis_db

    @staticmethod
    def __get_unleash_client():
        """ Static access method. """
        if FeatureFlag.__client is None:
            from UnleashClient import UnleashClient
            FeatureFlag.__client = UnleashClient(FeatureFlag.__url, FeatureFlag.__app_name, FeatureFlag.__redis_host,
                                                 FeatureFlag.__redis_port, FeatureFlag.__redis_db)
            FeatureFlag.__client.initialize_client()

        return FeatureFlag.__client

    @staticmethod
    def __get_full_feature_name(feature_name: str):
        """ Static access method. """
        return feature_name + ':' + FeatureFlag.__environment + ':' + FeatureFlag.__cas_name

    @staticmethod
    def is_enabled_by_domain_ids(feature_name: str, domain_ids: str):
        """ Static access method. """
        context = {'domainIds': domain_ids}
        variant = FeatureFlag.__get_unleash_client().get_variant(
            FeatureFlag.__get_full_feature_name(feature_name), context)
        return variant.enabled
