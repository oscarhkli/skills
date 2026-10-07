**Carol:** Should the export run synchronously in the request, or as a background job?
**Dave:** Sync is simpler. Most exports are small.
**Carol:** Some customers export 2M rows. That will time out at 30s.
**Dave:** Fair. Background job then, and email a download link when done?
**Erin:** Email links leak. Let's show it on the Exports page instead and keep links valid for 24h.
**Dave:** Agreed. Background job, Exports page, 24h links.
**Carol:** 👍
