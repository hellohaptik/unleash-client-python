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
    feature_provisioning = get_feature_toggles(
        url, app_name, instance_id,
        custom_headers, custom_options
    )

    if feature_provisioning:
        features = feature_provisioning.get('features', [])
        if not features:
            LOGGER.warning("Features are empty")
        cache.set(FEATURES_URL, pickle.dumps(features))
    else:
        LOGGER.warning("Unable to get feature flag toggles, using cached provisioning.")

    load_features(cache, features, strategy_mapping)
