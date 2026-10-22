import {
  useCallback,
  useEffect,
  useRef,
  useState,
  lazy,
  Suspense,
} from "react";
import {
  ArrowUpRight,
  ChevronDown,
  ChevronRight,
  Flag,
  Menu,
  Radio,
  X,
} from "lucide-react";
import type {
  Driver,
  Event,
  Lap,
  Session,
  Selection,
  Comparison,
  Page,
} from "./types";
import { loadJob, request } from "./api";
import {
  AngularPanel,
  DataStatus,
  DriverCard,
  LapPicker,
  SelectionBar,
} from "./components";
import "./App.css";
import PhotoCredits from "./PhotoCredits";
const Workspace = lazy(() => import("./Workspace"));
const PAGES: Page[] = [
  "Drivers",
  "Track Replay",
  "Telemetry",
  "Mathematics",
  "Methods",
];

function App() {
  const [page, setPage] = useState<Page>("Drivers"),
    [mobileNav, setMobileNav] = useState(false);
  const [provider, setProvider] = useState<"openf1" | "fastf1">("openf1");
  const [seasons, setSeasons] = useState<number[]>([2024]),
    [year, setYear] = useState(2024);
  const [events, setEvents] = useState<Event[]>([]),
    [round, setRound] = useState<number | null>(null),
    [sessionName, setSessionName] = useState("");
  const [scheduleBusy, setScheduleBusy] = useState(true),
    [scheduleError, setScheduleError] = useState<string | null>(null),
    [scheduleRetry, setScheduleRetry] = useState(0);
  const [session, setSession] = useState<Session | null>(null),
    [sessionBusy, setSessionBusy] = useState(false),
    [sessionError, setSessionError] = useState<string | null>(null),
    [sessionRetry, setSessionRetry] = useState(0);
  const [selections, setSelections] = useState<(Selection | null)[]>([
      null,
      null,
    ]),
    [active, setActive] = useState(0),
    [picker, setPicker] = useState<{ driver: Driver; slot: number } | null>(
      null,
    );
  const [comparison, setComparison] = useState<Comparison | null>(null),
    [comparisonId, setComparisonId] = useState(""),
    [compareBusy, setCompareBusy] = useState(false),
    [compareError, setCompareError] = useState<string | null>(null);
  const [notice, setNotice] = useState(""),
    [search, setSearch] = useState("");
  const compareAbort = useRef<AbortController | null>(null);
  const event = events.find((e) => e.round === round);
  const resetComparison = useCallback(() => {
    compareAbort.current?.abort();
    setComparison(null);
    setComparisonId("");
    setCompareError(null);
    setCompareBusy(false);
  }, []);
  const resetSelections = useCallback(() => {
    resetComparison();
    setSelections([null, null]);
    setActive(0);
    setPicker(null);
    setSearch("");
  }, [resetComparison]);
  useEffect(() => {
    const controller = new AbortController();
    request<{ seasons: number[] }>("/api/seasons", undefined, controller.signal)
      .then((r) => setSeasons(r.seasons))
      .catch(() => {});
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setScheduleBusy(true);
    setScheduleError(null);
    setEvents([]);
    setRound(null);
    setSessionName("");
    setSession(null);
    resetSelections();
    loadJob<Event[]>(`/api/schedule/${year}`, undefined, controller.signal)
      .then(({ data }) => {
        setEvents(data);
        const first = data.find(
          (e) => e.supported && e.sessions.some((s) => s.completed),
        );
        if (first) {
          setRound(first.round);
          setSessionName(
            first.sessions.find((s) => s.name === "Qualifying" && s.completed)
              ?.name ||
              first.sessions.find((s) => s.completed)?.name ||
              "",
          );
        }
      })
      .catch((e) => {
        if (e.name !== "AbortError") setScheduleError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setScheduleBusy(false);
      });
    return () => controller.abort();
  }, [year, scheduleRetry, resetSelections]);
  useEffect(() => {
    const controller = new AbortController();
    resetSelections();
    setSession(null);
    setSessionError(null);
    if (round === null || !sessionName) {
      setSessionBusy(false);
      return () => controller.abort();
    }
    setSessionBusy(true);
    loadJob<Session>(
      "/api/session",
      {
        year,
        round,
        session: sessionName,
        refresh: sessionRetry > 0,
        provider,
      },
      controller.signal,
    )
      .then(({ data }) => setSession(data))
      .catch((e) => {
        if (e.name !== "AbortError") setSessionError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setSessionBusy(false);
      });
    return () => controller.abort();
  }, [year, round, sessionName, provider, sessionRetry, resetSelections]);
  useEffect(() => () => compareAbort.current?.abort(), []);
  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [page]);
  useEffect(() => {
    if (!picker) return;
    const close = (e: KeyboardEvent) => {
      if (e.key === "Escape") setPicker(null);
    };
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [picker]);
  function chooseDriver(driver: Driver) {
    if (!driver.best_lap) return;
    const other = 1 - active;
    if (selections[other]?.driver.id === driver.id) {
      setNotice(
        `${driver.name} is already in Driver ${other === 0 ? "A" : "B"}. Choose another driver or swap the slots.`,
      );
      return;
    }
    resetComparison();
    const next = [...selections];
    next[active] = { driver, lap: driver.best_lap };
    setSelections(next);
    setNotice("");
    if (!next[other]) setActive(other);
  }
  function chooseLap(lap: Lap) {
    if (!picker) return;
    resetComparison();
    const next = [...selections];
    next[picker.slot] = { driver: picker.driver, lap };
    setSelections(next);
    setPicker(null);
    if (!next[1 - picker.slot]) setActive(1 - picker.slot);
  }
  function openPicker(driver: Driver, slot: number) {
    const existing = selections.findIndex((s) => s?.driver.id === driver.id);
    if (existing >= 0) {
      setPicker({ driver, slot: existing });
      return;
    }
    if (selections[1 - slot]?.driver.id === driver.id) return;
    setPicker({ driver, slot });
  }
  async function compare() {
    const [a, b] = selections;
    if (!a || !b) return;
    compareAbort.current?.abort();
    const controller = new AbortController();
    compareAbort.current = controller;
    setCompareBusy(true);
    setCompareError(null);
    try {
      const result = await loadJob<Comparison>(
        "/api/compare",
        {
          year,
          round,
          session: sessionName,
          provider,
          driver_a: a.driver.id,
          lap_a: a.lap.number,
          driver_b: b.driver.id,
          lap_b: b.lap.number,
        },
        controller.signal,
      );
      setComparison(result.data);
      setComparisonId(result.id);
      setPage("Track Replay");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      if (e instanceof Error && e.name !== "AbortError")
        setCompareError(e.message);
    } finally {
      if (!controller.signal.aborted) setCompareBusy(false);
    }
  }
  function changeEvent(value: number) {
    const next = events.find((e) => e.round === value);
    setRound(value);
    setSessionName(
      next?.sessions.find((s) => s.name === "Qualifying")?.name ||
        next?.sessions[0]?.name ||
        "",
    );
  }
  const filtered =
    session?.drivers.filter((d) =>
      `${d.name} ${d.team} ${d.number}`
        .toLowerCase()
        .includes(search.toLowerCase()),
    ) || [];
  return (
    <div className="app-shell">
      <header className="site-header">
        <a
          className="wordmark"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setPage("Drivers");
          }}
          aria-label="F1 Driver DNA home"
        >
          <span className="logo-speed" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          <span>
            F1 DRIVER <b>DNA</b>
            <small>THE SCIENCE BEHIND THE SPEED</small>
          </span>
        </a>
        <nav aria-label="Main navigation" className={mobileNav ? "open" : ""}>
          {PAGES.map((p) => (
            <button
              key={p}
              onClick={() => {
                setPage(p);
                setMobileNav(false);
              }}
              className={page === p ? "current" : ""}
            >
              {p}
            </button>
          ))}
        </nav>
        <div className="header-data">
          <span className="status-dot" /> RECORDED DATA{" "}
          <span className="header-divider" /> {provider.toUpperCase()}
        </div>
        <button
          className="mobile-menu icon-button"
          onClick={() => setMobileNav(!mobileNav)}
          aria-label="Toggle navigation"
        >
          {mobileNav ? <X /> : <Menu />}
        </button>
      </header>
      <main>
        {page === "Drivers" ? (
          <>
            <div className="hero">
              <div>
                <div className="eyebrow">
                  <span className="coral-rule" /> MOTORSPORT. MEET MATHEMATICS.
                </div>
                <h1>
                  CHOOSE YOUR
                  <br />
                  <span>DRIVERS</span>
                  <span className="hero-period">.</span>
                </h1>
                <p>
                  Select two drivers. Replay their laps. Discover the
                  differences.
                </p>
              </div>
              <div className="hero-aside">
                <div className="dna-decoration" aria-hidden="true">
                  DNA<span>01 — 02</span>
                </div>
                <span className="outlined-label">
                  <Radio size={13} /> REAL LAPS. REAL DIFFERENCES.
                </span>
              </div>
            </div>
            <div className="source-selector">
              <span className="eyebrow">YOUR DATA / YOUR CHOICE</span>
              <label>
                DATA SOURCE
                <select
                  value={provider}
                  onChange={(e) =>
                    setProvider(e.target.value as "openf1" | "fastf1")
                  }
                >
                  <option value="openf1">
                    FastF1 drivers + OpenF1 telemetry (2023+)
                  </option>
                  <option value="fastf1">
                    FastF1 · cached or authenticated archive
                  </option>
                </select>
              </label>
              <span className="source-explanation">
                {provider === "openf1"
                  ? "FastF1 driver identities. OpenF1 timing and telemetry. No subscription required."
                  : "Archive downloads require F1 TV authentication."}
              </span>
            </div>
            <AngularPanel className="event-selector">
              <div className="selector-intro">
                <Flag size={21} />
                <div>
                  <span className="eyebrow">SET THE STAGE</span>
                  <strong>Every circuit tells a story.</strong>
                </div>
              </div>
              <label>
                <span>01 / SEASON</span>
                <div className="select-wrap">
                  <select
                    value={year}
                    onChange={(e) => setYear(Number(e.target.value))}
                  >
                    {seasons.map((y) => (
                      <option key={y}>{y}</option>
                    ))}
                  </select>
                  <ChevronDown size={14} />
                </div>
              </label>
              <label className="gp-select">
                <span>02 / GRAND PRIX</span>
                <div className="select-wrap">
                  <select
                    aria-label="Grand Prix"
                    value={round ?? ""}
                    disabled={scheduleBusy || !events.length}
                    onChange={(e) => changeEvent(Number(e.target.value))}
                  >
                    {!events.length && (
                      <option value="">
                        {scheduleBusy
                          ? "Loading calendar…"
                          : "Calendar unavailable"}
                      </option>
                    )}
                    {events.map((e) => (
                      <option key={e.round} value={e.round}>
                        {e.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDown size={14} />
                </div>
              </label>
              <label>
                <span>03 / SESSION</span>
                <div className="select-wrap">
                  <select
                    aria-label="Session"
                    value={sessionName}
                    disabled={!event}
                    onChange={(e) => setSessionName(e.target.value)}
                  >
                    {!event && <option value="">Choose an event</option>}
                    {event?.sessions.map((s) => (
                      <option key={s.name} value={s.name}>
                        {s.name}
                        {!s.completed ? " · scheduled" : ""}
                      </option>
                    ))}
                  </select>
                  <ChevronDown size={14} />
                </div>
              </label>
            </AngularPanel>
            {scheduleError && (
              <DataStatus
                error={scheduleError}
                onRetry={() => setScheduleRetry((r) => r + 1)}
              />
            )}
            <div className="session-meta">
              <span>
                {event ? (
                  <>
                    <span className="status-dot" />
                    {event.location.toUpperCase()},{" "}
                    {event.country.toUpperCase()} <i /> {event.date} <i />
                    {sessionName.toUpperCase()}
                  </>
                ) : (
                  "SELECT A RECORDED SESSION"
                )}
              </span>
              <span>
                {session
                  ? `${session.drivers.length} PARTICIPANTS / ${provider.toUpperCase()}`
                  : `${provider.toUpperCase()} SESSION ARCHIVE`}{" "}
                <ArrowUpRight size={12} />
              </span>
            </div>
            <SelectionBar
              selections={selections}
              active={active}
              setActive={setActive}
              remove={(i) => {
                resetComparison();
                setSelections((s) => s.map((v, j) => (j === i ? null : v)));
                setActive(i);
              }}
              lap={(i) => {
                const s = selections[i];
                if (s) setPicker({ driver: s.driver, slot: i });
              }}
              swap={() => {
                resetComparison();
                setSelections(([a, b]) => [b, a]);
                setActive((i) => 1 - i);
              }}
              compare={compare}
              loading={compareBusy}
            />
            {notice && (
              <div className="notice" role="status">
                {notice}
              </div>
            )}
            {compareBusy && (
              <DataStatus loading>
                Downloading car and position telemetry for your selected
                session. Cached data will make the next comparison faster.
              </DataStatus>
            )}
            {compareError && (
              <DataStatus error={compareError} onRetry={compare} />
            )}
            <div className="section-heading">
              <div>
                <span className="eyebrow">THE GRID</span>
                <h2>
                  {session
                    ? `${session.drivers.length} drivers. Your comparison.`
                    : "Every driver. A different signature."}
                </h2>
              </div>
              <label className="search">
                <span className="sr-only">Search drivers or teams</span>
                <input
                  placeholder="Search driver or team"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  disabled={!session}
                />
                <span>⌕</span>
              </label>
            </div>
            {session && !session.timing_available && (
              <DataStatus
                error={session.availability}
                onRetry={() => setSessionRetry((r) => r + 1)}
              />
            )}
            {sessionBusy || scheduleBusy ? (
              <>
                <DataStatus loading>
                  Loading actual session participants and lap timing. First
                  downloads can take a minute; subsequent views use the local
                  cache.
                </DataStatus>
                <div className="driver-grid" aria-hidden="true">
                  {Array.from({ length: 10 }, (_, i) => (
                    <div className="skeleton-card" key={i}>
                      <div />
                      <span />
                      <span />
                    </div>
                  ))}
                </div>
              </>
            ) : sessionError ? (
              <DataStatus
                error={sessionError}
                onRetry={() => setSessionRetry((r) => r + 1)}
              />
            ) : session ? (
              <>
                <div className="driver-grid">
                  {filtered.map((d) => {
                    const slot = selections.findIndex(
                      (s) => s?.driver.id === d.id,
                    );
                    return (
                      <DriverCard
                        key={d.id}
                        driver={d}
                        slot={slot >= 0 ? slot : undefined}
                        lap={slot >= 0 ? selections[slot]?.lap : null}
                        onSelect={() => chooseDriver(d)}
                        onLap={
                          d.laps.length
                            ? () => openPicker(d, active)
                            : undefined
                        }
                      />
                    );
                  })}
                </div>
                {!filtered.length && (
                  <DataStatus>No drivers match your search.</DataStatus>
                )}
                <div className="grid-footnote">
                  <span>
                    <span className="coral-dot" /> DEFAULT: FASTEST ELIGIBLE LAP
                  </span>
                  <p>
                    Numbers are racing numbers, not ratings. Source:{" "}
                    {session.source}. Grey accents indicate missing team
                    colours. Driver photography: Wikimedia Commons. Full credits
                    in Methods; initials are retained when a portrait is
                    unavailable.
                  </p>
                </div>
              </>
            ) : (
              <DataStatus>Choose an available session above.</DataStatus>
            )}
            <div className="feature-strip">
              <div>
                <b>01</b>
                <span>
                  <strong>CHOOSE YOUR PAIR</strong>
                  <small>Real participants. Their actual laps.</small>
                </span>
              </div>
              <div>
                <b>02</b>
                <span>
                  <strong>FOLLOW EVERY METRE</strong>
                  <small>Synchronized ghost lap replay.</small>
                </span>
              </div>
              <div>
                <b>03</b>
                <span>
                  <strong>FIND THE DIFFERENCE</strong>
                  <small>Telemetry meets linear algebra.</small>
                </span>
              </div>
            </div>
          </>
        ) : page === "Methods" ? (
          <Methods />
        ) : (
          <Suspense
            fallback={
              <DataStatus loading>Loading analysis workspace…</DataStatus>
            }
          >
            <Workspace
              round={round!}
              page={page}
              comparison={comparison}
              comparisonId={comparisonId}
              selections={selections}
              onSelect={() => setPage("Drivers")}
            />
          </Suspense>
        )}
      </main>
      <footer>
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setPage("Drivers");
          }}
        >
          F1 DRIVER <b>DNA</b>
        </a>
        <span>
          RECORDED DATA. DOCUMENTED CALCULATIONS. NO INVENTED RATINGS.
        </span>
        <button onClick={() => setPage("Methods")}>
          Data & methods <ChevronRight size={12} />
        </button>
      </footer>
      {picker && (
        <LapPicker
          driver={picker.driver}
          current={
            selections[picker.slot]?.driver.id === picker.driver.id
              ? selections[picker.slot]?.lap.number
              : undefined
          }
          onChoose={chooseLap}
          provider={provider}
          onClose={() => setPicker(null)}
        />
      )}
    </div>
  );
}
function Methods() {
  return (
    <div className="methods-page">
      <div className="eyebrow">TRANSPARENCY / DATA & METHODS</div>
      <h1>
        BEHIND THE
        <br />
        <span>DIFFERENCE.</span>
      </h1>
      <p className="page-lead">
        A lap is a measurement. A model is an interpretation. Here is where each
        number comes from.
      </p>
      <AngularPanel className="auth-instructions">
        <span className="eyebrow">ARCHIVE AUTHENTICATION / LOCAL SETUP</span>
        <h2>Connect your own F1 TV account.</h2>
        <p>
          The OpenF1 source is available without a subscription for 2023 onward.
          For FastF1 archive downloads, F1 now requires an F1 TV Access
          subscription or higher. The app uses FastF1 3.9.0a0, the maintainer’s
          authentication preview. Sign in from your local terminal, then click
          Retry in the driver grid. Credentials are handled by FastF1; never
          paste them into this site or chat.
        </p>
        <code>
          .venv/bin/python -m fastf1 auth f1tv --authenticate --method browser
        </code>
        <p>
          The browser method requires the official FastF1 Companion extension.
          FastF1 stores its token locally outside this project. Cached sessions
          remain usable when their data is present.
        </p>
        <a
          href="https://github.com/theOehrly/Fast-F1/issues/978"
          target="_blank"
          rel="noreferrer"
        >
          Read the maintainer’s archive access update ↗
        </a>
      </AngularPanel>
      <div className="methods-grid">
        {[
          [
            "01",
            "Recorded, never invented",
            "Calendars come from FastF1. The default combines FastF1 driver names, abbreviations and teams with OpenF1 participants, team colours, lap times, tyres, sectors and telemetry for the exact selected session. Identities must match both racing number and abbreviation. Unmatched identities remain from OpenF1, and the source note reports the match count or unavailable FastF1 metadata. OpenF1 covers 2023 onward; nothing is silently substituted. Changing the session clears all incompatible selections. Missing values stay unavailable.",
          ],
          [
            "02",
            "Which laps qualify?",
            "FastF1 mode requires recorded timing, IsAccurate, no deletion, no pit entry/exit, and no generated lap. OpenF1 mode requires a start timestamp, a timed lap with all three sectors agreeing within 0.05 seconds, no pit-out flag or recorded pit-lane segment, and no matching race-control lap-time deletion. OpenF1 does not supply FastF1’s IsAccurate flag. Race-control reinstatement reverses a matched deletion. The default is the fastest eligible lap for each driver. Eligibility does not guarantee telemetry coverage.",
          ],
          [
            "03",
            "Ghost laps, one shared start",
            "Both laps start together at elapsed time zero. Markers follow recorded timestamps and position coordinates, with client-side interpolation between samples. Discrete brake and gear values use the preceding sample. This is not an actual race-position replay.",
          ],
          [
            "04",
            "Timing versus interpolation",
            "Lap and sector times are official recorded session values. Running channels, track positions, integrated distance, and distance-aligned time deltas are estimates. FastF1 merges car and position streams; OpenF1 mode merges those streams by recorded UTC timestamps. Both can contain interpolated values. OpenF1 lap-start timestamps and locations are approximate; its distance is estimated by trapezoidal integration of speed. Timing sectors use recorded sector durations, never equal thirds of track distance.",
          ],
          [
            "05",
            "Shared measurements, shared model",
            "Both laps are aligned to 400 equally spaced samples on their overlapping recorded distance. Speed, throttle and RPM are interpolated; gear and brake use preceding samples. Complete rows are jointly centred, optionally scaled to unit variance, and fitted in one PCA model. Covariance eigenvalues and SVD use this same matrix.",
          ],
          [
            "06",
            "What the mathematics can tell you",
            "PCA describes variation in the selected measurements. It does not identify personality or prove driver ability. Polynomial curve fits summarize speed over a chosen distance interval; the fit is descriptive and does not model vehicle dynamics. Car setup, tyres, fuel, traffic, and conditions are confounding factors.",
          ],
          [
            "07",
            "Circuit and image provenance",
            "Circuit outlines come from selected-lap X/Y position telemetry. Corner annotations, when available in FastF1 mode, come from MultiViewer circuit information; OpenF1 mode shows no invented corner annotations. We do not substitute another circuit. Real, individually credited Wikimedia Commons photographs appear on the driver cards, with initials retained for unavailable images. Portrait years may differ from the selected session; the photographer, source, and licence are listed below. Country flags are shown only for recognized recorded country codes.",
          ],
          [
            "08",
            "Coverage, caching and independence",
            "FastF1 timing coverage begins in 2018 and can vary by session and channel. Downloads are cached locally in .cache/fastf1 or .cache/openf1. OpenF1’s free historical data is intended for personal education and research; its rate limits are respected by spacing and caching requests. Initial retrieval can take several minutes. This independent educational project is not affiliated with Formula 1, the FIA, EA Sports, or any team.",
          ],
        ].map(([n, title, body]) => (
          <AngularPanel key={n}>
            <span className="module-number">{n}</span>
            <h2>{title}</h2>
            <p>{body}</p>
          </AngularPanel>
        ))}
      </div>
      <PhotoCredits />
      <p className="source-links">
        Source documentation:{" "}
        <a href="https://openf1.org/docs/" target="_blank" rel="noreferrer">
          OpenF1
        </a>{" "}
        ·{" "}
        <a href="https://docs.fastf1.dev/" target="_blank" rel="noreferrer">
          FastF1
        </a>{" "}
        ·{" "}
        <a
          href="https://docs.fastf1.dev/time_explanation.html"
          target="_blank"
          rel="noreferrer"
        >
          Time definitions
        </a>{" "}
        ·{" "}
        <a
          href="https://docs.fastf1.dev/circuit_info.html"
          target="_blank"
          rel="noreferrer"
        >
          Circuit annotations
        </a>
      </p>
    </div>
  );
}
export default App;
