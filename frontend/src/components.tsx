import {
  Check,
  ChevronRight,
  CircleAlert,
  LoaderCircle,
  RefreshCw,
  X,
  ArrowLeftRight,
  Flag,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import type { Driver, Lap, Selection } from "./types";
import { COLORS, flag, lapTime } from "./format";
import { portraitFor } from "./portraitAssets";

export function AngularPanel({
  children,
  className = "",
  id,
}: {
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={`angular-panel ${className}`}>
      {children}
    </section>
  );
}
export function DataStatus({
  loading,
  error,
  onRetry,
  children,
}: {
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  children?: ReactNode;
}) {
  return (
    <div
      className={`data-status ${error ? "error" : ""}`}
      role={error ? "alert" : "status"}
    >
      {loading ? (
        <LoaderCircle className="spin" size={21} />
      ) : error ? (
        <CircleAlert size={22} />
      ) : (
        <Flag size={22} />
      )}
      <div>
        <strong>
          {error
            ? "DATA UNAVAILABLE"
            : loading
              ? "FETCHING RECORDED DATA"
              : "READY WHEN YOU ARE"}
        </strong>
        <p>{error || children || "Select a session to get started."}</p>
      </div>
      {error && onRetry && (
        <button className="button small" onClick={onRetry}>
          <RefreshCw size={14} />
          Retry
        </button>
      )}
    </div>
  );
}
export function DriverCard({
  driver,
  lap,
  slot,
  onSelect,
  onLap,
  compact = false,
}: {
  driver: Driver;
  lap?: Lap | null;
  slot?: number;
  onSelect?: () => void;
  onLap?: () => void;
  compact?: boolean;
}) {
  const selected = slot !== undefined;
  const portrait = portraitFor(driver);
  const [failedPortrait, setFailedPortrait] = useState<string | null>(null);
  const [loadedPortrait, setLoadedPortrait] = useState<string | null>(null);
  const photoVisible = portrait !== null && failedPortrait !== portrait.src;
  const photoLoaded = photoVisible && loadedPortrait === portrait.src;
  const actualLap = lap || driver.best_lap;
  const nationalFlag = flag(driver.country);
  return (
    <article
      className={`driver-card ${selected ? "selected" : ""} ${compact ? "compact" : ""}`}
      style={
        {
          "--team": driver.color,
          "--selection": selected ? COLORS[slot] : driver.color,
        } as CSSProperties
      }
    >
      <button
        className="card-face"
        aria-label={`${selected ? `Driver ${slot === 0 ? "A" : "B"}, ` : ""}${driver.name}, ${driver.team}${actualLap ? `, ${actualLap.number === driver.best_lap?.number ? "fastest eligible" : "selected"} lap ${lapTime(actualLap.time)}` : ", no eligible laps"}`}
        onClick={onSelect}
        disabled={!onSelect || !driver.best_lap}
        aria-pressed={onSelect ? selected : undefined}
      >
        <div className={`card-art ${photoLoaded ? "has-portrait" : ""}`}>
          <div className="card-diagonal" />
          <span className="racing-number">
            <small>DRIVER</small>
            {driver.number}
          </span>
          <span className="initials" aria-hidden="true">
            {driver.first_name.slice(0, 1)}
            {driver.last_name.slice(0, 1)}
          </span>
          {photoVisible && (
            <img
              key={portrait.src}
              className={`driver-portrait ${photoLoaded ? "loaded" : ""}`}
              src={portrait.src}
              alt={`Portrait of ${driver.name}`}
              loading="lazy"
              decoding="async"
              width="360"
              height="480"
              style={{ objectPosition: portrait.position }}
              onLoad={() => setLoadedPortrait(portrait.src)}
              onError={() => setFailedPortrait(portrait.src)}
            />
          )}
          <span className="portrait-caption">
            {photoLoaded
              ? `PHOTO ${portrait.photoYear} / COMMONS`
              : "PORTRAIT UNAVAILABLE"}
          </span>
          {selected && (
            <span className="selection-tag">
              <Check size={12} /> DRIVER {slot === 0 ? "A" : "B"}
            </span>
          )}
        </div>
        <div className="nameplate">
          <div className="driver-nationality">
            {nationalFlag ? (
              <span aria-label={driver.country || ""}>{nationalFlag}</span>
            ) : (
              <span className="country-code">{driver.country || "—"}</span>
            )}
            <span>{driver.code}</span>
          </div>
          <span className="driver-first">{driver.first_name}</span>
          <strong className="driver-last">{driver.last_name}</strong>
          <small className="team-name">{driver.team}</small>
        </div>
        <div className="card-stats">
          <span>
            <small>LAP</small>
            <b>{actualLap?.number ?? "—"}</b>
          </span>
          <span>
            <small>LAP TIME</small>
            <b>{lapTime(actualLap?.time)}</b>
          </span>
          <span>
            <small>TYRE</small>
            <b>{actualLap?.compound?.slice(0, 1) || "—"}</b>
          </span>
        </div>
      </button>
      <button
        className="lap-link"
        onClick={onLap}
        disabled={!onLap}
        aria-label={`Choose lap for ${driver.name}`}
      >
        {actualLap
          ? lap && lap.number !== driver.best_lap?.number
            ? "SELECTED LAP"
            : "FASTEST ELIGIBLE LAP"
          : "NO ELIGIBLE LAP"}
        {onLap && <ChevronRight size={12} />}
      </button>
      {!driver.best_lap && (
        <p className="card-unavailable">{driver.unavailable_reason}</p>
      )}
    </article>
  );
}
export function DriverSelectionSlot({
  index,
  selection,
  active,
  onActivate,
  onRemove,
  onLap,
}: {
  index: number;
  selection: Selection | null;
  active: boolean;
  onActivate: () => void;
  onRemove: () => void;
  onLap: () => void;
}) {
  return (
    <div
      className={`selection-slot ${active ? "active" : ""}`}
      style={{ "--selection": COLORS[index] } as CSSProperties}
    >
      <button className="slot-main" onClick={onActivate}>
        <span className="slot-letter">{index === 0 ? "A" : "B"}</span>
        <span>
          <small>DRIVER {index === 0 ? "A" : "B"}</small>
          <strong>
            {selection ? selection.driver.name : "Select a driver"}
          </strong>
          <em>
            {selection
              ? `${selection.driver.team} · L${selection.lap.number} · ${lapTime(selection.lap.time)}`
              : active
                ? "Choose a card below"
                : "Click to activate this slot"}
          </em>
        </span>
        {selection ? <Check size={18} /> : <span className="slot-plus">+</span>}
      </button>
      {selection && (
        <div className="slot-actions">
          <button onClick={onLap}>Change lap</button>
          <button
            onClick={onRemove}
            aria-label={`Remove driver ${index === 0 ? "A" : "B"}`}
          >
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  );
}
export function SelectionBar({
  selections,
  active,
  setActive,
  remove,
  lap,
  swap,
  compare,
  loading,
}: {
  selections: (Selection | null)[];
  active: number;
  setActive: (i: number) => void;
  remove: (i: number) => void;
  lap: (i: number) => void;
  swap: () => void;
  compare: () => void;
  loading: boolean;
}) {
  return (
    <div className="selection-bar">
      <DriverSelectionSlot
        index={0}
        selection={selections[0]}
        active={active === 0}
        onActivate={() => setActive(0)}
        onRemove={() => remove(0)}
        onLap={() => lap(0)}
      />
      <button
        className="swap-button"
        onClick={swap}
        disabled={!selections.some(Boolean)}
        aria-label="Swap drivers"
      >
        <ArrowLeftRight size={18} />
      </button>
      <DriverSelectionSlot
        index={1}
        selection={selections[1]}
        active={active === 1}
        onActivate={() => setActive(1)}
        onRemove={() => remove(1)}
        onLap={() => lap(1)}
      />
      <button
        className="button primary compare-button"
        disabled={!selections.every(Boolean) || loading}
        onClick={compare}
      >
        {loading ? (
          <LoaderCircle size={17} className="spin" />
        ) : (
          <>
            Compare selected laps <ChevronRight size={17} />
          </>
        )}
      </button>
    </div>
  );
}
export function LapPicker({
  driver,
  current,
  onChoose,
  onClose,
  provider,
}: {
  driver: Driver;
  current?: number;
  onChoose: (lap: Lap) => void;
  onClose: () => void;
  provider: string;
}) {
  const dialog = useRef<HTMLElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    dialog.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const trap = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const controls = Array.from(
        dialog.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), input, select, [tabindex="0"]',
        ) || [],
      );
      const first = controls[0],
        last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", trap);
    return () => {
      document.removeEventListener("keydown", trap);
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, []);
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section
        ref={dialog}
        className="lap-modal angular-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="lap-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header>
          <div>
            <span className="eyebrow">LAP LIBRARY / {driver.code}</span>
            <h2 id="lap-title">{driver.name}</h2>
          </div>
          <button
            className="icon-button"
            onClick={onClose}
            aria-label="Close lap picker"
          >
            <X />
          </button>
        </header>
        <p>
          {provider === "openf1"
            ? "Eligible OpenF1 laps have a timestamp, complete sectors agreeing with lap time, no pit-lane indicators, and no matched deletion notice. See Methods for limitations."
            : "Only accurate, timed laps outside the pits are eligible. Deleted and generated laps are excluded."}
        </p>
        <div className="lap-table">
          <table>
            <thead>
              <tr>
                <th>Lap</th>
                <th>Time</th>
                <th>Tyre</th>
                <th>Availability</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {driver.laps.map((l) => (
                <tr
                  key={l.number}
                  className={current === l.number ? "chosen" : ""}
                >
                  <td>{l.number}</td>
                  <td>{lapTime(l.time)}</td>
                  <td>{l.compound || "—"}</td>
                  <td>
                    {l.eligible
                      ? l.number === driver.best_lap?.number
                        ? "Fastest eligible"
                        : "Eligible"
                      : l.reason}
                  </td>
                  <td>
                    <button
                      className="button small"
                      disabled={!l.eligible}
                      onClick={() => onChoose(l)}
                    >
                      {current === l.number ? "Selected" : "Use lap"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
