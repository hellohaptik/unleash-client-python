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

FEATURE_TOGGLES_ENABLED = True

FeatureToggles.initialize(url="http://128.199.29.137:4242/api", app_name="feature-toggles-poc",
cas_name='haptik',
environment='development',
instance_id="haptik-development-dev-parvez-vm-1", custom_strategies=my_custom_strategies, redis_host="localhost", redis_port="6379",redis_db="8")


        fl_args = {
            "url": "http://128.199.29.137:4242/api",
            "app_name": "feature-toggles-poc",
            "instance_id": "haptik-development-dev-parvez-vm-1",
            "custom_headers": {},
            "custom_options": {},
            "cache": cache,
            "features": {},
            "strategy_mapping": strategy_mapping
        }