from app.tenants.settings import tenant_setting

GLOBAL_MAX_UPLOAD_MB = 20


def max_upload_mb(tenant_id):
    return tenant_setting(tenant_id, "max_upload_mb", GLOBAL_MAX_UPLOAD_MB)
