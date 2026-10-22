export const COLORS = ["#ff646e", "#69d6df"];
export function lapTime(time: number | null | undefined) {
  if (time == null || !Number.isFinite(time)) return "—";
  const ms = Math.round(time * 1000);
  return `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, "0")}.${String(ms % 1000).padStart(3, "0")}`;
}
export function seconds(time: number | null | undefined) {
  return time == null ? "—" : time.toFixed(3);
}
export function numeric(value: number | null | undefined, digits = 0) {
  return value == null || !Number.isFinite(value) ? "—" : value.toFixed(digits);
}
export function sampleAt(times: number[], t: number) {
  let low = 0,
    high = times.length - 1;
  while (low < high) {
    const mid = Math.ceil((low + high) / 2);
    if (times[mid] <= t) low = mid;
    else high = mid - 1;
  }
  return low;
}
export function interpolate(
  times: number[],
  values: (number | null)[],
  t: number,
  discrete = false,
): number | null {
  const i = sampleAt(times, t),
    a = values[i],
    b = values[i + 1];
  if (a == null) return null;
  if (discrete || b == null || i === times.length - 1) return a;
  const f = Math.max(
    0,
    Math.min(1, (t - times[i]) / (times[i + 1] - times[i])),
  );
  return a + (b - a) * f;
}
// FastF1 CountryCode uses IOC-style three-letter codes. Flags are country symbols, not portrait assets.
const COUNTRIES: Record<string, string> = {
  GBR: "GB",
  NED: "NL",
  MON: "MC",
  MCO: "MC",
  AUS: "AU",
  ESP: "ES",
  FRA: "FR",
  GER: "DE",
  DEU: "DE",
  FIN: "FI",
  DEN: "DK",
  DNK: "DK",
  CAN: "CA",
  JPN: "JP",
  CHN: "CN",
  THA: "TH",
  MEX: "MX",
  NZL: "NZ",
  USA: "US",
  BRA: "BR",
  ARG: "AR",
  ITA: "IT",
  POL: "PL",
  RUS: "RU",
};
export function flag(code: string | null) {
  const iso = code ? COUNTRIES[code] : null;
  return iso
    ? [...iso]
        .map((c) => String.fromCodePoint(127397 + c.charCodeAt(0)))
        .join("")
    : null;
}
