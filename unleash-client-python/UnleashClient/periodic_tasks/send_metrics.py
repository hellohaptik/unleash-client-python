import redis
import pickle
from collections import ChainMap
from datetime import datetime, timezone
from UnleashClient.api import send_metrics
from UnleashClient.constants import METRIC_LAST_SENT_TIME


def aggregate_and_send_metrics(url: str,
                               app_name: str,
                               instance_id: str,
                               custom_headers: dict,
                               custom_options: dict,
                               features: dict,
                               ondisk_cache: redis.Redis
                               ) -> None:
    feature_stats_list = []

    for feature_name in features.keys():
        feature_stats = {
            features[feature_name].name: {
                "yes": features[feature_name].yes_count,
                "no": features[feature_name].no_count
            }
        }

        features[feature_name].reset_stats()
        feature_stats_list.append(feature_stats)

    metric_last_seen_time = pickle.loads(
        ondisk_cache.get(
            METRIC_LAST_SENT_TIME
        )
    )

    metrics_request = {
        "appName": app_name,
        "instanceId": instance_id,
        "bucket": {
            "start": metric_last_seen_time.isoformat(),
            "stop": datetime.now(timezone.utc).isoformat(),
            "toggles": dict(ChainMap(*feature_stats_list))
        }
    }

    send_metrics(url, metrics_request, custom_headers, custom_options)
    ondisk_cache.set(
        METRIC_LAST_SENT_TIME,
        pickle.dumps(datetime.now(timezone.utc))
    )
