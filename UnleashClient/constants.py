# Library
SDK_NAME = "unleash-client-python"
SDK_VERSION = "3.5.0"
REQUEST_TIMEOUT = 30
METRIC_LAST_SENT_TIME = "mlst"

# =Unleash=
APPLICATION_HEADERS = {"Content-Type": "application/json"}
DISABLED_VARIATION = {
        'name': 'disabled',
        'enabled': False
}

# Paths
REGISTER_URL = "/client/register"
FEATURES_URL = "/client/features"
METRICS_URL = "/client/metrics"

REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
REDIS_DB = 8
