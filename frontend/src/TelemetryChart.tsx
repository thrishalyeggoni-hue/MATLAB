import { memo, useMemo } from "react";
import type {
  Data,
  Layout,
  PlotRelayoutEvent,
  PlotMouseEvent,
} from "plotly.js";
import Plot from "./Plot";
import type { Analysis, Comparison, Selection } from "./types";
import { COLORS, interpolate } from "./format";
import { AngularPanel } from "./components";
import { BASE_LAYOUT } from "./plotTheme";

function TelemetryChartView({
  comparison,
  selections,
  analysis,
  channel,
  title,
  unit,
  time,
  range,
  cursor,
  setRange,
  setCursor,
  onSeek,
}: {
  comparison: Comparison;
  selections: (Selection | null)[];
  analysis: Analysis | null;
  channel: "speed" | "throttle" | "brake" | "gear" | "rpm" | "delta";
  title: string;
  unit: string;
  time: number;
  range: [number, number] | null;
  cursor: number | null;
  setRange: (r: [number, number] | null) => void;
  setCursor: (x: number | null) => void;
  onSeek: (x: number) => void;
}) {
  const isDelta = channel === "delta";
  const datasets: Data[] = useMemo(
    () =>
      isDelta
        ? analysis
          ? [
              {
                x: analysis.distance,
                y: analysis.delta,
                type: "scatter",
                mode: "lines",
                name: "B − A (estimated)",
                line: { color: "#e5e8ed", width: 2 },
                hovertemplate: "%{y:.3f} s<extra></extra>",
              },
            ]
          : []
        : comparison.traces.map((t, i) => ({
            x: t.samples.distance,
            y: t.samples[channel],
            type: "scatter",
            mode: "lines",
            name: `${i ? "B" : "A"} / ${selections[i]?.driver.code}`,
            line: {
              color: COLORS[i],
              width: 1.7,
              shape:
                channel === "brake" || channel === "gear" ? "hv" : "linear",
            },
            hovertemplate: `%{y:.${channel === "brake" || channel === "gear" ? "0" : "1"}f} ${unit}<extra></extra>`,
          })),
    [isDelta, analysis, comparison, selections, channel, unit],
  );
  const replayX = interpolate(
    comparison.traces[0].samples.time,
    comparison.traces[0].samples.distance,
    time,
  );
  const layout: Partial<Layout> = {
    ...BASE_LAYOUT,
    height: 250,
    uirevision: "linked-telemetry",
    xaxis: {
      ...BASE_LAYOUT.xaxis,
      ...(range ? { range } : { autorange: true }),
    },
    yaxis: {
      ...BASE_LAYOUT.yaxis,
      title: { text: unit },
      ...(channel === "brake"
        ? { tickvals: [0, 1], ticktext: ["OFF", "ON"], range: [-0.1, 1.1] }
        : {}),
    },
    shapes: [
      ...(replayX != null
        ? [
            {
              type: "line" as const,
              xref: "x" as const,
              yref: "paper" as const,
              x0: replayX,
              x1: replayX,
              y0: 0,
              y1: 1,
              line: { color: "#ffffff80", width: 1, dash: "dot" as const },
            },
          ]
        : []),
      ...(cursor !== null
        ? [
            {
              type: "line" as const,
              xref: "x" as const,
              yref: "paper" as const,
              x0: cursor,
              x1: cursor,
              y0: 0,
              y1: 1,
              line: { color: "#d4dae2", width: 1 },
            },
          ]
        : []),
    ],
  };
  function relayout(e: PlotRelayoutEvent) {
    if (e["xaxis.autorange"]) setRange(null);
    else if (
      e["xaxis.range[0]"] !== undefined &&
      e["xaxis.range[1]"] !== undefined
    )
      setRange([Number(e["xaxis.range[0]"]), Number(e["xaxis.range[1]"])]);
  }
  return (
    <AngularPanel className="chart-panel">
      <div className="panel-title">
        <h3>{title}</h3>
        <span>
          {isDelta ? "POSITIVE = B TAKES LONGER" : "RECORDED CHANNEL / " + unit}
        </span>
      </div>
      {isDelta && !analysis ? (
        <p className="empty-chart">
          Distance delta is unavailable until the numerical analysis loads.
        </p>
      ) : (
        <Plot
          data={datasets}
          layout={layout}
          useResizeHandler
          style={{ width: "100%" }}
          config={{
            responsive: true,
            displaylogo: false,
            modeBarButtonsToRemove: ["lasso2d", "select2d"],
            scrollZoom: false,
          }}
          onRelayout={relayout}
          onHover={(e: PlotMouseEvent) => {
            const x = e.points[0]?.x;
            if (typeof x === "number") setCursor(x);
          }}
          onUnhover={() => setCursor(null)}
          onClick={(e: PlotMouseEvent) => {
            const x = e.points[0]?.x;
            if (typeof x === "number") onSeek(x);
          }}
        />
      )}
    </AngularPanel>
  );
}

export const TelemetryChart = memo(TelemetryChartView);
