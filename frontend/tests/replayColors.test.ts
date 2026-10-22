import test from "node:test";
import assert from "node:assert/strict";
import { replayColors, SECTOR_COLORS } from "../src/replayColors.ts";

const identities = ["#ff646e", "#69d6df"];
const colorGap = (a: string, b: string) => Math.hypot(...[1, 3, 5].map((offset) =>
  parseInt(a.slice(offset, offset + 2), 16) - parseInt(b.slice(offset, offset + 2), 16)));

test("every team and either driver slot adapts to matching sectors without matching its rival", () => {
  const teams = ["#e8002d", "#3671c6", "#27f4d2", "#ff8000", "#229971", "#b6babd", "#6692ff", "#64c4ff", "#52e252", "#0093cc", ...SECTOR_COLORS];
  for (const a of teams) for (const b of teams) {
    for (const sector of SECTOR_COLORS) {
      const colors = replayColors([a, b], [[sector], [sector]], identities);
      assert.ok(colorGap(colors[0], sector) >= 150, `A ${a} on ${sector}`);
      assert.ok(colorGap(colors[1], sector) >= 150, `B ${b} on ${sector}`);
      assert.ok(colorGap(colors[0], colors[1]) >= 150, `pair ${a}, ${b} on ${sector}`);
    }
  }
});
test("conflicting liveries change locally and restore after leaving the sector", () => {
  const teams = ["#e8002d", "#3671c6"];
  const changed = replayColors(teams, [["#ff3038"], ["#168bff"]], identities);
  assert.notEqual(changed[0], teams[0]);
  assert.notEqual(changed[1], teams[1]);
  assert.notEqual(changed[0], changed[1]);
  assert.deepEqual(replayColors(teams, [["#ffdc24"], ["#ffdc24"]], identities), teams);
});

test("same-team cars and sector-boundary overlaps remain visually distinct", () => {
  const result = replayColors(["#e8002d", "#e8002d"], [["#ff3038", "#168bff"], ["#ff3038"]], identities);
  assert.notEqual(result[0], result[1]);
  assert.notEqual(result[0], "#e8002d");
  assert.notEqual(result[1], "#e8002d");
});

test("blue car keeps one fallback as its rival changes sectors or crosses a boundary", () => {
  const teams = ["#e8002d", "#3671c6"];
  const blueOnly = replayColors(teams, [["#ffdc24"], ["#168bff"]], identities);
  const bothClashing = replayColors(teams, [["#ff3038"], ["#168bff"]], identities);
  const atBoundary = replayColors(teams, [["#ff3038"], ["#ff3038", "#168bff"]], identities);
  assert.equal(blueOnly[1], bothClashing[1]);
  assert.equal(blueOnly[1], atBoundary[1]);
  assert.notEqual(blueOnly[1], teams[1]);
  assert.notEqual(bothClashing[0], bothClashing[1]);
  const clear = replayColors(teams, [["#168bff"], ["#ffdc24"]], identities);
  assert.deepEqual(clear, teams);
});
