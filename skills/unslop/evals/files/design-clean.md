## Caching

The service uses Redis directly.

Entries expire after 10 minutes.

Keys are prefixed with the tenant ID so tenants cannot read each other's data.
