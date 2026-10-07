## Caching

After a long discussion with the reviewers in the design PR, we decided to drop the original proposal of a separate CacheProvider interface. Initially we considered three options (in-memory, Redis, and a provider abstraction), but following feedback from Alice and Bob we landed on Redis. The CacheProvider interface has since been removed and the service now talks to Redis directly.

Entries expire after 10 minutes. This was changed from 5 minutes in revision 3 after the second review round.

Keys are prefixed with the tenant ID so tenants cannot read each other's data.
