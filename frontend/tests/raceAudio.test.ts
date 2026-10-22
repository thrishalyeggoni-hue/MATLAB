import test from 'node:test';
import assert from 'node:assert/strict';
import { audioTargets, WinnerCue } from '../src/raceAudio.ts';
import type { Trace } from '../src/types.ts';

const trace = { samples: { time:[0,1,2], speed:[180,220,100], throttle:[0,100,0],
  brake:[0,0,1], rpm:[6000,12000,8000], gear:[3,4,3], x:[0,1,2], y:[0,1,2], distance:[0,50,100] } } as Trace;

test('engine pitch and loudness follow RPM and throttle; braking adds an effect', () => {
  const low = audioTargets(trace, 0), high = audioTargets(trace, 1), braking = audioTargets(trace, 2);
  assert.ok(high.rate > low.rate);
  assert.ok(high.engine > low.engine);
  assert.equal(high.brake, 0);
  assert.ok(braking.brake > 0);
  assert.equal(high.gear, 4);
});
test('missing telemetry, stopped samples and outages remain silent', () => {
  for (const time of [-1, 3]) {
    const result = audioTargets(trace, time);
    assert.equal(result.active, false); assert.equal(result.engine, 0); assert.equal(result.brake, 0);
  }
  assert.equal(audioTargets({ ...trace, gaps:[[.5,1.5]] }, 1).engine, 0);
  assert.equal(audioTargets({ ...trace, samples:{ ...trace.samples, rpm:[null,null,null] } }, 1).engine, 0);
});
test('winner cue fires once at the finish, including the final stopped playback frame', () => {
  const cue = new WinnerCue();
  assert.equal(cue.update(98, true, 0, 100), false);
  assert.equal(cue.update(99, true, 0, 100), false);
  assert.equal(cue.update(100, false, 0, 100), true);
  assert.equal(cue.update(100, false, 0, 100), false);
});
test('seeking past the finish is silent; a new continuous pass can announce again', () => {
  const cue = new WinnerCue();
  cue.update(0, true, 0, 100);
  assert.equal(cue.update(101, true, 1, 100), false);
  assert.equal(cue.update(102, true, 1, 100), false);
  cue.update(98, false, 2, 100);
  cue.update(99, true, 2, 100);
  assert.equal(cue.update(101, true, 2, 100), true);
});
