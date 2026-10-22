# Replay audio verification

- Downloaded the published HQ preview of LordFluffeh's "Formula 1 racing" from Freesound. Its primary source page specifies CC0. Original MP3 retained with source/author/licence/processing credits alongside it.
- Browser trusted button interaction successfully created/resumed Web Audio, decoded the sample and started both loop voices. Sound defaults off.
- Verified Sound ready when paused, Audio running during playback, separate A/B/Both selections, and pause returning to ready state. No browser console errors were observed.
- Verified actual 2024 Bahrain winner from FastF1/Jolpica classification: Max Verstappen, car 1; recorded finish at 5505.276 seconds on the shared race clock.
- Jumped to Verstappen lap 57, played continuously across the finish and verified the chequered-flag winner banner. Explicit replay of the winner announcement produced the visible "Winner announcement playing" status from the browser speech onstart event.
- Unit regressions cover RPM/throttle response, braking effect activation, silence outside coverage and through telemetry gaps, one finish cue per pass, and no automatic announcement when seeking past the finish.
- Backend regression verifies a winner outside the selected driver pair is identified from position 1, rather than inferred from the selected cars or fastest lap.
- Speech is a browser announcer voice. Engine texture is an illustrative licensed trackside recording, rather than original audio from the selected race. Added braking/wind/shift sounds are synthesized.
