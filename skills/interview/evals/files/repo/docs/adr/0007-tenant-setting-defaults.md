# ADR 0007: Defaults for per-tenant settings

Status: Accepted (2026-05-12)

## Decision

A per-tenant setting with no override for a tenant falls back to the global value. New per-tenant settings are read through `app/tenants/settings.py` `tenant_setting` and overridden in `config/tenants.yaml`.
