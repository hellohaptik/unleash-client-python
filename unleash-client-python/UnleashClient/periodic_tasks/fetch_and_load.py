import redis
import pickle
from UnleashClient.api import get_feature_toggles
from UnleashClient.loader import load_features
from UnleashClient.constants import FEATURES_URL
from UnleashClient.utils import LOGGER


def fetch_and_load_features(url: str,
                            app_name: str,
                            instance_id: str,
                            custom_headers: dict,
                            custom_options: dict,
                            cache: redis.Redis,
                            features: dict,
                            strategy_mapping: dict) -> None:
        # Sample data we're writing into cache
        # {
        #   "features": [{
        #     "name": "haptik.development.enable_smart_skills",
        #     "description": "Feature to enable smart skills on dev servers",
        #     "type": "release",
        #     "project": "default",
        #     "enabled": true,
        #     "stale": false,
        #     "strategies": [
        #         {
        #         "name": "EnableForPartners",
        #         "parameters": {
        #             "partner_names": "Platform Demo,haptik,demo,aksc"
        #         }
        #         }
        #     ],
        #     "variants": [],
        #     "createdAt": "2021-03-08T09:14:41.828Z"
        #   }]
        # }
        features = feature_provisioning.get('features', [])
        if not features:
            LOGGER.warning("Features are empty")
        cache.set(FEATURES_URL, pickle.dumps(features))
    else:
        LOGGER.warning("Unable to get feature flag toggles, using cached provisioning.")

    load_features(cache, features, strategy_mapping)
