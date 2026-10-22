# Mathematics learning guide

The 44-page PDF is at `output/pdf/F1_Driver_DNA_Mathematics_Guide.pdf`.
It covers only the current Mathematics module, progressing from arithmetic and measurement alignment through standardisation, covariance, eigenvectors, PCA, SVD and polynomial fitting. It includes recorded numerical examples, labelled practice data, graph interpretation, UI controls, exercises, worked answers and a teach-back script.

## Rebuild

From the project root, with the project virtual environment active:

```bash
python -m pip install reportlab matplotlib numpy pypdf
python scripts/build_math_guide.py
```

Document packages are optional authoring dependencies; the website does not require ReportLab or pypdf.

`docs/math-guide-example.json` preserves the actual backend calculation used for the recorded graphs. The written narrative identifies 2024 Bahrain qualifying, Leclerc L12 and Verstappen L16, with all five channels standardised. It is intentionally tied to this dataset. If changing the example, update the narrative, labels and numerical checks along with the input. The generator guards against silently substituting a different dataset.

`docs/math-guide-pages.json` indexes the page titles. Temporary chart images and rendered review pages are generated under `tmp/pdfs/` and are not source deliverables.

## Verification

- All 44 pages rendered with Poppler and visually reviewed; changed pages reviewed again at higher resolution.
- Text extraction checked: 44 pages, no replacement/black-square glyphs, no body text outside the margins.
- Recorded covariance recomputed from Q; all PCA scores recomputed by projection.
- U/Sigma/V-transpose product checked against Z; singular-value/eigenvalue relationship checked.
- Every rank's squared relative error checked against one minus retained energy.
- Polynomial predictions and speed RMSE recalculated from the saved arrays.
- No application source or production dependency changes are needed for this guide.
