const ALTERNATES = ["#ffffff", "#62f5a0", "#ff9a32", "#c69aff", "#55e5ef", "#172235", "#ff00ff", "#00ff00", "#000000"];

function distance(a: string, b: string) {
  const rgb = (hex: string) => [1, 3, 5].map((offset) => parseInt(hex.slice(offset, offset + 2), 16));
  const left = rgb(a), right = rgb(b);
  return Math.hypot(...left.map((channel, i) => channel - right[i]));
}

export const SECTOR_COLORS = ["#ff3038", "#168bff", "#ffdc24"];

/** Fix one fallback per car for the whole comparison, independent of either position. */
export function replayColors(teams: string[], nearbySectors: string[][], identities: string[]) {
  const options = teams.map((_, i) =>
    [...new Set([identities[i], ...ALTERNATES])].filter((candidate) =>
      [...SECTOR_COLORS, ...teams].every((color) => distance(candidate, color) >= 150)),
  );
  // Fallbacks contrast with every sector, both original liveries, and each other.
  const fallbackA = options[0].find((a) => options[1].some((b) => distance(a, b) >= 150));
  const fallbackB = options[1].find((b) => fallbackA && distance(fallbackA, b) >= 150);
  const fallbacks = [fallbackA, fallbackB];
  return teams.map((team, i) => {
    const clashesWithTrack = nearbySectors[i].some((sector) => distance(team, sector) < 150);
    // Keep A in its team colour when two original liveries are alike; B uses its fixed fallback.
    const clashesWithTeammate = i > 0 && distance(team, teams[0]) < 150;
    return clashesWithTrack || clashesWithTeammate ? fallbacks[i] || team : team;
  });
}
