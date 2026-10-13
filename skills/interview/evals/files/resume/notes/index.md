# Per-tenant retention

Goal: let retention differ per tenant instead of one global value.

## Verified facts

- `retention_days` is 30. Source: `config.yaml`. Checked 2026-09-01.
- `retention_days` is read only in `cleanup.py` (`purge`). Checked 2026-09-01.

## User answers

- "Keep it backwards compatible, no data migration." (user, 2026-09-01)

## Open items

- Blocking: what does a tenant without an override get? Asked in review thread 101. No reply yet.

## Next step

Wait for the reply on thread 101, then draft the plan.