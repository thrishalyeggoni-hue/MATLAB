export interface Lap {
  number: number;
  time: number | null;
  sectors: (number | null)[];
  compound: string | null;
  tyre_life: number | null;
  eligible: boolean;
  reason: string | null;
}
export interface Driver {
  id: string;
  number: string;
  name: string;
  first_name: string;
  last_name: string;
  code: string;
  team: string;
  color: string;
  country: string | null;
  portrait: string | null;
  laps: Lap[];
  best_lap: Lap | null;
  unavailable_reason: string | null;
}
export interface Event {
  round: number;
  name: string;
  country: string;
  location: string;
  date: string;
  supported: boolean;
  sessions: { name: string; date: string; completed: boolean }[];
}
export interface Session {
  year: number;
  round: number;
  session: string;
  event: string;
  country: string;
  location: string;
  date: string;
  drivers: Driver[];
  timing_available: boolean;
  availability: string | null;
  source: string;
  portrait_note: string;
}
export interface Selection {
  driver: Driver;
  lap: Lap;
}
export interface Samples {
  time: number[];
  distance: (number | null)[];
  speed: (number | null)[];
  throttle: (number | null)[];
  brake: (number | null)[];
  gear: (number | null)[];
  rpm: (number | null)[];
  x: (number | null)[];
  y: (number | null)[];
}
export interface Trace {
  driver: string;
  lap: Lap;
  samples: Samples;
  gaps?: [number, number][];
}
export interface RaceReplay extends Comparison {
  winner: { number: string; name: string; team: string; finish_time: number; source: string } | null;
  duration: number;
  total_laps: number;
  origin: string;
  participants: { driver: Driver; laps: (Lap & { start: number | null; end: number | null })[]; end: number; last_lap: number }[];
}
export interface Comparison {
  traces: Trace[];
  corners: { x: number; y: number; number: string; distance: number | null }[];
  rotation: number;
  event: string;
  session: string;
  year: number;
  warnings: string[];
  source: string;
}
export interface Analysis {
  distance: number[];
  delta: number[];
  features: string[];
  scaled: boolean;
  means: number[];
  scales: number[];
  sample_count: number;
  explained_variance: number[];
  components: number[][];
  scores: number[][][];
  covariance: number[][];
  eigenvalues: number[];
  eigenvectors: number[][];
  singular_values: number[];
  svd_relative_error: number;
  fit: {
    degree: number;
    distance: number[];
    origin: number;
    span: number;
    drivers: {
      coefficients: number[];
      observed: number[];
      fitted: number[];
      rmse: number;
      r_squared: number | null;
    }[];
  };
}
export type Page =
  "Drivers" | "Track Replay" | "Telemetry" | "Mathematics" | "Methods";
