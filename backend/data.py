"""FastF1 data access. Only recorded sessions, with explicit availability states."""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from threading import RLock
from datetime import datetime, timezone

from backend.calendar import event_schedule

import fastf1
import numpy as np
import pandas as pd

log = logging.getLogger(__name__)
DATA_LOCK = RLock()


def scalar(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def seconds(value):
    return None if value is None or pd.isna(value) else round(value.total_seconds(), 6)


def schedule(year: int):
    rows = event_schedule(year)
    rows = rows[~rows.is_testing()]
    now = datetime.now(timezone.utc)
    events = []
    for _, row in rows.iterrows():
        sessions = []
        for i in range(1, 6):
            name, date = row.get(f'Session{i}'), row.get(f'Session{i}DateUtc')
            if not name or pd.isna(name) or pd.isna(date):
                continue
            stamp = pd.Timestamp(date).tz_localize('UTC') if pd.Timestamp(date).tzinfo is None else pd.Timestamp(date)
            sessions.append({'name': name, 'date': stamp.isoformat(), 'completed': stamp.to_pydatetime() < now})
        events.append({'round': int(row['RoundNumber']), 'name': row['EventName'],
                       'country': row['Country'], 'location': row['Location'],
                       'date': str(row['EventDate'].date()),
                       'supported': bool(row.get('F1ApiSupport', False)), 'sessions': sessions})
    return events


@lru_cache(maxsize=3)
def get_session(year: int, round_number: int, name: str):
    # Native FastF1 caching avoids repeated downloads. Serialize its mutable sessions.
    session = event_schedule(year).get_event_by_round(round_number).get_session(name)
    session.load(laps=True, telemetry=False, weather=False, messages=False)
    if session.results.empty:
        raise ValueError('No participant data is available for this session.')
    return session


@lru_cache(maxsize=8)
def driver_metadata(year: int, round_number: int, name: str):
    """Load participant identity/results without requesting lap or telemetry archives."""
    with DATA_LOCK:
        session = event_schedule(year).get_event_by_round(round_number).get_session(name)
        session.load(laps=False, telemetry=False, weather=False, messages=False)
        if session.results.empty:
            raise ValueError('FastF1 participant metadata is unavailable.')
        fields = {'name': 'FullName', 'first_name': 'FirstName',
                  'last_name': 'LastName', 'code': 'Abbreviation', 'team': 'TeamName',
                  'position': 'Position'}
        return {str(row['DriverNumber']): {
            dest: scalar(row.get(src)) for dest, src in fields.items()
        } for _, row in session.results.iterrows()}


def lap_info(lap):
    issues = []
    if pd.isna(lap.get('LapTime')):
        issues.append('No recorded lap time')
    if not isinstance(lap.get('IsAccurate'), (bool, np.bool_)) or not bool(lap.get('IsAccurate')):
        issues.append('Timing not marked accurate by FastF1')
    if isinstance(lap.get('Deleted'), (bool, np.bool_)) and bool(lap.get('Deleted')):
        issues.append('Deleted lap')
    if pd.notna(lap.get('PitInTime')) or pd.notna(lap.get('PitOutTime')):
        issues.append('Pit in/out lap')
    if isinstance(lap.get('FastF1Generated'), (bool, np.bool_)) and bool(lap.get('FastF1Generated')):
        issues.append('FastF1 generated lap')
    return {'number': int(lap['LapNumber']), 'time': seconds(lap.get('LapTime')),
            'sectors': [seconds(lap.get(f'Sector{i}Time')) for i in range(1, 4)],
            'compound': scalar(lap.get('Compound')), 'tyre_life': scalar(lap.get('TyreLife')),
            'eligible': not issues, 'reason': '; '.join(issues) if issues else None}


def session_summary(year: int, round_number: int, name: str, refresh: bool = False):
    with DATA_LOCK:
        if refresh:
            get_session.cache_clear()
        s = get_session(year, round_number, name)
        try:
            recorded_laps = s.laps
            timing_available = not recorded_laps.empty
        except Exception:
            recorded_laps = None
            timing_available = False
        availability = None if timing_available else ('Session results are available, but lap timing could not be loaded. F1 now requires an F1 TV Access subscription or higher for archive timing. Authenticate locally using the command in Methods, then retry. A pre-existing FastF1 cache can also supply recorded data.')
        drivers = []
        for _, result in s.results.iterrows():
            number = str(result['DriverNumber'])
            laps = [lap_info(lap) for _, lap in recorded_laps.pick_drivers(number).iterrows() if pd.notna(lap.get('LapNumber'))] if recorded_laps is not None else []
            valid = [lap for lap in laps if lap['eligible']]
            best = min(valid, key=lambda lap: lap['time']) if valid else None
            color = str(result.get('TeamColor', ''))
            color = f'#{color}' if re.fullmatch(r'[0-9a-fA-F]{6}', color) else '#8b929f'
            drivers.append({'id': number, 'number': number, 'name': str(result['FullName']),
                            'first_name': str(result.get('FirstName', '')),
                            'last_name': str(result.get('LastName', '')),
                            'code': str(result.get('Abbreviation', number)),
                            'team': str(result.get('TeamName', 'Unavailable')),
                            'color': color, 'country': scalar(result.get('CountryCode')),
                            'portrait': None, 'laps': laps, 'best_lap': best,
                            'unavailable_reason': None if best else ('Lap timing unavailable · archive access required' if not timing_available else 'No accurate, timed, non-deleted lap outside the pits is available.')})
        return {'year': year, 'round': round_number, 'session': name,
                'event': str(s.event['EventName']), 'country': str(s.event['Country']),
                'location': str(s.event['Location']), 'date': str(s.date.date()),
                'drivers': drivers, 'timing_available': timing_available, 'availability': availability, 'source': 'FastF1 recorded session timing' if timing_available else 'FastF1 / Jolpica recorded session results; timing unavailable',
                'portrait_note': 'Initials are used because licensed driver portraits have not been supplied.'}


def _telemetry(s, driver: str, lap_number: int):
    laps = s.laps.pick_drivers(driver)
    picked = laps[laps['LapNumber'] == lap_number]
    if picked.empty:
        raise ValueError(f'Lap {lap_number} is not recorded for driver {driver}.')
    lap = picked.iloc[0]
    info = lap_info(lap)
    if not info['eligible']:
        raise ValueError(info['reason'])
    try:
        tel = lap.get_telemetry(frequency='original')
    except Exception as exc:
        raise ValueError(f'Telemetry is unavailable for driver {driver}, lap {lap_number}.') from exc
    if tel.empty or 'Distance' not in tel or 'Time' not in tel:
        raise ValueError('This lap has no usable telemetry.')
    tel = tel.sort_values('Time').drop_duplicates('Time')
    t = tel['Time'].dt.total_seconds().to_numpy(dtype=float)
    mask = np.isfinite(t) & (t >= 0) & (t <= info['time'] + .01)
    tel = tel.loc[mask]
    if len(tel) < 10:
        raise ValueError('Too few telemetry samples are available for comparison.')
    channels = {'time': tel['Time'].dt.total_seconds().tolist()}
    for dest, src in [('distance','Distance'),('speed','Speed'),('throttle','Throttle'),
                      ('brake','Brake'),('gear','nGear'),('rpm','RPM'),('x','X'),('y','Y')]:
        channels[dest] = [int(v) if dest == 'brake' and pd.notna(v) else scalar(v) for v in tel[src]] if src in tel else [None] * len(tel)
    if sum(v is not None for v in channels['x']) < 10:
        raise ValueError('Recorded position data is unavailable; this lap cannot be replayed.')
    return {'driver': driver, 'lap': info, 'samples': channels}


def compare(year: int, round_number: int, name: str, a: str, lap_a: int, b: str, lap_b: int):
    if a == b:
        raise ValueError('Choose two different drivers.')
    with DATA_LOCK:
        s = get_session(year, round_number, name)
        try:
            s.car_data
        except Exception:
            s.load(laps=True, telemetry=True, weather=False, messages=False)
        traces = [_telemetry(s, a, lap_a), _telemetry(s, b, lap_b)]
        warnings = ['Ghost lap comparison: selected laps start together. This is not actual race position.',
                    'Position and telemetry channels are merged by FastF1 and may include interpolation. Running values and distance deltas are estimates.']
        corners, rotation = [], 0
        try:
            circuit = s.get_circuit_info()
            if circuit:
                rotation = float(circuit.rotation)
                corners = [{'x': float(r.X), 'y': float(r.Y), 'number': f'{int(r.Number)}{r.Letter or ""}',
                            'distance': scalar(r.Distance)} for r in circuit.corners.itertuples()]
        except Exception:
            log.exception('Corner annotations unavailable')
        if not corners:
            warnings.append('Corner annotations are unavailable. The outline uses recorded lap position data.')
        return {'traces': traces, 'corners': corners, 'rotation': rotation,
                'event': str(s.event['EventName']), 'session': name, 'year': year,
                'warnings': warnings, 'source': 'FastF1 recorded car and position telemetry'}
