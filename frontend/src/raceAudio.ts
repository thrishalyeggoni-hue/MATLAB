import type { Trace } from "./types";
import { interpolate } from "./format.ts";

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
export function audioTargets(trace: Trace, time: number) {
  const s = trace.samples;
  const available = time >= s.time[0] && time <= s.time.at(-1)!
    && !trace.gaps?.some(([from, to]) => time > from && time < to);
  const rpm = interpolate(s.time, s.rpm, time);
  const throttle = interpolate(s.time, s.throttle, time);
  const speed = interpolate(s.time, s.speed, time);
  const brake = interpolate(s.time, s.brake, time, true);
  const gear = interpolate(s.time, s.gear, time, true);
  const active = available && rpm != null && throttle != null && speed != null;
  const braking = brake != null && brake > 0;
  return {
    active, rate: clamp((rpm || 0) / 11000, .45, 1.45), gear,
    engine: active ? (.045 + .22 * clamp(throttle! / 100, 0, 1)) * (braking ? .55 : 1) : 0,
    brake: active && braking && speed! > 30 ? .035 * clamp(speed! / 200, 0, 1) : 0,
    wind: active ? .018 * clamp(speed! / 300, 0, 1) : 0,
    brakeFrequency: 1100 + clamp(speed || 0, 0, 400) * 3,
  };
}

/** Only continuous playback crossing the classified winner's finish triggers a cue. */
export class WinnerCue {
  previousTime = 0;
  previousPlaying = false;
  previousSeek = -1;
  announced = false;
  update(time: number, playing: boolean, seek: number, finish: number) {
    if (seek !== this.previousSeek) {
      this.previousSeek = seek;
      this.previousTime = time;
      this.previousPlaying = playing;
      if (time < finish) this.announced = false;
      return false;
    }
    const crossed = this.previousPlaying && this.previousTime < finish && time >= finish && !this.announced;
    this.previousTime = time;
    this.previousPlaying = playing;
    if (crossed) this.announced = true;
    return crossed;
  }
}
