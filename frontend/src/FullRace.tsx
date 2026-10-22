import { memo, useCallback, useEffect, useRef, useState } from "react";
import type { Comparison, RaceReplay, Selection } from "./types";
import { loadJob } from "./api";
import { AngularPanel, DataStatus } from "./components";
import { COLORS, lapTime } from "./format";
import { PlaybackControls, TrackMap } from "./TrackReplay";
import ReplayAudio from "./ReplayAudio";

const RaceDriver = memo(function RaceDriver({ participant, index, currentLap, missing, ended, seek }: {
  participant: RaceReplay["participants"][number];
  index: number; currentLap: number | undefined; missing: boolean; ended: boolean; seek: (time: number) => void;
}) {
  const current = participant.laps.find((lap) => lap.number === currentLap);
  const fastest = participant.driver.best_lap;
  return <AngularPanel className="race-driver-panel">
    <div className="panel-title"><h3 style={{ color: COLORS[index] }}>{index ? "B" : "A"} / {participant.driver.code}</h3><span>{participant.last_lap} RECORDED LAPS</span></div>
    <p className="race-current-lap"><strong>{current ? `LAP ${current.number} / ${participant.last_lap}` : ended ? "DRIVER REPLAY ENDED" : "AWAITING RECORDED LAP"}</strong><small>{missing ? "Position telemetry unavailable at this time" : "Recorded race telemetry"}</small></p>
    <div className="race-fastest"><span>★ FASTEST ELIGIBLE LAP</span><strong>{fastest ? `L${fastest.number} · ${lapTime(fastest.time)}` : "Unavailable"}</strong></div>
    <div className="race-lap-list" aria-label={`${participant.driver.name} race laps`}>
      {participant.laps.map((lap) => <button key={lap.number} disabled={lap.start == null} onClick={() => { if (lap.start != null) seek(lap.start); }}
        className={`${lap.number === current?.number ? "current" : ""} ${lap.number === fastest?.number ? "fastest" : ""}`}
        aria-label={`${participant.driver.code} lap ${lap.number}, ${lapTime(lap.time)}${lap.number === fastest?.number ? ", fastest eligible lap" : ""}`}
        aria-current={lap.number === current?.number ? "step" : undefined}>
        <span>L{lap.number}</span><strong>{lapTime(lap.time)}</strong><small>{lap.start == null ? "NO START TIMESTAMP" : lap.number === fastest?.number ? "★ FASTEST" : !lap.eligible ? "PIT / UNTIMED / FLAGGED" : lap.compound || "RECORDED"}</small>
      </button>)}
    </div>
  </AngularPanel>;
});

export default function FullRace({ comparison, selections, round }: {
  comparison: Comparison; selections: (Selection | null)[]; round: number;
}) {
  const [race, setRace] = useState<RaceReplay | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const [time, setTime] = useState(0), [playing, setPlaying] = useState(false), [speed, setSpeed] = useState(4);
  const timeRef = useRef(0);
  const [seekToken, setSeekToken] = useState(0);
  const a = selections[0]?.driver.id, b = selections[1]?.driver.id;
  useEffect(() => {
    const controller = new AbortController();
    setRace(null); setError(null); setTime(0); setPlaying(false); timeRef.current = 0;
    loadJob<RaceReplay>("/api/race", { year: comparison.year, round, session: "Race", provider: "openf1", driver_a: a, driver_b: b }, controller.signal)
      .then(({ data }) => setRace(data))
      .catch((e) => { if (e.name !== "AbortError") setError(e.message); });
    return () => controller.abort();
  }, [comparison.year, round, a, b, retry]);
  const seek = useCallback((value: number) => { timeRef.current = value; setTime(value); setSeekToken((value) => value + 1); }, []);
  useEffect(() => {
    if (!playing || !race) return;
    let id = 0, previous = performance.now();
    const frame = (now: number) => {
      const next = Math.min(race.duration, timeRef.current + (now - previous) / 1000 * speed);
      previous = now; timeRef.current = next; setTime(next);
      if (next >= race.duration) { setPlaying(false); return; }
      id = requestAnimationFrame(frame);
    };
    id = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(id);
  }, [playing, race, speed]);
  useEffect(() => {
    if (!race) return;
    const handleKey = (event: KeyboardEvent) => {
      const element = event.target as HTMLElement;
      if (element.matches("input,select,textarea,button,a") || element.isContentEditable) return;
      if (event.code === "Space") { event.preventDefault(); if (timeRef.current >= race.duration) seek(0); setPlaying((value) => !value); }
      if (event.code === "ArrowRight") { event.preventDefault(); seek(Math.min(race.duration, timeRef.current + 10)); }
      if (event.code === "ArrowLeft") { event.preventDefault(); seek(Math.max(0, timeRef.current - 10)); }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [race, seek]);
  if (error) return <DataStatus error={error} onRetry={() => setRetry((r) => r + 1)} />;
  if (!race) return <DataStatus loading>Loading all race laps and both drivers’ full telemetry from OpenF1. First retrieval can take several minutes; downloads are cached locally.</DataStatus>;
  return <>
    <div className="race-summary"><strong>{race.total_laps} RACE LAPS</strong><span>OpenF1 archive · Shared recorded race clock · Click any lap to jump</span></div>
    <div className="full-race-layout">
      <AngularPanel className="circuit-panel">
        <div className="panel-title"><h3>{race.event.toUpperCase()}</h3><span>FULL RACE / {lapTime(time)}</span></div>
        <TrackMap comparison={comparison} markerComparison={race} selections={selections} time={time} section={null} cursor={null} />
        <PlaybackControls time={time} duration={race.duration} playing={playing} speed={speed} setTime={seek} setPlaying={setPlaying} setSpeed={setSpeed} speeds={[1, 2, 4, 8, 16, 32, 64]} />
        <ReplayAudio comparison={race} time={time} playing={playing} seekToken={seekToken} winner={race.winner} />
      </AngularPanel>
      <div className="full-race-sidebar">{race.participants.map((participant, index) => {
        const trace = race.traces[index];
        const current = participant.laps.find((lap) => lap.start != null && lap.end != null && time >= lap.start && time < lap.end);
        const missing = time < trace.samples.time[0] || time > trace.samples.time.at(-1)!
          || !!trace.gaps?.some(([from, to]) => time > from && time < to);
        return <RaceDriver key={participant.driver.id} participant={participant} index={index} currentLap={current?.number} missing={missing} ended={time >= participant.end} seek={seek} />;
      })}</div>
    </div>
    <div className="race-source-note"><strong>FULL RACE / OPENF1</strong>{race.warnings.map((warning) => <p key={warning}>{warning}</p>)}<p>Track sectors use the selected comparison lap’s timing geometry. The side panel highlights race laps, independently of the selected comparison laps.</p></div>
  </>;
}
