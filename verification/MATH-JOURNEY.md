# Inspectable mathematics verification

## Recorded comparison

2024 Bahrain Qualifying: Charles Leclerc L12 (687 source samples) and Max Verstappen L16 (700). Shared distance alignment produces 400 observations per driver, jointly stacked into an 800 × 5 matrix. The walkthrough labels aligned/interpolated values separately from source-sample counts.

## Numeric and interactive checks

- PCA PC1 explains 60.859%; PC1+PC2 retain 88.728% of joint variation.
- Clicked PCA plot point 201: inspector selected Leclerc L12, matrix row 201, distance 2689.91 m, elapsed 46.778 s. Driver and component selectors update the numeric contribution breakdown and graph.
- Covariance speed/throttle cell is 0.50639. Its inspector exposes the selected product and the n−1 denominator. Eigenvector checks show Cv and λv entries side by side, with residual norms around 1e-15.
- SVD rank 1: relative matrix error 0.62563; speed RMSE 26.93631 km/h. Rank 2: retained variation 88.728%, relative matrix error 0.33573, speed RMSE 10.28129 km/h. Rank 5: relative matrix error 7.7411e-16, speed RMSE 2.7029e-14 km/h.
- Expanded U/Σ/Vᵀ entries, checked singular-value/eigenvalue relation, and verified the inspector substitutes actual U, σ and Vᵀ entries for the selected row/channel.
- Polynomial plots show observed/fitted values, residual traces, fitted coefficients, normalized-distance substitution, RMSE and R². Fitting is explicitly a separate branch from aligned speed, not downstream of PCA/SVD.
- Recalculated with only speed/throttle and scaling off: all dimensions adapted to 800 × 2, rank maximum became 2, and full-rank relative error was 2.5201e-16. Restored all five standardized channels.
- Downloaded JSON includes full raw/centred matrices, source metadata, U, Vᵀ, all per-component contributions and all rank reconstructions. CSV has 800 rows and 14 columns. Parsed both exports independently and verified the raw entries match exactly and PCA contribution sums reproduce backend scores.
- Desktop 1280: plots and equation inspector side by side. Mobile 390: single-column layout with matrix tables scrolling inside their containers. Browser console checks reported no errors.

## Automated checks

20 backend tests and 11 frontend tests pass; production build succeeds. Lint succeeds with six pre-existing async loading/reset warnings. New numerical regressions independently verify scaling, covariance, contribution sums, eigen equations, thin-SVD reconstruction, restored-unit RMSE, monotonic rank error and the retained-energy/error identity for both standardized and unscaled input.

The API's numeric arrays drive all charts. Equations substitute their actual entries; displayed numbers are rounded, while exports retain full precision. Original analysis tabs and race replay remain available.
