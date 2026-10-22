import { audioTargets } from "./raceAudio";
import type { Trace } from "./types";

type Voice = { source: AudioBufferSourceNode; engine: GainNode; filter: BiquadFilterNode;
  brake: GainNode; wind: GainNode; squeal: OscillatorNode; panner: StereoPannerNode; gear: number | null };

export class ReplaySound {
  context = new AudioContext();
  master = this.context.createGain();
  voices: Voice[] = [];
  closed = false;
  constructor() {
    const limiter = this.context.createDynamicsCompressor();
    limiter.threshold.value = -12; limiter.ratio.value = 12;
    this.master.gain.value = 0;
    this.master.connect(limiter); limiter.connect(this.context.destination);
  }
  async start() {
    // Called from a button gesture; never attempts autoplay.
    await this.context.resume();
    const response = await fetch('/audio/f1-brands-hatch.mp3');
    if (!response.ok) throw new Error('Engine recording could not load. Retry sound.');
    const recording = await this.context.decodeAudioData(await response.arrayBuffer());
    if (this.closed) return;
    const sampleRate = recording.sampleRate, fade = Math.round(sampleRate * .06), length = Math.round(sampleRate * 1.4);
    const loop = this.context.createBuffer(1, length - fade, sampleRate);
    const data = loop.getChannelData(0), original = recording.getChannelData(0), start = Math.round(5 * sampleRate);
    for (let i = 0; i < data.length; i++) {
      const old = original[start + fade + i] || 0;
      if (i < data.length - fade) data[i] = old;
      else {
        const n = i - (data.length - fade), mix = n / fade;
        data[i] = old * Math.cos(mix * Math.PI / 2) + (original[start + n] || 0) * Math.sin(mix * Math.PI / 2);
      }
    }
    const noise = this.context.createBuffer(1, sampleRate * 2, sampleRate);
    const noiseData = noise.getChannelData(0);
    for (let i = 0; i < noiseData.length; i++) noiseData[i] = Math.random() * 2 - 1;
    for (let i = 0; i < 2; i++) {
      const source = this.context.createBufferSource(), engine = this.context.createGain();
      const filter = this.context.createBiquadFilter(), panner = this.context.createStereoPanner();
      source.buffer = loop; source.loop = true; engine.gain.value = 0;
      filter.type = 'lowpass'; filter.frequency.value = 5000;
      panner.pan.value = i ? .55 : -.55;
      source.connect(filter); filter.connect(engine); engine.connect(panner); panner.connect(this.master);
      source.start(0, i * .3);
      const air = this.context.createBufferSource(), wind = this.context.createGain();
      const highpass = this.context.createBiquadFilter();
      air.buffer = noise; air.loop = true; highpass.type = 'highpass'; highpass.frequency.value = 1700;
      wind.gain.value = 0; air.connect(highpass); highpass.connect(wind); wind.connect(panner); air.start();
      const squeal = this.context.createOscillator(), brake = this.context.createGain();
      squeal.type = 'sine'; brake.gain.value = 0; squeal.connect(brake); brake.connect(panner); squeal.start();
      this.voices.push({ source, engine, filter, brake, wind, squeal, panner, gear: null });
    }
  }
  update(traces: Trace[], time: number, playing: boolean, volume: number, focus: string, duck: boolean) {
    if (this.closed || this.context.state !== 'running') return;
    const now = this.context.currentTime;
    this.master.gain.setTargetAtTime(playing ? volume * (duck ? .12 : 1) : 0, now, .04);
    this.voices.forEach((voice, i) => {
      const trace = traces[i];
      if (!trace) return;
      const value = audioTargets(trace, time);
      const audible = focus === 'both' || focus === String(i);
      voice.source.playbackRate.setTargetAtTime(value.rate, now, .07);
      voice.filter.frequency.setTargetAtTime(value.brake ? 2500 : 1800 + value.engine * 15000, now, .06);
      voice.engine.gain.setTargetAtTime(audible ? value.engine : 0, now, .045);
      voice.brake.gain.setTargetAtTime(audible ? value.brake : 0, now, .025);
      voice.squeal.frequency.setTargetAtTime(value.brakeFrequency, now, .06);
      voice.wind.gain.setTargetAtTime(audible ? value.wind : 0, now, .08);
      if (playing && audible && value.active && voice.gear != null && value.gear != null && value.gear !== voice.gear) {
        // Short torque-cut pulse for a recorded gear change, avoiding invented radio sounds.
        voice.engine.gain.cancelScheduledValues(now);
        voice.engine.gain.setValueAtTime(value.engine * .3, now);
        voice.engine.gain.setTargetAtTime(value.engine, now + .025, .025);
      }
      voice.gear = value.active ? value.gear : null;
    });
  }
  dispose() {
    this.closed = true;
    void this.context.close().catch(() => {});
  }
}
