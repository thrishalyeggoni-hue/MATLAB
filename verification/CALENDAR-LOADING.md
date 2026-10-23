# Calendar loading regression - 23 October 2026

The original UI kept polling a 2024 schedule job while FastF1's underlying calendar HTTP request waited without a timeout. Health requests still completed immediately, so a health check alone did not verify application data loading.

## Change

- Added bounded downloads of the original FastF1 schedule JSON and persistent per-season calendar storage.
- Preserved the recorded event fields and UTC conversions used to match exact OpenF1 sessions.
- Constructed FastF1 sessions from the cached event schedule, preventing a second calendar request.
- Added frontend job deadlines, request timeouts and retry errors; user cancellation remains an AbortError.
- Adopted the installed FastF1 version's non-deprecated cache configuration API.

## Evidence

- A fresh direct 2024 calendar call completed in 0.051 seconds and returned 24 Grand Prix events.
- Browser showed Bahrain Grand Prix / Qualifying, 20 participants and actual driver cards/lap times, replacing the indefinite spinner.
- Frontend-proxied calendar and session APIs returned completed jobs with 24 events and 20 drivers.
- Backend: 25 tests passed, including disk reuse after restart, recorded local-to-UTC conversion, explicit network-timeout failure, invalid-response cache protection and stale-current-calendar fallback.
- Frontend: 14 tests passed, including never-finishing polling, an aborted stuck fetch, successful job data and preserved user cancellation.
- Production TypeScript/Vite build passed.

The test fixtures are synthetic and test-only. No substitute calendar or telemetry was served. Existing cached real OpenF1 data was reused.
