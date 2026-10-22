import { useState } from "react";
import MathJourney from "./MathJourney";
import type { Analysis, Selection } from "./types";
import type { Data } from "plotly.js";
import Plot from "./Plot";
import { BASE_LAYOUT } from "./plotTheme";
import { AngularPanel, DataStatus } from "./components";
import { COLORS, numeric } from "./format";
export interface AnalysisSettings {
  degree: number;
  start: number;
  end: number | null;
  scale: boolean;
  features: string[];
}
const LABELS: Record<string, string> = {
  speed: "Speed (km/h)",
  throttle: "Throttle (%)",
  brake: "Brake (0/1)",
  gear: "Gear",
  rpm: "RPM",
};
export default function Mathematics({
  analysis,
  settings,
  setSettings,
  loading,
  error,
  selections,
  maxDistance,
  onRetry,
}: {
  analysis: Analysis | null;
  settings: AnalysisSettings;
  setSettings: (s: AnalysisSettings) => void;
  loading: boolean;
  error: string | null;
  selections: (Selection | null)[];
  maxDistance: number;
  onRetry: () => void;
}) {
  const [module, setModule] = useState("Walkthrough"),
    [pc, setPC] = useState(0);
  const [draft, setDraft] = useState(settings);
  const plotLayout = { ...BASE_LAYOUT, height: 350, showlegend: true };
  let data: Data[] = [],
    explanation = "",
    interpretation = "";
  if (analysis && module === "PCA") {
    data = analysis.scores.map((rows, i) => ({
      x: rows.map((r) => r[0]),
      y: rows.map((r) => r[1]),
      type: "scatter",
      mode: "markers",
      name: selections[i]?.driver.code,
      marker: { color: COLORS[i], size: 4, opacity: 0.65 },
      text: analysis.distance.map((d) => `${d.toFixed(0)} m`),
      hovertemplate: "PC1 %{x:.2f}<br>PC2 %{y:.2f}<br>%{text}<extra></extra>",
    }));
    explanation =
      "Principal components rotate the same jointly fitted measurement space for both drivers. Each point is a sampled distance along one lap.";
    interpretation = `PC1 explains ${(analysis.explained_variance[0] * 100).toFixed(1)}% and PC2 explains ${(analysis.explained_variance[1] * 100).toFixed(1)}% of variation in this selected data. Overlap indicates similar measurements, not similar personality or equal ability.`;
  } else if (analysis && module === "Eigenvalues") {
    data = [
      {
        x: analysis.eigenvalues.map((_, i) => `λ${i + 1}`),
        y: analysis.eigenvalues,
        type: "bar",
        name: "Covariance eigenvalue",
        marker: { color: "#ff646e" },
      },
    ];
    explanation =
      "Eigenvectors are directions in the shared measurement space. Their eigenvalues quantify variance along those directions. Both are calculated from the covariance matrix of the centred input.";
    interpretation =
      "The largest eigenvalues identify the strongest directions of variation. Feature units dominate this result when standardization is disabled. Eigenvector signs are arbitrary.";
  } else if (analysis && module === "SVD") {
    data = [
      {
        x: analysis.singular_values.map((_, i) => `σ${i + 1}`),
        y: analysis.singular_values,
        type: "bar",
        name: "Singular value",
        marker: { color: "#69d6df" },
      },
    ];
    explanation =
      "Singular value decomposition factors the joint, centred matrix X into UΣVᵀ. The right singular vectors are PCA directions; σ²/(n − 1) gives each covariance eigenvalue.";
    interpretation = `Reconstructing X with all components gives a relative Frobenius error of ${analysis.svd_relative_error.toExponential(2)}. This is a numerical identity check, not a prediction score.`;
  } else if (analysis && module !== "Walkthrough") {
    data = analysis.fit.drivers.flatMap((fit, i) => [
      {
        x: analysis.fit.distance,
        y: fit.observed,
        type: "scatter" as const,
        mode: "lines" as const,
        name: `${selections[i]?.driver.code} recorded`,
        line: { color: COLORS[i], width: 1 },
        opacity: 0.5,
      },
      {
        x: analysis.fit.distance,
        y: fit.fitted,
        type: "scatter" as const,
        mode: "lines" as const,
        name: `${selections[i]?.driver.code} fitted`,
        line: { color: COLORS[i], width: 2.5, dash: "dash" as const },
      },
    ]);
    explanation =
      "A least-squares polynomial summarizes recorded speed over the chosen distance interval. Distance is normalized to u = (distance − origin) / span before fitting.";
    interpretation =
      "This descriptive fit smooths the data; it is not a vehicle dynamics model. A high-degree global polynomial can miss braking zones or oscillate between measurements. RMSE is in km/h.";
  }
  const axes =
    module === "PCA"
      ? { x: "PC1 (score)", y: "PC2 (score)" }
      : module === "Curve fitting"
        ? { x: "DISTANCE (m)", y: "SPEED (km/h)" }
        : {
            x: "COMPONENT",
            y: module === "SVD" ? "SINGULAR VALUE" : "VARIANCE",
          };
  return (
    <div className="math-workspace">
      <div className="math-tabs">
        {["Walkthrough", "PCA", "Eigenvalues", "SVD", "Curve fitting"].map((m, i) => (
          <button
            key={m}
            onClick={() => setModule(m)}
            className={module === m ? "active" : ""}
          >
            <span>0{i + 1}</span>
            {m === "Eigenvalues" ? "Eigenvalues & vectors" : m}
          </button>
        ))}
      </div>
      <AngularPanel className="analysis-controls">
        <div className="panel-title">
          <h3>SHARED INPUT MEASUREMENTS</h3>
          <span>ONE MODEL / BOTH DRIVERS</span>
        </div>
        <div className="feature-checkboxes">
          {Object.keys(LABELS).map((f) => (
            <label key={f}>
              <input
                type="checkbox"
                checked={draft.features.includes(f)}
                onChange={(e) =>
                  setDraft({
                    ...draft,
                    features: e.target.checked
                      ? [...draft.features, f]
                      : draft.features.filter((k) => k !== f),
                  })
                }
              />
              {LABELS[f]}
            </label>
          ))}
          <label>
            <input
              type="checkbox"
              checked={draft.scale}
              onChange={(e) => setDraft({ ...draft, scale: e.target.checked })}
            />
            Standardize channels
          </label>
        </div>
        <div className="fit-controls">
          <label>
            Polynomial degree
            <select
              value={draft.degree}
              onChange={(e) =>
                setDraft({ ...draft, degree: Number(e.target.value) })
              }
            >
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n}>{n}</option>
              ))}
            </select>
          </label>
          <label>
            From (m)
            <input
              type="number"
              min="0"
              max={maxDistance}
              value={draft.start}
              onChange={(e) =>
                setDraft({ ...draft, start: Number(e.target.value) })
              }
            />
          </label>
          <label>
            To (m)
            <input
              type="number"
              min={draft.start + 1}
              max={Math.ceil(maxDistance)}
              value={draft.end ?? Math.floor(maxDistance)}
              onChange={(e) =>
                setDraft({ ...draft, end: Number(e.target.value) })
              }
            />
          </label>
          <button
            className="button primary"
            disabled={
              loading ||
              draft.features.length < 2 ||
              (draft.end !== null && draft.end <= draft.start)
            }
            onClick={() => {
              setPC(0);
              setSettings({ ...draft });
            }}
          >
            Calculate
          </button>
        </div>
        <p>
          At least two channels are required. PCA, eigenvalues and SVD use both
          full aligned laps. The distance interval applies to curve fitting
          only.
        </p>
      </AngularPanel>
      {loading && (
        <DataStatus loading>
          Calculating the shared measurement matrix and numerical
          decompositions…
        </DataStatus>
      )}
      {error && <DataStatus error={error} onRetry={onRetry} />}
      {analysis && !loading && !error && (module === "Walkthrough" ? <MathJourney analysis={analysis} selections={selections} /> : (
        <>
          <div className="math-module-head">
            <div>
              <span className="eyebrow">
                COMPUTED FROM {analysis.sample_count} ALIGNED OBSERVATIONS
              </span>
              <h2>
                {module === "Eigenvalues"
                  ? "EIGENVALUES & EIGENVECTORS"
                  : module.toUpperCase()}
              </h2>
              <p>{explanation}</p>
            </div>
          </div>
          <AngularPanel className="chart-panel">
            <Plot
              data={data}
              layout={{
                ...plotLayout,
                xaxis: { ...BASE_LAYOUT.xaxis, title: { text: axes.x } },
                yaxis: { ...BASE_LAYOUT.yaxis, title: { text: axes.y } },
              }}
              config={{ responsive: true, displaylogo: false }}
              useResizeHandler
              style={{ width: "100%" }}
            />
          </AngularPanel>
          <div className="math-output-grid">
            <AngularPanel>
              <span className="eyebrow">NUMERICAL OUTPUT</span>
              {module === "PCA" ? (
                <>
                  <h3>Variance & loadings</h3>
                  <label className="component-select">
                    Inspect component
                    <select
                      value={pc}
                      onChange={(e) => setPC(Number(e.target.value))}
                    >
                      {analysis.explained_variance.map((v, i) => (
                        <option key={i} value={i}>
                          PC{i + 1} · {(v * 100).toFixed(2)}%
                        </option>
                      ))}
                    </select>
                  </label>
                  <table className="matrix-table">
                    <thead>
                      <tr>
                        <th>Feature</th>
                        <th>PC{pc + 1} loading</th>
                        <th>Mean</th>
                        <th>Scale</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysis.features.map((f, i) => (
                        <tr key={f}>
                          <td>{LABELS[f]}</td>
                          <td>{analysis.components[pc]?.[i]?.toFixed(4)}</td>
                          <td>{analysis.means[i].toFixed(2)}</td>
                          <td>{analysis.scales[i].toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              ) : module === "Eigenvalues" ? (
                <>
                  <h3>Covariance eigendecomposition</h3>
                  <div className="matrix-scroll">
                    <table className="matrix-table">
                      <thead>
                        <tr>
                          <th>λ</th>
                          {analysis.features.map((_, i) => (
                            <th key={i}>{i + 1}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>Value</td>
                          {analysis.eigenvalues.map((v, i) => (
                            <td key={i}>{v.toFixed(4)}</td>
                          ))}
                        </tr>
                        {analysis.features.map((f, i) => (
                          <tr key={f}>
                            <td>{f}</td>
                            {analysis.eigenvectors[i].map((v, j) => (
                              <td key={j}>{v.toFixed(4)}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <details>
                    <summary>Covariance matrix</summary>
                    <pre>
                      {analysis.covariance
                        .map((row) => row.map((n) => n.toFixed(3)).join("  "))
                        .join("\n")}
                    </pre>
                  </details>
                </>
              ) : module === "SVD" ? (
                <>
                  <h3>X = UΣVᵀ</h3>
                  <table className="matrix-table">
                    <thead>
                      <tr>
                        <th>Component</th>
                        <th>σ</th>
                        <th>σ² / (n − 1)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysis.singular_values.map((v, i) => (
                        <tr key={i}>
                          <td>{i + 1}</td>
                          <td>{v.toFixed(5)}</td>
                          <td>
                            {((v * v) / (analysis.sample_count - 1)).toFixed(5)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p>
                    U: {analysis.sample_count} × {analysis.features.length} · Σ:{" "}
                    {analysis.features.length} × {analysis.features.length} ·
                    Vᵀ: {analysis.features.length} × {analysis.features.length}
                  </p>
                </>
              ) : (
                <>
                  <h3>Degree {analysis.fit.degree} · least squares</h3>
                  {analysis.fit.drivers.map((fit, i) => (
                    <div key={i} className="fit-result">
                      <b style={{ color: COLORS[i] }}>
                        {selections[i]?.driver.code}
                      </b>
                      <p>
                        RMSE {fit.rmse.toFixed(3)} km/h · R²{" "}
                        {numeric(fit.r_squared, 4)}
                      </p>
                      <code>
                        c₀…c{analysis.fit.degree}:{" "}
                        {fit.coefficients.map((c) => c.toFixed(3)).join(", ")}
                      </code>
                    </div>
                  ))}
                  <p>
                    u = (distance − {analysis.fit.origin.toFixed(1)}) /{" "}
                    {analysis.fit.span.toFixed(1)}
                    <br />
                    speed = c₀ + c₁u + c₂u² + …
                  </p>
                </>
              )}
            </AngularPanel>
            <AngularPanel>
              <span className="eyebrow">READING THE RESULT</span>
              <h3>What this tells you.</h3>
              <p>{interpretation}</p>
              <div className="method-callout">
                These are two selected laps, influenced by car, tyres, fuel,
                traffic and conditions. No mathematical output here is a driver
                rating.
              </div>
            </AngularPanel>
          </div>
        </>
      ))}
    </div>
  );
}
