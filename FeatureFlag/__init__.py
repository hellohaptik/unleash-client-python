class FeatureFlag:
    __instance = None
    __client = None

    def __init__(self):
        """ Virtually private constructor. """
        if FeatureFlag.__instance is None or FeatureFlag.__client is None:
            raise Exception("FeatureFlag class not initialized!")
        else:
            return FeatureFlag.__instance


    @staticmethod
    def get_unleash_client():
        """ Static access method. """
        if FeatureFlag.__instance is None or FeatureFlag.__client is None:
            raise Exception("FeatureFlag class not initialized!")
        return FeatureFlag.__client


    @staticmethod
    def init_instance(url: str, app_name: str, redis_host: str, redis_port: int, redis_db: int):
        """ Static access method. """
        if FeatureFlag.__instance is None:
            FeatureFlag.__instance = FeatureFlag()

            from UnleashClient import UnleashClient
            FeatureFlag.__client = UnleashClient(url, app_name, redis_host, redis_port, redis_db)
            FeatureFlag.__client.initialize_client()
        else:
            raise Exception("FeatureFlag class already initialized!")


    @staticmethod
    def is_enabled_by_domain_ids(feature_name: str, domain_ids: str):
        """ Static access method. """

        context = {'domainIds': domain_ids}
        variant = FeatureFlag.get_unleash_client().get_variant(feature_name, context)
        return variant.enabled
