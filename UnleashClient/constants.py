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
FEATURES_URL = "/client/features/"
METRICS_URL = "/client/metrics"


FEATURE_TOGGLES_BASE_URL = "http://128.199.29.137:4242/api"
FEATURE_TOGGLES_APP_NAME = "feature-toggles-poc"
FEATURE_TOGGLES_INSTANCE_ID = "haptik-development-dev-parvez-vm-1"
FEATURE_TOGGLES_ENABLED = False
FEATURE_TOGGLES_CACHE_KEY = "/client/features"
FEATURE_TOGGLES_API_RESPONSE = {
    "haptik.development.enable_smart_skills": {
        "domain_names": ["test_pvz_superman", "priyanshisupermandefault"],
        "business_via_names": ["testpvzsupermanchannel", "priyanshisupermandefaultchannel"],
        "partner_names": ["Platform Demo"]
    },
    "prestaging.staging.enable_smart_skills": {
        "domain_names": ["test_pvz_superman", "priyanshisupermandefault"],
        "business_via_names": ["testpvzsupermanchannel", "priyanshisupermandefaultchannel"],
        "partner_names": ["Platform Demo"]
    },
    "haptik.staging.enable_smart_skills": {
        "domain_names": ["test_pvz_superman", "priyanshisupermandefault"],
        "business_via_names": ["testpvzsupermanchannel", "priyanshisupermandefaultchannel"],
        "partner_names": ["Platform Demo"]
    },
    "haptik.production.enable_smart_skills": {
        "domain_names": ["test_pvz_superman", "priyanshisupermandefault"],
        "business_via_names": ["testpvzsupermanchannel", "priyanshisupermandefaultchannel"],
        "partner_names": ["Platform Demo"]
    }
}

