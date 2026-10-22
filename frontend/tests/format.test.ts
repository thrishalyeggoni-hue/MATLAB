import test from "node:test";
import assert from "node:assert/strict";
import { lapTime, interpolate, flag } from "../src/format.ts";
test("lap timing rounds across minute boundaries and preserves unavailable values", () => {
  assert.equal(lapTime(59.9996), "1:00.000");
  assert.equal(lapTime(null), "—");
  assert.equal(lapTime(89.165), "1:29.165");
});
test("recorded timestamps drive interpolation; discrete states use preceding sample", () => {
  assert.equal(interpolate([0, 1, 3], [100, 200, 300], 2), 250);
  assert.equal(interpolate([0, 1, 3], [1, 3, 4], 2, true), 3);
  assert.equal(interpolate([0, 1], [null, 4], 0.5), null);
  assert.equal(interpolate([0, 1], [1, 2], 10), 2);
});
test("flags only resolve known country codes", () => {
  assert.equal(flag("NED"), "🇳🇱");
  assert.equal(flag("???"), null);
  assert.equal(flag(null), null);
});
