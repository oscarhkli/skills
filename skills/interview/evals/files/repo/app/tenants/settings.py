import yaml

_OVERRIDES = yaml.safe_load(open("config/tenants.yaml")) or {}


def tenant_setting(tenant_id, key, default):
    return _OVERRIDES.get(tenant_id, {}).get(key, default)
