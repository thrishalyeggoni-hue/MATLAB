import { useMemo } from "react";
import { Pause, Play, RotateCcw } from "lucide-react";
import type { Comparison, Selection } from "./types";
import { COLORS, interpolate, lapTime, numeric, seconds } from "./format";
import { AngularPanel } from "./components";
import { replayColors, SECTOR_COLORS } from "./replayColors";

export function TrackMap({
  comparison,
  markerComparison,
  selections,
  time,
  section,
  cursor,
}: {
  comparison: Comparison;
  markerComparison?: Comparison;
  selections: (Selection | null)[];
  time: number;
  section: [number, number] | null;
  cursor: number | null;
}) {
  const { points, transform, sectors } = useMemo(() => {
    const s = comparison.traces[0].samples,
      angle = (comparison.rotation * Math.PI) / 180,
      cos = Math.cos(angle),
      sin = Math.sin(angle);
    const rotated = s.x
      .map((x, i) =>
        x == null || s.y[i] == null
          ? null
          : [x * cos - s.y[i]! * sin, x * sin + s.y[i]! * cos],
      )
      .filter((p): p is number[] => p !== null);
    const xs = rotated.map((p) => p[0]),
      ys = rotated.map((p) => p[1]),
      minX = Math.min(...xs),
      maxX = Math.max(...xs),
      minY = Math.min(...ys),
      maxY = Math.max(...ys);
    const scale = Math.min(680 / (maxX - minX || 1), 370 / (maxY - minY || 1)),
      offX = (800 - (maxX - minX) * scale) / 2,
      offY = (470 - (maxY - minY) * scale) / 2;
    const transform = (x: number, y: number) => [
      offX + (x * cos - y * sin - minX) * scale,
      470 - (offY + (x * sin + y * cos - minY) * scale),
    ];
    const points = s.x.map((x, i) =>
      x == null || s.y[i] == null ? null : transform(x, s.y[i]!),
    );
    const durations = comparison.traces[0].lap.sectors;
    const sectors = durations.every((duration) => duration != null && duration > 0)
      ? durations.map((duration, index) => {
          const from = durations.slice(0, index).reduce<number>((sum, value) => sum + value!, 0);
          const until = from + duration!;
          const positionAt = (t: number) => {
            const x = interpolate(s.time, s.x, t), y = interpolate(s.time, s.y, t);
            return x == null || y == null ? null : transform(x, y);
          };
          const segment = [positionAt(from), ...points.filter((p, i) => p && s.time[i] > from && s.time[i] < until), positionAt(until)]
            .filter((p): p is number[] => p !== null);
          return { duration: duration!, points: segment, boundary: segment[0] };
        })
      : [];
    return { points, transform, sectors };
  }, [comparison]);
  const path = points
    .filter((p): p is number[] => p !== null)
    .map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(2)},${p[1].toFixed(2)}`)
    .join(" ");
  const highlighted = section
    ? points.filter(
        (p, i) =>
          p &&
          comparison.traces[0].samples.distance[i] != null &&
          comparison.traces[0].samples.distance[i]! >= section[0] &&
          comparison.traces[0].samples.distance[i]! <= section[1],
      )
    : [];
  const start = points.find(Boolean);
  const s = comparison.traces[0].samples;
  const markerTraces = markerComparison?.traces || comparison.traces;
  const traceVisible = (trace: Comparison["traces"][number]) => !markerComparison ||
    (time >= trace.samples.time[0] && time <= trace.samples.time.at(-1)! &&
      !trace.gaps?.some(([from, to]) => time > from && time < to));
  const markerPositions = markerTraces.map((trace) => {
    if (!traceVisible(trace)) return null;
    const x = interpolate(trace.samples.time, trace.samples.x, time);
    const y = interpolate(trace.samples.time, trace.samples.y, time);
    return x == null || y == null ? null : transform(x, y);
  });
  const markerDrivers = markerTraces.map((trace) =>
    selections.find((selection) => selection?.driver.id === trace.driver)?.driver,
  );
  const nearbySectors = markerPositions.map((position) => position
    ? sectors.flatMap((sector, index) => sector.points.some((point) =>
        Math.hypot(point[0] - position[0], point[1] - position[1]) < 30)
        ? [SECTOR_COLORS[index]] : [])
    : []);
  const markerColors = replayColors(markerDrivers.map((driver, i) => driver?.color || COLORS[i]), nearbySectors, COLORS);
  const cursorPoint =
    cursor === null
      ? null
      : (() => {
          const valid = s.distance
            .map((d, i) =>
              d === null || s.x[i] === null || s.y[i] === null
                ? null
                : [d, s.x[i]!, s.y[i]!],
            )
            .filter((row): row is number[] => row !== null);
          const distances = valid.map((row) => row[0]);
          const x = interpolate(
              distances,
              valid.map((row) => row[1]),
              cursor,
            ),
            y = interpolate(
              distances,
              valid.map((row) => row[2]),
              cursor,
            );
          return x == null || y == null ? null : transform(x, y);
        })();
  return (
    <div className="track-canvas">
      <svg
        viewBox="0 0 800 470"
        role="img"
        aria-label={`${comparison.event} circuit, derived from selected lap position telemetry`}
      >
        <defs>
          <g id="replay-f1-car">
            <path d="M-7-10H7M-7 9H7" stroke="#a5afbc" strokeWidth="2" />
            <g fill="#090c12" stroke="#a5afbc" strokeWidth=".7">
              <rect x="-10" y="-13" width="5" height="8" rx="1.5" />
              <rect x="5" y="-13" width="5" height="8" rx="1.5" />
              <rect x="-10" y="5" width="5" height="9" rx="1.5" />
              <rect x="5" y="5" width="5" height="9" rx="1.5" />
            </g>
            <g stroke="#edf3fa" strokeWidth=".8" strokeLinejoin="round">
              <path d="M-1.5-17H1.5L3-7 6-2 6 9 4 14H-4L-6 9V-2L-3-7Z" />
              <path d="M-9-17H9V-14H-9ZM-8 13H8V17H-8Z" />
            </g>
            <path d="M0-12V-6M-4 4V10M4 4V10" stroke="#fff" strokeWidth="1.2" />
            <ellipse cy="0" rx="2.8" ry="4.3" fill="#10151d" stroke="#d6e0ed" strokeWidth=".7" />
            <path d="M-3-1Q0-5 3-1M0-3V2" fill="none" stroke="#d6e0ed" strokeWidth="1" />
          </g>
          <pattern
            id="grid"
            width="26"
            height="26"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 26 0 L 0 0 0 26"
              fill="none"
              stroke="#ffffff"
              strokeOpacity=".035"
              strokeWidth=".8"
            />
          </pattern>
        </defs>
        <rect width="800" height="470" fill="url(#grid)" />
        <path
          d={path}
          fill="none"
          stroke="#090b0e"
          strokeWidth="19"
          strokeLinejoin="round"
        />
        <path
          d={path}
          fill="none"
          stroke="#3f464f"
          strokeWidth="11"
          strokeLinejoin="round"
        />
        {sectors.map((sector, i) => (
          <g key={i}>
            <title>{`Sector ${i + 1} · ${seconds(sector.duration)} s · boundary estimated from Driver A's recorded sector timing and position samples`}</title>
            <polyline
              points={sector.points.map((p) => p.join(",")).join(" ")}
              fill="none"
              stroke={SECTOR_COLORS[i]}
              strokeWidth="18"
              strokeOpacity=".14"
              strokeLinejoin="round"
            />
            <polyline
              points={sector.points.map((p) => p.join(",")).join(" ")}
              fill="none"
              stroke={SECTOR_COLORS[i]}
              strokeWidth="9"
              strokeLinejoin="round"
            />
            {i > 0 && sector.boundary && (
              <rect x={sector.boundary[0] - 3.5} y={sector.boundary[1] - 3.5} width="7" height="7" fill={SECTOR_COLORS[i]} stroke="#fff" strokeWidth="1.2" />
            )}
          </g>
        ))}
        {sectors.length === 0 && <path d={path} fill="none" stroke="#a9b2bf" strokeWidth="5" />}
        {highlighted.length > 1 && (
          <polyline
            points={highlighted.map((p) => p!.join(",")).join(" ")}
            fill="none"
            stroke="#fff"
            strokeWidth="6"
            strokeLinecap="round"
          />
        )}
        {comparison.corners.map((c) => {
          const p = transform(c.x, c.y);
          return (
            <g key={c.number}>
              <circle cx={p[0]} cy={p[1]} r="2" fill="#b5bac4" />
              <text
                x={p[0] + 10}
                y={p[1] - 10}
                fill="#858e9e"
                fontSize="10"
                fontFamily="monospace"
              >
                {c.number}
              </text>
            </g>
          );
        })}
        {start && (
          <g>
            <path
              d={`M ${start[0]} ${start[1]} l 0 -25 l 18 0 l 0 12 l -18 0`}
              stroke="#eceff3"
              fill="#eceff3"
              strokeWidth="1.2"
            />
            <text
              x={start[0] + 23}
              y={start[1] - 17}
              fill="#cdd1d8"
              fontSize="10"
              fontFamily="monospace"
            >
              START / FINISH
            </text>
          </g>
        )}
        {markerTraces.map((trace, i) => {
          if (!traceVisible(trace)) return null;
          const x = interpolate(trace.samples.time, trace.samples.x, time),
            y = interpolate(trace.samples.time, trace.samples.y, time);
          if (x == null || y == null) return null;
          const p = transform(x, y);
          const before = Math.max(trace.samples.time[0], time - 0.3);
          const after = Math.min(trace.samples.time.at(-1)!, time + 0.3);
          const bx = interpolate(trace.samples.time, trace.samples.x, before);
          const by = interpolate(trace.samples.time, trace.samples.y, before);
          const ax = interpolate(trace.samples.time, trace.samples.x, after);
          const ay = interpolate(trace.samples.time, trace.samples.y, after);
          let heading = 0;
          if (bx != null && by != null && ax != null && ay != null) {
            const from = transform(bx, by), to = transform(ax, ay);
            heading = Math.atan2(to[1] - from[1], to[0] - from[0]) * 180 / Math.PI + 90;
          }
          const driver = markerDrivers[i];
          const speed = interpolate(trace.samples.time, trace.samples.speed, time);
          // Opposite sides keep both readouts legible when the ghost cars overlap.
          const labelX = i === 0 ? Math.max(8, p[0] - 138) : Math.min(684, p[0] + 30);
          const labelY = Math.max(8, Math.min(436, p[1] - 13));
          return (
            <g key={trace.driver}>
              <title>{`${i ? "B" : "A"} · ${driver?.name || trace.driver} · ${numeric(speed)} km/h · ${driver?.team || "Team unavailable"}${markerColors[i] !== (driver?.color || COLORS[i]) ? " · contrast colour active" : " · team colour"}`}</title>
              <g
                transform={`translate(${p[0]},${p[1]}) rotate(${heading}) scale(1.4)`}
                style={{ filter: "drop-shadow(0 0 1.5px #000) drop-shadow(0 0 2px #000)" }}
              >
                <use href="#replay-f1-car" fill={markerColors[i]} />
                <path d="M-3 8H3V12H-3Z" fill={markerColors[i]} stroke="#111720" strokeWidth=".6" />
              </g>
              <path
                d={`M${p[0]},${p[1]} L${i === 0 ? labelX + 108 : labelX},${labelY + 13}`}
                stroke={COLORS[i]} strokeWidth="1" strokeOpacity=".65" />
              <g transform={`translate(${labelX},${labelY})`} className="car-speed-label">
                <rect width="108" height="26" rx="4" fill="#10151d" fillOpacity=".95" stroke={COLORS[i]} strokeOpacity=".65" />
                <text x="7" y="20" fill={COLORS[i]} fontSize="19" fontFamily="monospace" fontWeight="bold">
                  {i ? "B" : "A"}
                </text>
                <text x="27" y="17" fill="#f4f7fb" fontSize="12" fontFamily="monospace" fontWeight="bold">
                  {numeric(speed)}<tspan fill="#a7b3c3" fontSize="9"> KM/H</tspan>
                </text>
              </g>
            </g>
          );
        })}
        {cursorPoint && (
          <circle
            cx={cursorPoint[0]}
            cy={cursorPoint[1]}
            r="7"
            stroke="#fff"
            strokeWidth="2"
            fill="none"
          />
        )}
      </svg>
      {sectors.length > 0 && (
        <div className="track-sector-legend" aria-label="Track timing sectors">
          {sectors.map((sector, i) => (
            <span key={i}>
              <i style={{ background: SECTOR_COLORS[i], boxShadow: `0 0 10px ${SECTOR_COLORS[i]}55` }} />
              <strong>SECTOR {i + 1}</strong>
              <small>{seconds(sector.duration)} s</small>
            </span>
          ))}
          <p>Boundaries estimated from Driver A’s recorded sector times and position trace.<br />All drivers use a fixed contrast colour when needed; A/B letters identify each car.</p>
        </div>
      )}
      <div className="map-caption">
        <span>POSITION TRACE / {comparison.year}</span>
        <span>{markerComparison ? "RECORDED RACE TIMELINE" : "GHOST LAP COMPARISON"}</span>
      </div>
    </div>
  );
}
export function PlaybackControls({
  speeds = [0.25, 0.5, 1, 2, 4],
  time,
  duration,
  playing,
  speed,
  setTime,
  setPlaying,
  setSpeed,
}: {
  speeds?: number[];
  time: number;
  duration: number;
  playing: boolean;
  speed: number;
  setTime: (t: number) => void;
  setPlaying: (p: boolean) => void;
  setSpeed: (n: number) => void;
}) {
  return (
    <div className="playback-controls">
      <div className="playback-buttons">
        <button
          className="play-button"
          onClick={() => {
            if (time >= duration) setTime(0);
            setPlaying(!playing);
          }}
          aria-label={playing ? "Pause replay" : "Play replay"}
        >
          {playing ? <Pause size={18} /> : <Play size={18} />}
        </button>
        <button
          className="icon-button"
          onClick={() => {
            setTime(0);
            setPlaying(false);
          }}
          aria-label="Restart replay"
        >
          <RotateCcw size={17} />
        </button>
        <span className="elapsed">
          {lapTime(time)} <small>/ {lapTime(duration)}</small>
        </span>
        <label className="speed-label">
          <span className="sr-only">Playback speed</span>
          <select
            value={speed}
            onChange={(e) => setSpeed(Number(e.target.value))}
          >
            {speeds.map((n) => (
              <option value={n} key={n}>
                {n}×
              </option>
            ))}
          </select>
        </label>
      </div>
      <input
        aria-label="Replay timeline"
        className="timeline"
        type="range"
        min="0"
        max={duration}
        step="0.001"
        value={time}
        onChange={(e) => setTime(Number(e.target.value))}
      />
      <span className="playback-hint">SPACE: PLAY / PAUSE · ← →: SEEK</span>
    </div>
  );
}
export function TimingStrip({
  comparison,
  selections,
  time,
}: {
  comparison: Comparison;
  selections: (Selection | null)[];
  time: number;
}) {
  return (
    <AngularPanel className="timing-panel">
      <div className="panel-title">
        <h3>THE TIMING LINE</h3>
        <span>OFFICIAL RECORDED TIMES / SECONDS</span>
      </div>
      <div className="timing-scroll">
        <table className="timing-table">
          <thead>
            <tr>
              <th>DRIVER</th>
              <th>LAP</th>
              <th>LAP TIME</th>
              <th>SECTOR 1</th>
              <th>SECTOR 2</th>
              <th>SECTOR 3</th>
              <th>REPLAY ELAPSED</th>
            </tr>
          </thead>
          <tbody>
            {comparison.traces.map((trace, i) => (
              <tr key={trace.driver}>
                <td style={{ color: COLORS[i] }}>
                  <b>{i ? "B" : "A"}</b> {selections[i]?.driver.code}
                </td>
                <td>{trace.lap.number}</td>
                <td className="lap-time">{lapTime(trace.lap.time)}</td>
                {trace.lap.sectors.map((v, j) => {
                  const other = comparison.traces[1 - i].lap.sectors[j];
                  const best = v != null && other != null && v < other;
                  return (
                    <td key={j} className={best ? "pair-best" : ""}>
                      {seconds(v)}
                    </td>
                  );
                })}
                <td>
                  {lapTime(Math.min(time, trace.samples.time.at(-1) || 0))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="timing-note">
        Underlined sector = faster of this pair only. Recorded sectors may not
        sum exactly to lap time.
      </p>
    </AngularPanel>
  );
}
export function LiveTelemetry({
  comparison,
  selections,
  time,
}: {
  comparison: Comparison;
  selections: (Selection | null)[];
  time: number;
}) {
  return (
    <div className="live-telemetry">
      {comparison.traces.map((trace, i) => {
        const s = trace.samples,
          one = trace.lap.sectors[0],
          two = trace.lap.sectors[1],
          sector =
            one == null || two == null
              ? null
              : time < one
                ? 1
                : time < one + two
                  ? 2
                  : 3;
        return (
          <AngularPanel key={trace.driver}>
            <div className="live-driver" style={{ color: COLORS[i] }}>
              <b>
                DRIVER {i ? "B" : "A"} / {selections[i]?.driver.code}
              </b>
              <span>
                {time >= (s.time.at(-1) || 0)
                  ? "LAP COMPLETE"
                  : sector
                    ? `TIMING SECTOR ${sector}`
                    : "SECTOR UNAVAILABLE"}
              </span>
            </div>
            <div className="live-values">
              {[
                ["speed", "SPEED", "KM/H"],
                ["throttle", "THROTTLE", "%"],
                ["brake", "BRAKE", "ON/OFF"],
                ["gear", "GEAR", ""],
                ["rpm", "RPM", ""],
              ].map(([key, label, unit]) => {
                const value = interpolate(
                  s.time,
                  s[key as "speed"],
                  time,
                  key === "brake" || key === "gear",
                );
                return (
                  <div key={key}>
                    <small>{label}</small>
                    <strong>
                      {key === "brake"
                        ? value == null
                          ? "—"
                          : value
                            ? "ON"
                            : "OFF"
                        : numeric(value)}
                    </strong>
                    <em>{unit}</em>
                  </div>
                );
              })}
            </div>
            <small className="estimated-label">
              ESTIMATED RUNNING VALUES · INTERPOLATED RECORDED SAMPLES
            </small>
          </AngularPanel>
        );
      })}
    </div>
  );
}
