# F1 Driver DNA

A local React + TypeScript + Vite app with a FastAPI backend for comparing real Formula 1 laps. The angular driver-card design follows the supplied reference, without game branding or fabricated ratings.

## Start

Prerequisites: Python 3.11/3.12, Node.js LTS (Node 24 recommended for the built-in test runner), npm, and optionally VS Code/Git.

From this project folder, use two terminals:

```bash
# Terminal 1 — backend
source .venv/bin/activate
uvicorn backend.main:app --reload --reload-dir backend
```

```bash
# Terminal 2 — frontend
cd frontend
npm run dev
```

Open **http://127.0.0.1:5174/** (or the URL printed by Vite).
API documentation: http://127.0.0.1:8000/docs

On a fresh checkout, first install dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd frontend
npm ci
```

On Windows, create the environment with `py -3.12 -m venv .venv` and activate it with `.venv\Scripts\Activate.ps1` in PowerShell. The Python lockfile records the verified environment; use `backend/requirements-lock.txt` instead to reproduce those versions on a compatible platform.

## Data sources — choose explicitly

**FastF1 driver identities + OpenF1 telemetry is the default for this setup.** Its free historical archive covers 2023 onward, without an F1 TV subscription. Calendars come from FastF1. Driver names, abbreviations and teams come from FastF1 results, loaded without requesting lap or telemetry archives. A participant must match both number and abbreviation before enrichment. Unmatched participants retain OpenF1 metadata, with the matched count shown in the source note. If FastF1 metadata cannot load, the source note explicitly reports the OpenF1 fallback. The adapter matches the exact season, session name, country, and scheduled UTC date; it refuses ambiguous or missing matches. The participant list, team colours, racing numbers, tyres, lap and sector durations, car telemetry, and location samples come from that matching OpenF1 session. It never substitutes another event. Requests are spaced to respect the free rate limit and cached under `.cache/openf1`.

**FastF1 remains selectable.** In October 2026, F1 began requiring an F1 TV Access subscription or higher for timing-archive downloads. This project pins the maintainer's FastF1 `3.9.0a0` authentication preview to support that change. If you have a subscription, authenticate locally:

```bash
.venv/bin/python -m fastf1 auth f1tv --authenticate --method browser
```

The browser method uses the official FastF1 Companion extension. Never put passwords or tokens in frontend code or chat. FastF1 stores its token outside the repository. Click Retry after authentication; if a token is not picked up in an already-running process, restart the backend. Existing cached recorded sessions can also work. FastF1 caches downloads under `.cache/fastf1`. Without timing access, available recorded results still appear and timing fields remain unavailable.

Sources: [OpenF1 docs](https://openf1.org/docs/), [FastF1 archive authentication update](https://github.com/theOehrly/Fast-F1/issues/978), [FastF1 auth docs](https://docs.fastf1.dev/versions/dev/api_reference/accounts_auth.html).

OpenF1's free archive is intended for personal education and research. No deployment or public hosting is configured. This independent educational app is not affiliated with Formula 1, the FIA, EA Sports, or any team.

## Use the app

1. Choose a source, season, Grand Prix, and session. The initial selection is the first recorded supported event of 2024, qualifying where available.
2. Activate Driver A or B and select a card. The fastest eligible lap is selected initially. The other empty slot activates automatically.
3. Use the lap picker to inspect all recorded laps, their eligibility, and timing. Remove, replace, and swap selections as needed. The same driver cannot occupy both slots; same-team drivers receive distinct comparison colours.
4. Compare selected laps to retrieve their recorded telemetry. The first download can take a minute; subsequent comparisons use cached data.
5. Use Track Replay, Telemetry, Mathematics, and Methods in the header.

Changing the source, Grand Prix, season, or session clears incompatible selections and replay results. Missing data has explicit unavailable states and Retry controls. Driver cards use real, locally stored photographs from Wikimedia Commons, with individual photographer credits, source links, and licences in Methods. Photographs are illustrative portraits, not necessarily photographs from the selected session or year; team names and colours still come from session data. Initials remain the fallback for missing or failed images. Known country codes map to flag emoji; unknown codes are shown as text.

## Replay and timing

- Both selected laps start together: **ghost comparison**, never actual race position or an overtake claim.
- Markers follow recorded timestamped X/Y coordinates; frames use `requestAnimationFrame` entirely in the browser.
- Play/pause, restart, speed, timeline, and keyboard controls are supported. Space toggles playback and arrow keys seek when focus is outside form controls.
- Official recorded lap/sector values are separate from estimated running values. Timing sectors follow recorded sector durations, never equal-distance thirds.
- The underlined sector is faster of the selected pair only, not session best.
- FastF1 may merge/interpolate car and position streams. OpenF1 mode joins its car and location samples by recorded UTC timestamps. Gear and brake use the preceding sample.
- OpenF1 lap starts and locations are approximate. Distance is estimated using trapezoidal integration of recorded speed. Its approximate distance-aligned delta is B's elapsed time minus A's at common measured distance, not the official final lap-time difference.
- Substantial gaps in an OpenF1 lap's telemetry cause an explicit rejection. The app does not synthesize missing laps.
- Track geometry comes from the selected lap, not a static circuit image. FastF1/MultiViewer corner labels appear only when available. OpenF1 mode has no invented corner labels.

## Eligibility and mathematics

FastF1 mode requires a timed, accurate lap that is not deleted, generated, or a pit in/out lap. OpenF1 mode requires a timestamp, full sector durations agreeing with lap duration within 0.05 s, no pit-out or recorded pit-lane indicators, and no matched race-control deletion. Reinstatement reverses a matched deletion. OpenF1 does not expose FastF1's IsAccurate flag; eligibility policies are documented separately. Eligibility does not guarantee telemetry coverage.

Both laps are aligned to 400 samples on their overlapping estimated distance. Complete measurements are jointly mean-centred and optionally standardized. Speed, throttle, and RPM are continuous; brake/gear use preceding samples. One shared PCA is fitted across both drivers. Covariance eigenvalues/eigenvectors and full SVD use that same matrix; the UI exposes numeric outputs and reconstruction error.

Curve fitting uses SciPy least squares on speed over a selected distance interval. Degree 1–5 is supported, with normalized distance, coefficients, RMSE, and R² shown. These are descriptive measurement comparisons, not driver ratings, personality measures, or proof of ability. Car, fuel, tyres, traffic, conditions, sampling, and interpolation limit interpretation.

## Checks

```bash
# From the project root
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s backend/tests -v
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend run lint
```

Tests use synthetic fixtures only inside test files. The app never serves synthetic race data. Verification screenshots and notes are in `verification/`; the reference brief and screenshot are in `reference/`.

The Vite development server proxies `/api` to port 8000. For a separately hosted frontend, set `VITE_API_URL` at build time to the actual backend origin and configure appropriate server access. A static frontend alone cannot run the Python backend.

Virtual environments, node_modules, caches, build output, `.env` files, and Python bytecode are excluded from Git. Streamlit and extra animation libraries are not used.

## Driver photography

Original source images are in `frontend/public/portraits/`, with a complete `credits.json` manifest. The UI catalog is `frontend/src/portrait-catalog.json`. Each photograph retains its own linked licence (CC BY, CC BY-SA, CC0, or OGL), including attribution and share-alike requirements. Original image bytes are retained; the UI uses CSS framing and edge fades without retouching or generating faces. `scripts/install_portraits.py` re-downloads individually reviewed sources, spaces requests, and stops on rate limiting. `reference/portrait-discovery.json` records discovery candidates; only reviewed, downloaded images are included in the actual catalog.

## Full-race playback

Track Replay now defaults to **Full race · all laps** for the chosen Grand Prix and driver pair. It loads the matching Race session from the free OpenF1 archive, even when the comparison laps were selected from qualifying. Both cars share recorded elapsed race time; this is not a repeated fastest lap or a lap-synchronized ghost replay. The sidebar lists every recorded lap, includes pit/flagged/untimed entries, shows the current lap, and highlights each driver's fastest eligible race lap. Click a timestamped lap to jump, scrub the full race timeline, or use playback speeds up to 64×. The original single-lap view remains under **Selected lap comparison**.

Whole-session car and location downloads are cached locally. Missing position/car coverage and gaps longer than three seconds hide that car instead of extrapolating it. Laps lacking a start timestamp remain listed with jumping disabled. The race clock continues to the recorded race end even if a selected driver stops earlier. First retrieval can take several minutes. Track geometry and sector boundaries use the selected comparison lap; moving cars use full-race coordinates and timestamps.

## Replay sound and winner commentary

Use **Enable sound** beneath the timeline. Audio is opt-in, with volume and Both cars / Driver A / Driver B controls. A and B are panned left/right. Engine pitch follows RPM, engine level follows throttle, recorded gear changes cause short torque-cut pulses, and recorded braking drives a synthesized braking tone. Wind level follows speed. Missing channels, telemetry gaps, paused playback and hidden tabs are muted. Acceleration of the replay does not multiply audio pitch by the playback-speed setting.

The engine texture uses LordFluffeh’s CC0 [Formula 1 racing](https://freesound.org/people/LordFluffeh/sounds/478546/) trackside sample. The original preview is stored in `frontend/public/audio/f1-brands-hatch.mp3` with `credits.json`. A short crossfaded loop is made in memory and modulated using telemetry. This is an illustrative soundscape; it is not original audio from the selected driver or race. Brake/wind/shift effects are synthesized.

In full-race mode, **Winner announcement** speaks the classified race winner in the browser’s announcer voice when continuous playback crosses that driver’s recorded finish. It uses FastF1/Jolpica final position, including winners outside the selected pair; fastest laps are never used to decide the winner. Seeking past the finish is silent. The finish banner provides a button to replay the announcement when sound is enabled. If the classified winner or speech support is unavailable, no winner is invented. Muting or leaving the replay closes its AudioContext and cancels its own speech.
