# Verification — 22 October 2026

## Verified locally

- FastAPI health responds successfully at port 8000; Vite serves the app at port 5174 and proxies API requests.
- Production TypeScript/Vite build succeeds.
- Python dependency check reports no conflicts.
- 14 Python tests pass: shared numerical alignment, PCA/eigen/SVD identities, curve fit accuracy, missing inputs, lap eligibility, API validation, exact event matching, lap deletion/reinstatement, and recorded timestamp joining.
- 3 frontend tests pass: timing formatting, continuous/discrete interpolation, and verified flag mapping.
- Lint completes with five warnings about state resets in effects; no lint errors. These resets clear dependent session/replay state and synchronize asynchronous loads.

## Real data and browser checks

OpenF1 historical archive, explicitly selected in the UI; calendar via FastF1:

1. **2024 Bahrain qualifying**
   - Loaded 20 actual session participants, their racing numbers, team colours, tyres, eligible laps, and recorded sector durations.
   - Charles Leclerc lap 12: 1:29.165; sectors 28.843 / 38.059 / 22.263.
   - Max Verstappen lap 16: 1:29.179; sectors 28.535 / 38.269 / 22.375.
   - Retrieved 687 and 700 joined car/location samples, respectively.
   - Shared analysis used 800 observations; PCA PC1 explained about 60.86%, PC2 about 27.87%; full SVD reconstruction relative error was approximately 7.74e-16.
   - Verified replay play/pause, speed, timeline seeking, and restart in the browser.
   - Verified all six telemetry charts render. Zooming speed changed all six distance axes to the same range.
   - Verified PCA, covariance eigenvalues/eigenvectors, SVD, and degree/range-controlled speed curve fitting. Changing degree to 2 and distance to 1000–2000 m produced new recorded-data fit coefficients and error metrics.
2. **2024 Monaco qualifying**
   - Loaded a distinct matching session with actual participant laps.
   - Charles Leclerc lap 25: 1:10.270; sectors 18.386 / 33.174 / 18.710.
   - Oscar Piastri lap 23: 1:10.424; sectors 18.303 / 33.380 / 18.741.
   - Browser replay showed the Monaco position trace, not the Bahrain circuit.
3. **Selection and responsive behaviour**
   - Duplicate driver selection was rejected with an explanatory message.
   - Two Ferrari drivers retained the same recorded team colour but had distinct coral/cyan comparison colours and A/B badges.
   - Swap changed slot assignments correctly.
   - Changing Grand Prix cleared driver/lap selections and comparison state.
   - Lap picker showed recorded laps, unavailable/deleted/pit timing reasons, and eligible selection controls.
   - Desktop driver grid used five columns; 390 px mobile grid used two columns.
   - Mobile navigation, replay, and mathematics rendered without page-level horizontal overflow (document width and scroll width both 390 px).
   - No browser console errors observed during verified flows.

Screenshots are saved alongside this file. Browser viewport override was reset after mobile checks.

## Limitations retained explicitly

- The user has no F1 TV subscription. FastF1 archive requests returned HTTP 401; authenticated FastF1 telemetry could not be verified. FastF1 remains an explicit selectable source with setup instructions. OpenF1 is the working, free default from 2023 onward.
- Driver portraits were not supplied with a suitable licence. The app uses initials fallbacks, not extracted or fabricated portraits.
- OpenF1 lap-start timestamps and X/Y positions are approximate. Speed integration gives estimated distance. Ghost positions, running values, and distance deltas are labelled estimates, separate from recorded lap/sector timing.
- OpenF1 does not provide the FastF1 IsAccurate flag or corner annotations. Its eligibility rules and source limitations are documented in Methods and the README.
- This is a local app; no public deployment was performed. Other sessions remain subject to source coverage and rate limits.
