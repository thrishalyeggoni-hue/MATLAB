import { useCallback, useEffect, useRef, useState } from "react";
import { Volume2, VolumeX } from "lucide-react";
import type { Comparison, RaceReplay } from "./types";
import { ReplaySound } from "./ReplaySound";
import { WinnerCue } from "./raceAudio";

export default function ReplayAudio({ comparison, time, playing, seekToken = 0, winner = null }: {
  comparison: Comparison; time: number; playing: boolean; seekToken?: number; winner?: RaceReplay["winner"];
}) {
  const engine = useRef<ReplaySound | null>(null);
  const utterance = useRef<SpeechSynthesisUtterance | null>(null);
  const cue = useRef(new WinnerCue());
  const mounted = useRef(true);
  const [enabled, setEnabled] = useState(false), [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null), [volume, setVolume] = useState(.3);
  const [focus, setFocus] = useState('both'), [voice, setVoice] = useState(true), [speaking, setSpeaking] = useState(false);
  const [visible, setVisible] = useState(!document.hidden);
  const speechAvailable = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
  useEffect(() => {
    mounted.current = true;
    const visibility = () => {
      setVisible(!document.hidden);
      if (document.hidden && utterance.current) { window.speechSynthesis.cancel(); utterance.current = null; setSpeaking(false); }
    };
    document.addEventListener('visibilitychange', visibility);
    return () => {
      mounted.current = false; document.removeEventListener('visibilitychange', visibility);
      engine.current?.dispose(); engine.current = null;
      if (utterance.current) window.speechSynthesis.cancel();
    };
  }, []);
  async function toggle() {
    if (enabled) {
      engine.current?.dispose(); engine.current = null; setEnabled(false);
      if (utterance.current) { window.speechSynthesis.cancel(); utterance.current = null; setSpeaking(false); }
      return;
    }
    setLoading(true); setError(null);
    try {
      const sound = new ReplaySound(); engine.current = sound;
      await sound.start();
      if (mounted.current && !sound.closed) setEnabled(true);
    } catch (e) {
      engine.current?.dispose(); engine.current = null;
      if (mounted.current) setError(e instanceof Error ? e.message : 'Sound is unavailable in this browser.');
    } finally { if (mounted.current) setLoading(false); }
  }
  const announce = useCallback(() => {
    if (!winner || !enabled || !voice || !speechAvailable || !visible) return;
    const speech = new SpeechSynthesisUtterance(`Chequered flag! ${winner.name} wins the ${comparison.event}. Congratulations to ${winner.name} and ${winner.team}.`);
    speech.lang = 'en-GB'; speech.rate = 1.05; speech.volume = volume;
    const english = window.speechSynthesis.getVoices().find((v) => v.lang === 'en-GB' && v.localService);
    if (english) speech.voice = english;
    speech.onstart = () => { if (mounted.current && utterance.current === speech) setSpeaking(true); };
    const done = () => { if (utterance.current === speech) { utterance.current = null; if (mounted.current) setSpeaking(false); } };
    speech.onend = done; speech.onerror = done;
    if (utterance.current) window.speechSynthesis.cancel();
    utterance.current = speech;
    window.speechSynthesis.speak(speech);
  }, [winner, enabled, voice, speechAvailable, visible, comparison.event, volume]);
  useEffect(() => {
    engine.current?.update(comparison.traces, time, enabled && playing && visible, volume, focus, speaking);
  }, [comparison, time, playing, enabled, volume, focus, speaking, visible]);
  useEffect(() => {
    if (!winner) return;
    if (cue.current.update(time, playing, seekToken, winner.finish_time)) announce();
  }, [time, playing, seekToken, winner, announce]);
  const finished = winner && time >= winner.finish_time;
  return <div className="replay-audio">
    <div className="replay-audio-controls">
      <button className={enabled ? 'sound-button enabled' : 'sound-button'} onClick={() => void toggle()} disabled={loading} aria-pressed={enabled}>
        {enabled ? <Volume2 size={15} /> : <VolumeX size={15} />}{loading ? 'Loading sound…' : enabled ? 'Sound on' : 'Enable sound'}
      </button>
      <label>VOLUME<input aria-label="Replay sound volume" type="range" min="0" max="1" step=".01" value={volume} onChange={(e) => setVolume(Number(e.target.value))} /></label>
      <label>LISTEN<select aria-label="Listen to driver" value={focus} onChange={(e) => setFocus(e.target.value)}><option value="both">Both cars</option><option value="0">Driver A</option><option value="1">Driver B</option></select></label>
      {comparison.session === 'Race' && <label className="winner-voice"><input type="checkbox" checked={voice} disabled={!speechAvailable} onChange={(e) => { setVoice(e.target.checked); if (!e.target.checked && utterance.current) { window.speechSynthesis.cancel(); utterance.current = null; setSpeaking(false); } }} />Winner announcement</label>}
    </div>
    <p className="audio-status" role="status">{error || (speaking ? 'Winner announcement playing' : enabled ? playing && visible ? 'Audio running · throttle, RPM, shifts and braking' : 'Sound ready · press Play to hear the cars' : 'Sound is off · enable to hear telemetry-reactive effects')}{!speechAvailable && comparison.session === 'Race' ? ' · Browser voice unavailable' : ''}</p>
    <details className="audio-credits"><summary>Sound source & credits</summary><p>Trackside F1 sample by <a href="https://freesound.org/people/LordFluffeh/sounds/478546/" target="_blank" rel="noreferrer">LordFluffeh</a>, <a href="https://creativecommons.org/publicdomain/zero/1.0/" target="_blank" rel="noreferrer">CC0</a>. Looped and adjusted using recorded telemetry; this is an illustrative soundscape, not the selected driver’s original race audio. Brake, wind and shift effects are synthesized. Winner commentary uses the browser’s announcer voice.</p></details>
    {finished && <div className="race-winner-banner" role="status"><span>🏁 CHEQUERED FLAG</span><strong>{winner.name} wins</strong><small>{winner.team} · {comparison.event}</small>{enabled && voice && speechAvailable && <button onClick={announce}>Replay winner announcement</button>}</div>}
  </div>;
}
