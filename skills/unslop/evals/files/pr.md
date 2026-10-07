## Summary

I started by investigating the failing test, then traced the issue to the date parser. After a few attempts, I found the root cause: the parser assumed UTC. In the first pass I tried patching the caller, but the reviewer pointed out this would miss other callers, so in the second iteration I moved the fix into the parser itself.

## Changes

- Updated per review feedback: `parseDate` now accepts an explicit time zone and defaults to the caller's local zone.
- Round 2 of the self-review found a missing null check, which has now been added: `parseDate(null)` returns `null`.
- Added unit tests.

## Testing

All tests pass locally.
