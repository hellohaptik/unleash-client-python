class FeatureFlag:
    __instance = None
    __client = None

    __url = None
    __app_name = None
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
    def __get_unleash_client():
        """ Static access method. """
        if FeatureFlag.__instance is None:
            FeatureFlag.__instance = FeatureFlag()

            from UnleashClient import UnleashClient
            FeatureFlag.__client = UnleashClient(FeatureFlag.__url, FeatureFlag.__app_name, FeatureFlag.__redis_host,
                                                 FeatureFlag.__redis_port, FeatureFlag.__redis_db)
            FeatureFlag.__client.initialize_client()

        return FeatureFlag.__client


    @staticmethod
    def set_init_params(url: str, app_name: str, redis_host: str, redis_port: int, redis_db: int):
        """ Static access method. """
        FeatureFlag.__url = url
        FeatureFlag.__app_name = app_name
        FeatureFlag.__redis_host = redis_host
        FeatureFlag.__redis_port = redis_port
        FeatureFlag.__redis_db = redis_db


    @staticmethod
    def is_enabled_by_domain_ids(feature_name: str, domain_ids: str):
        """ Static access method. """

        context = {'domainIds': domain_ids}
        variant = FeatureFlag.__get_unleash_client().get_variant(feature_name, context)
        return variant.enabled
