# unleash-client-python

This is the Python client for [Unleash](https://github.com/unleash/unleash).  It implements [Client Specifications 1.0](https://github.com/Unleash/unleash/blob/master/docs/client-specification.md) and checks compliance based on spec in [unleash/client-specifications](https://github.com/Unleash/client-specification).

## Params Required to initialise the FeatureToggles
```
url -> Unleash Service Client URL

app_name -> Unleash server URL

environment -> Get from ENV variable

cas_name -> Get from ENV variable

redis_host -> Get from ENV variable

redis_port -> Get from ENV variable

redis_db -> Get from ENV variable

enable_feature_oggle_service -> Get from ENV variable
```

## Initialise the client in haptik_api
```
FeatureToggles.initialize(
    url,
    app_name,
    environment,
    cas_name,
    redis_host,
    redis_port,
    redis_db
    enable_feature_toggle_service)
```

## Usage in haptik Repositories
```
# To check if feature is enabled for domain
FeatureToggles.is_enabled_for_domain(<feature-name>, <domain_name>)

# Check if certainfeature is enabled for partner
FeatureToggles.is_enabled_for_partner(<feature-name>, <partner_name>)

# Check if certain feature is enabled for business
FeatureToggles.is_enabled_for_business(<feature-name>, <business_via_name>)

# Check if certain feature is enabled for an expert
FeatureToggles.is_enabled_for_expert(<feature-name>, <expert_email>)
```
