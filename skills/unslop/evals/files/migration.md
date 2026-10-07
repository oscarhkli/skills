## Upgrading to 2.0

Version 2.0 removes the `legacy_auth` flag. Deployments that still set it must move to `auth.mode` before upgrading, or startup fails.

Tests: 14 added, all pass locally.
