import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowUpRight, Maximize2 } from "lucide-react";
import type { Analysis, Comparison, Page, Selection } from "./types";
import { AngularPanel, DataStatus, DriverCard } from "./components";
import { COLORS, interpolate, numeric } from "./format";
import { request } from "./api";
import {
  LiveTelemetry,
  PlaybackControls,
  TimingStrip,
  TrackMap,
} from "./TrackReplay";
import { TelemetryChart } from "./TelemetryChart";
import Mathematics from "./Mathematics";
import type { AnalysisSettings } from "./Mathematics";
import FullRace from "./FullRace";
import ReplayAudio from "./ReplayAudio";

export default function Workspace({
  round,
  page,
  comparison,
  comparisonId,
  selections,
  onSelect,
}: {
  round: number;
  page: Page;
  comparison: Comparison | null;
  comparisonId: string;
  selections: (Selection | null)[];
  onSelect: () => void;
}) {
  const [fullRace, setFullRace] = useState(true);
  const [time, setTime] = useState(0),
    [playing, setPlaying] = useState(false),
    [speed, setSpeed] = useState(1);
  const [range, setRange] = useState<[number, number] | null>(null),
    [cursor, setCursor] = useState<number | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null),
    [analysisBusy, setAnalysisBusy] = useState(false),
    [analysisError, setAnalysisError] = useState<string | null>(null),
    [retry, setRetry] = useState(0);
  const [settings, setSettings] = useState<AnalysisSettings>({
    degree: 3,
    start: 0,
    end: null,
    scale: true,
    features: ["speed", "throttle", "brake", "gear", "rpm"],
  });
  const duration = comparison
    ? Math.max(
        ...comparison.traces.map(
          (t) => t.lap.time || t.samples.time.at(-1) || 0,
        ),
      )
    : 0;
  const timeRef = useRef(0);
  useEffect(() => {
    timeRef.current = time;
  }, [time]);
  useEffect(() => {
    setTime(0);
    setPlaying(false);
    setRange(null);
    setCursor(null);
    setSettings({
      degree: 3,
      start: 0,
      end: null,
      scale: true,
      features: ["speed", "throttle", "brake", "gear", "rpm"],
    });
  }, [comparisonId]);
  useEffect(() => {
    if (!comparisonId) return;
    const controller = new AbortController();
    setAnalysisBusy(true);
    setAnalysisError(null);
    setAnalysis(null);
    request<Analysis>(
      "/api/analysis",
      { comparison_id: comparisonId, ...settings },
      controller.signal,
    )
      .then(setAnalysis)
      .catch((e) => {
        if (e.name !== "AbortError") setAnalysisError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setAnalysisBusy(false);
      });
    return () => controller.abort();
  }, [comparisonId, settings, retry]);
  useEffect(() => {
    if (!playing) return;
    let id = 0,
      last = performance.now();
    const frame = (now: number) => {
      const next = Math.min(
        duration,
        timeRef.current + ((now - last) / 1000) * speed,
      );
      last = now;
      timeRef.current = next;
      setTime(next);
      if (next >= duration) {
        setPlaying(false);
        return;
      }
      id = requestAnimationFrame(frame);
    };
    id = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(id);
  }, [playing, speed, duration]);
  useEffect(() => {
    if (page === "Mathematics") setPlaying(false);
  }, [page]);
  useEffect(() => {
    if (page === "Track Replay" && fullRace) return;
    const handler = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement;
      if (
        el.matches("input,select,textarea,button,a") ||
        el.isContentEditable ||
        page === "Mathematics"
      )
        return;
      if (e.code === "Space") {
        e.preventDefault();
        if (timeRef.current >= duration) setTime(0);
        setPlaying((p) => !p);
      }
      if (e.code === "ArrowRight") {
        e.preventDefault();
        setTime((t) => Math.min(duration, t + 1));
      }
      if (e.code === "ArrowLeft") {
        e.preventDefault();
        setTime((t) => Math.max(0, t - 1));
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [duration, page, fullRace]);
  const seek = useCallback(
    (distance: number) => {
      if (!comparison) return;
      const s = comparison.traces[0].samples;
      const value = interpolate(
        s.distance.map((v) => v ?? NaN),
        s.time,
        distance,
      );
      if (value !== null) {
        setTime(value);
        setPlaying(false);
      }
    },
    [comparison],
  );
  if (!comparison)
    return (
      <div className="workspace-empty">
        <div className="eyebrow">
          {page.toUpperCase()} / NO COMPARISON LOADED
        </div>
        <h1>
          IT STARTS
          <br />
          WITH <span>TWO.</span>
        </h1>
        <p>
          Select two drivers and compare their recorded laps to unlock the
          replay, telemetry, and mathematics workspace.
        </p>
        <button className="button primary" onClick={onSelect}>
          Choose your drivers <ArrowUpRight size={17} />
        </button>
        <DataStatus>
          No comparison data has been substituted or simulated.
        </DataStatus>
      </div>
    );
  const maxDistance = Math.min(
    ...comparison.traces.map((t) =>
      Math.max(...t.samples.distance.filter((d): d is number => d !== null)),
    ),
  );
  const currentDistance = interpolate(
    comparison.traces[0].samples.time,
    comparison.traces[0].samples.distance,
    time,
  );
  const delta =
    analysis && currentDistance !== null
      ? interpolate(analysis.distance, analysis.delta, currentDistance)
      : null;
  const charts = (
    <div className="telemetry-charts">
      {(["speed", "throttle", "brake", "gear", "rpm", "delta"] as const).map(
        (channel, i) => (
          <TelemetryChart
            key={channel}
            comparison={comparison}
            selections={selections}
            analysis={analysis}
            channel={channel}
            title={
              [
                "SPEED TRACE",
                "THROTTLE APPLICATION",
                "BRAKING INPUT",
                "GEAR SELECTION",
                "ENGINE SPEED",
                "ESTIMATED TIME DIFFERENCE",
              ][i]
            }
            unit={["km/h", "%", "ON / OFF", "GEAR", "RPM", "s"][i]}
            time={Math.floor(time * 5) / 5}
            range={range}
            cursor={cursor}
            setRange={setRange}
            setCursor={setCursor}
            onSeek={seek}
          />
        ),
      )}
    </div>
  );
  return (
    <div className="workspace">
      <button className="back-link" onClick={onSelect}>
        <ArrowLeft size={13} /> BACK TO DRIVER SELECTION
      </button>
      <div className="workspace-heading">
        <div>
          <span className="eyebrow">
            {comparison.year} / {page === "Track Replay" && fullRace ? "RACE" : comparison.session.toUpperCase()} / RECORDED
            TELEMETRY
          </span>
          <h1>
            {page === "Track Replay" ? (
              <>
                EVERY <span>METRE.</span>
              </>
            ) : page === "Telemetry" ? (
              <>
                READ THE <span>TRACE.</span>
              </>
            ) : (
              <>
                DECODE THE <span>DNA.</span>
              </>
            )}
          </h1>
          <p>
            {comparison.event}{" "}
            <span className="muted">
              —{" "}
              {page === "Mathematics"
                ? "The measurements behind the difference."
                : page === "Track Replay" && fullRace ? "Full race — every recorded lap on a shared race clock."
                : "Ghost lap comparison — both selected laps start together."}
            </span>
          </p>
        </div>
        <div className="comparison-legend">
          {selections.map((s, i) => (
            <span key={i} style={{ color: COLORS[i] }}>
              <b>{i ? "B" : "A"}</b>
              {s?.driver.code}{page === "Track Replay" && fullRace ? "" : ` / L${s?.lap.number}`}
            </span>
          ))}
        </div>
      </div>
      {page === "Track Replay" && (
        <div className="race-mode-switch" aria-label="Replay mode">
          <button className={fullRace ? "active" : ""} aria-pressed={fullRace} onClick={() => { setPlaying(false); setFullRace(true); }}>Full race · all laps</button>
          <button className={!fullRace ? "active" : ""} aria-pressed={!fullRace} onClick={() => setFullRace(false)}>Selected lap comparison</button>
        </div>
      )}
      {page === "Track Replay" && fullRace ? (
        <FullRace comparison={comparison} selections={selections} round={round} />
      ) : page === "Mathematics" ? (
        <Mathematics
          analysis={analysis}
          settings={settings}
          setSettings={setSettings}
          loading={analysisBusy}
          error={analysisError}
          selections={selections}
          maxDistance={maxDistance}
          onRetry={() => setRetry((r) => r + 1)}
        />
      ) : (
        <>
          <div
            className={`replay-layout ${page === "Telemetry" ? "telemetry-map-layout" : ""}`}
          >
            <AngularPanel className="circuit-panel">
              <div className="panel-title">
                <h3>{comparison.event.toUpperCase()}</h3>
                <span>
                  <Maximize2 size={12} /> ACTUAL LAP GEOMETRY
                </span>
              </div>
              <TrackMap
                comparison={comparison}
                selections={selections}
                time={time}
                section={range}
                cursor={cursor}
              />
              <PlaybackControls
                time={time}
                duration={duration}
                playing={playing}
                speed={speed}
                setTime={setTime}
                setPlaying={setPlaying}
                setSpeed={setSpeed}
              />
              <ReplayAudio comparison={comparison} time={time} playing={playing} />
            </AngularPanel>
            <div className="replay-sidebar">
              <div className="compact-cards">
                {selections.map(
                  (s, i) =>
                    s && (
                      <DriverCard
                        key={s.driver.id}
                        driver={s.driver}
                        lap={s.lap}
                        slot={i}
                        compact
                      />
                    ),
                )}
              </div>
              <AngularPanel className="delta-panel">
                <span className="eyebrow">DISTANCE-ALIGNED / B − A</span>
                <strong>
                  {delta === null
                    ? "—"
                    : `${delta >= 0 ? "+" : ""}${numeric(delta, 3)}`}
                  <small> s</small>
                </strong>
                <p>
                  Estimated comparison delta
                  <br />
                  Positive: Driver B takes longer
                </p>
              </AngularPanel>
            </div>
          </div>
          <TimingStrip
            comparison={comparison}
            selections={selections}
            time={time}
          />
          <LiveTelemetry
            comparison={comparison}
            selections={selections}
            time={time}
          />
          <div className="section-heading">
            <div>
              <span className="eyebrow">THE DIFFERENCE IS IN THE DETAILS</span>
              <h2>Two laps. One shared distance.</h2>
            </div>
            <button className="text-button" onClick={() => setRange(null)}>
              Reset chart zoom
            </button>
          </div>
          <p className="chart-instructions">
            Drag to zoom any chart; all distance axes follow. Hover highlights
            the circuit. Click a sample to seek the replay.
          </p>
          {analysisBusy && (
            <DataStatus loading>
              Calculating the shared distance alignment…
            </DataStatus>
          )}
          {analysisError && (
            <DataStatus
              error={analysisError}
              onRetry={() => setRetry((r) => r + 1)}
            />
          )}
          {charts}
        </>
      )}
      <div className="provenance">
        <span className="eyebrow">READ THE DATA CORRECTLY</span>
        {comparison.warnings.map((w) => (
          <p key={w}>{w}</p>
        ))}
      </div>
    </div>
  );
}
