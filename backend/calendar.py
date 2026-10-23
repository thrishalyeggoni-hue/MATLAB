"""Bounded downloads of the FastF1 calendar, persisted independently of HTTP cache."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock

import fastf1
import httpx
import pandas as pd

CACHE = Path(__file__).resolve().parent.parent / '.cache' / 'calendars'
SOURCE = 'https://raw.githubusercontent.com/theOehrly/f1schedule/master/schedule_{year}.json'
LOCK = RLock()


def decode(payload, year):
    """Preserve FastF1 event/session metadata and convert recorded local times to UTC."""
    frame = pd.DataFrame(payload)
    required = {'round_number', 'event_name', 'event_date', 'country', 'location',
                'gmt_offset', 'event_format', 'f1_api_support'}
    required |= {f'session{i}{suffix}' for i in range(1, 6) for suffix in ('', '_date')}
    if not required.issubset(frame.columns) or frame.empty:
        raise ValueError('Incomplete FastF1 calendar response.')
    for i in range(1, 6):
        local, utc = [], []
        for _, row in frame.iterrows():
            stamp = pd.Timestamp(row[f'session{i}_date'])
            offset = row['gmt_offset'] or '+00:00'
            sign = -1 if offset.startswith('-') else 1
            hours, minutes = map(int, offset.lstrip('+-').split(':'))
            zone = timezone(sign * timedelta(hours=hours, minutes=minutes))
            stamp = stamp.tz_localize(zone) if not pd.isna(stamp) and stamp.tzinfo is None else stamp
            local.append(stamp)
            utc.append(stamp.tz_convert('UTC').tz_localize(None) if not pd.isna(stamp) else pd.NaT)
        frame[f'session{i}_date'] = pd.Series(local, index=frame.index, dtype=object)
        frame[f'session{i}_date_utc'] = utc
    frame['event_date'] = pd.to_datetime(frame['event_date']).dt.normalize()
    frame = frame.drop(columns='gmt_offset')
    frame = frame.rename(columns={key: ''.join(part.capitalize() for part in key.split('_')) for key in frame.columns})
    if not (pd.to_numeric(frame['RoundNumber'], errors='coerce') > 0).any():
        raise ValueError('No recorded Grand Prix events in this calendar.')
    return fastf1.events.EventSchedule(frame, year=year)


def event_schedule(year):
    target = CACHE / f'{year}.json'
    with LOCK:
        saved = None
        try:
            saved = decode(json.loads(target.read_text()), year)
            # Past calendars are stable. Revalidate the current calendar once a day.
            if year < datetime.now(timezone.utc).year or datetime.now().timestamp() - target.stat().st_mtime < 86400:
                return saved
        except (OSError, ValueError, TypeError, KeyError):
            pass
        try:
            with httpx.Client(timeout=httpx.Timeout(8, connect=4)) as client:
                response = client.get(SOURCE.format(year=year))
                response.raise_for_status()
                payload = response.json()
            result = decode(payload, year)
        except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
            if saved is not None:
                return saved
            raise ValueError('The season calendar could not be downloaded within the time limit. Check your connection and press Retry. Previously saved calendars remain available.') from exc
        CACHE.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.NamedTemporaryFile(mode='w', dir=CACHE, suffix='.tmp', delete=False) as output:
                json.dump(payload, output)
                temp = Path(output.name)
            os.replace(temp, target)
        except OSError:
            # A read-only disk should not prevent using a successfully retrieved calendar.
            if 'temp' in locals():
                temp.unlink(missing_ok=True)
        return result
