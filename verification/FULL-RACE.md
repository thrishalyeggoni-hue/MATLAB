# Full-race replay verification

- Track Replay defaults to Full race / all laps. The original selected-lap comparison remains available.
- Verified live OpenF1 2024 Bahrain Race: both Leclerc and Verstappen have 57 listed laps (114 accessible lap buttons total), including pit / flagged timing entries.
- Fastest eligible race highlights: Leclerc L36 1:34.090; Verstappen L39 1:32.608.
- Clicked L36: race time 57:29.977, both counters L36. Played continuously at 64x; counters advanced independently to Leclerc L47 / Verstappen L48. Paused without losing position.
- Clicked L57: both counters reached L57; the full race is not a loop of the selected qualifying lap.
- Shared race clock, timestamps and original full-session car telemetry; 20,669 Leclerc and 20,528 Verstappen car samples in initial verification. No synthesized lap paths.
- Race duration includes recorded finishes for the whole field; selected drivers can end earlier. Positions are hidden outside source coverage or across gaps longer than 3 seconds.
- Desktop 1280: map and two driver panels side by side. Mobile 390: one-column layout with no horizontal overflow; lap lists scroll inside their own panels.
- Backend 18 tests passed; frontend 7 tests passed; production build passed. Lint exits successfully with six async loading/reset state-in-effect warnings (five pre-existing).
- Backend regression tests cover full-session telemetry gaps, preserved pit and untimed laps, missing lap-start timestamps, and a race clock that continues after selected drivers stop.
- Source note explains OpenF1 race data and comparison-lap sector geometry. Local downloads are cached.

Screenshots: full-race-desktop.png and full-race-mobile.png.
