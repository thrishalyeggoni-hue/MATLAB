"""Explicit OpenF1 historical-data adapter; never substitutes sessions or data."""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import timedelta
from pathlib import Path
from threading import RLock

import httpx
import numpy as np
import pandas as pd

from backend.data import schedule, scalar, driver_metadata

CACHE = Path(__file__).resolve().parent.parent / '.cache' / 'openf1'
CACHE.mkdir(parents=True, exist_ok=True)
LOCK = RLock()
LAST_REQUEST = 0.0
SOURCE = 'OpenF1 historical timing and telemetry; calendar via FastF1'


def enrich_drivers(drivers, year, round_number, name, refresh=False):
    """Match identities by number AND acronym, retaining exact OpenF1 participants."""
    if refresh:
        driver_metadata.cache_clear()
    try:
        metadata = driver_metadata(year, round_number, name)
    except Exception:
        return 'FastF1 driver metadata unavailable; driver identities from OpenF1'
    matched = 0
    for driver in drivers:
        recorded = metadata.get(driver['number'])
        if not recorded or not recorded.get('code') or recorded['code'] != driver['code']:
            continue
        for field in ('name', 'first_name', 'last_name', 'code', 'team'):
            if recorded.get(field):
                driver[field] = recorded[field]
        matched += 1
    return f'FastF1 driver identities ({matched}/{len(drivers)} matched; remaining identities from OpenF1)'


def fetch(endpoint: str, **params):
    global LAST_REQUEST
    identity = json.dumps([endpoint,params],sort_keys=True)
    target = CACHE / (hashlib.sha256(identity.encode()).hexdigest()+'.json')
    with LOCK:
        if target.exists():
            return json.loads(target.read_text())
        wait = 2.15 - (time.monotonic()-LAST_REQUEST)
        if wait > 0:
            time.sleep(wait)
        try:
            with httpx.Client(timeout=60) as client:
                response = client.get(f'https://api.openf1.org/v1/{endpoint}',params=params)
            LAST_REQUEST = time.monotonic()
            if response.status_code == 429:
                raise ValueError('OpenF1 rate limit reached. Wait a minute, then retry. Previously downloaded data is cached locally.')
            response.raise_for_status()
            rows = response.json()
            if not isinstance(rows,list):
                raise ValueError('OpenF1 returned an unexpected response.')
            # Only cache nonempty historical responses, not transient unavailable states.
            if rows:
                temp = target.with_suffix('.tmp')
                temp.write_text(json.dumps(rows))
                temp.replace(target)
            return rows
        except httpx.HTTPError as exc:
            raise ValueError(f'OpenF1 could not retrieve {endpoint}. Check your connection and retry; no other session was substituted.') from exc


def resolve_session(year:int, round_number:int, name:str):
    if year < 2023:
        raise ValueError('The free OpenF1 archive starts in 2023. Choose a later season or select FastF1 with a populated cache or authenticated account.')
    event = next((e for e in schedule(year) if e['round']==round_number),None)
    if event is None:
        raise ValueError('The selected Grand Prix is not in this season’s recorded calendar.')
    expected = next((s for s in event['sessions'] if s['name']==name),None)
    if not expected or not expected['completed']:
        raise ValueError('This session has not taken place yet. Only historical data is supported.')
    # Match by season, session name, country and scheduled UTC date. Country alone is ambiguous.
    candidates = fetch('sessions', year=year, session_name=name)
    date = pd.Timestamp(expected['date']).date()
    matches = [s for s in candidates if s.get('date_start') and pd.Timestamp(s['date_start']).date()==date and s.get('country_name')==event['country'] and not s.get('is_cancelled')]
    if len(matches)!=1:
        raise ValueError('OpenF1 has no unique matching record for this exact event and session. Nothing was substituted.')
    return event,matches[0]


def deleted_laps(messages):
    """Match deletion/reinstatement notices to recorded driver and exact lap duration."""
    states = {}
    for m in sorted(messages,key=lambda r:r.get('date') or ''):
        text = m.get('message','').upper()
        if not ('DELETED' in text or 'REINSTATED' in text):
            continue
        driver = m.get('driver_number')
        if driver is None:
            match = re.search(r'CAR\s+(\d+)',text)
            driver = int(match.group(1)) if match else None
        clock = re.search(r'(\d+):(\d{2})\.(\d{3})',text)
        if driver is not None and clock:
            milliseconds = (int(clock[1])*60+int(clock[2]))*1000+int(clock[3])
            states[(int(driver),milliseconds)] = 'DELETED' in text and 'REINSTATED' not in text
    return {k for k,v in states.items() if v}


def normalize_lap(row, stints, deleted, pits):
    driver, number = int(row['driver_number']),int(row['lap_number'])
    duration = row.get('lap_duration')
    sectors = [row.get(f'duration_sector_{i}') for i in range(1,4)]
    issues = []
    if duration is None or duration<=0:
        issues.append('No recorded lap duration')
    if not row.get('date_start'):
        issues.append('No recorded start timestamp')
    if row.get('is_pit_out_lap'):
        issues.append('Pit out lap')
    if (driver,number) in pits or any(2064 in (row.get(f'segments_sector_{i}') or []) for i in range(1,4)):
        issues.append('Pit lane recorded')
    if any(s is None or s<=0 for s in sectors):
        issues.append('Incomplete sector timing')
    elif duration is not None and abs(sum(sectors)-duration)>.05:
        issues.append('Sector sum differs from lap time by more than 0.05 s')
    if duration is not None and (driver,round(duration*1000)) in deleted:
        issues.append('Lap time deleted by race control')
    stint=next((s for s in stints if s.get('driver_number')==driver and s.get('lap_start') is not None and s['lap_start']<=number<=(s.get('lap_end') or number)),None)
    return {'number':number,'time':duration,'sectors':sectors,
            'compound':stint.get('compound') if stint else None,
            'tyre_life':number-stint['lap_start']+stint['tyre_age_at_start'] if stint and stint.get('tyre_age_at_start') is not None else None,
            'eligible':not issues,'reason':'; '.join(issues) if issues else None}


def session_summary(year:int, round_number:int, name:str, refresh=False):
    event,s=resolve_session(year,round_number,name)
    key=s['session_key']
    drivers=fetch('drivers',session_key=key)
    laps=fetch('laps',session_key=key)
    stints=fetch('stints',session_key=key)
    race_control=fetch('race_control',session_key=key)
    pit_records=fetch('pit',session_key=key)
    deleted=deleted_laps(race_control)
    pits={(int(p['driver_number']),int(p['lap_number'])) for p in pit_records if p.get('lap_number') is not None}
    if not drivers:
        raise ValueError('No participant records are available for this OpenF1 session.')
    output=[]
    for driver in drivers:
        number=int(driver['driver_number'])
        recorded=sorted([normalize_lap(l,stints,deleted,pits) for l in laps if l['driver_number']==number],key=lambda l:l['number'])
        valid=[l for l in recorded if l['eligible']]
        best=min(valid,key=lambda l:l['time']) if valid else None
        color=driver.get('team_colour') or ''
        output.append({'id':str(number),'number':str(number),'name':f"{driver.get('first_name','')} {driver.get('last_name','')}".strip(),
            'first_name':driver.get('first_name') or '', 'last_name':driver.get('last_name') or '',
            'code':driver.get('name_acronym') or str(number),'team':driver.get('team_name') or 'Unavailable',
            'color':'#'+color if re.fullmatch(r'[0-9a-fA-F]{6}',color) else '#8b929f',
            'country':driver.get('country_code'),'portrait':None,'laps':recorded,'best_lap':best,
            'unavailable_reason':None if best else 'No complete, timed lap outside the pits passed the OpenF1 eligibility checks.'})
    # A useful recorded ordering, never an invented rating: fastest eligible lap first.
    identities = enrich_drivers(output, year, round_number, name, refresh)
    output.sort(key=lambda d:(d['best_lap'] is None,d['best_lap']['time'] if d['best_lap'] else float('inf')))
    return {'year':year,'round':round_number,'session':name,'event':event['name'],'country':event['country'],
            'location':event['location'],'date':str(pd.Timestamp(s['date_start']).date()),'drivers':output,
            'timing_available':bool(laps),'availability':None if laps else 'No OpenF1 lap timing is available for this session.',
            'source':f'{identities}; {SOURCE}', 'portrait_note':'Licensed local portraits with initials as fallback.', 'provider':'openf1'}


def _trace(session_key, driver, selected_lap, raw_lap):
    start=pd.Timestamp(raw_lap['date_start'])
    duration=selected_lap['time']
    stop=start+timedelta(seconds=duration)
    params={'session_key':session_key,'driver_number':int(driver),'date>':(start-timedelta(seconds=1)).isoformat(),'date<':(stop+timedelta(seconds=1)).isoformat()}
    car=fetch('car_data',**params)
    pos=fetch('location',**params)
    if len(car)<10 or len(pos)<10:
        raise ValueError(f'Insufficient recorded car or location telemetry for driver {driver}, lap {selected_lap["number"]}. Choose another lap.')
    def to_matrix(rows,fields):
        matrix=np.array([[(pd.Timestamp(r['date'])-start).total_seconds(),*[r.get(f,np.nan) for f in fields]] for r in rows],dtype=float)
        matrix=matrix[np.isfinite(matrix).all(axis=1)]
        matrix=matrix[np.argsort(matrix[:,0])]
        _,indices=np.unique(matrix[:,0],return_index=True)
        return matrix[indices]
    c=to_matrix(car,['speed','throttle','brake','n_gear','rpm'])
    p=to_matrix(pos,['x','y'])
    if min(len(c),len(p))<10:
        raise ValueError('Too few complete telemetry rows for this selected lap.')
    lower=max(0,c[0,0],p[0,0]);upper=min(duration,c[-1,0],p[-1,0])
    # Reject large coverage gaps rather than showing an invented full-lap replay.
    if lower>1 or duration-upper>1 or np.max(np.diff(c[:,0]))>3 or np.max(np.diff(p[:,0]))>3:
        raise ValueError('This lap has a substantial telemetry gap. Choose another lap for replay.')
    times=np.unique(np.concatenate(([lower,upper],c[(c[:,0]>=lower)&(c[:,0]<=upper),0],p[(p[:,0]>=lower)&(p[:,0]<=upper),0])))
    preceding=np.clip(np.searchsorted(c[:,0],times,side='right')-1,0,len(c)-1)
    speed=np.interp(times,c[:,0],c[:,1])
    # Distance is explicitly an estimate from trapezoidal speed integration, in metres.
    distance=np.concatenate(([0.],np.cumsum((speed[1:]+speed[:-1])/2/3.6*np.diff(times))))
    samples={'time':times.tolist(),'distance':distance.tolist(),'speed':speed.tolist(),
             'throttle':np.interp(times,c[:,0],c[:,2]).tolist(),'brake':(c[preceding,3]>0).astype(int).tolist(),
             'gear':c[preceding,4].tolist(),'rpm':np.interp(times,c[:,0],c[:,5]).tolist(),
             'x':np.interp(times,p[:,0],p[:,1]).tolist(),'y':np.interp(times,p[:,0],p[:,2]).tolist()}
    return {'driver':str(driver),'lap':selected_lap,'samples':samples}


def compare(year,round_number,name,a,lap_a,b,lap_b):
    if a==b:
        raise ValueError('Choose two distinct drivers.')
    _,s=resolve_session(year,round_number,name)
    summary=session_summary(year,round_number,name)
    raw=fetch('laps',session_key=s['session_key'])
    traces=[]
    for driver,number in [(a,lap_a),(b,lap_b)]:
        participant=next((d for d in summary['drivers'] if d['id']==driver),None)
        selected=next((l for l in participant['laps'] if l['number']==number),None) if participant else None
        if not selected or not selected['eligible']:
            raise ValueError('This driver or lap is unavailable or ineligible in the selected session.')
        row=next(l for l in raw if l['driver_number']==int(driver) and l['lap_number']==number)
        traces.append(_trace(s['session_key'],driver,selected,row))
    return {'traces':traces,'corners':[],'rotation':0,'event':summary['event'],'session':name,'year':year,'source':summary['source'],
            'warnings':['Source: OpenF1 historical archive. This is an explicitly selected alternative to authenticated FastF1 timing.',
                        'Ghost lap comparison: both laps start together; these are not actual race positions.',
                        'OpenF1 lap-start timestamps and locations are approximate. Car and location channels are merged by timestamp with interpolation; gear and brake use the preceding sample.',
                        'Distance is estimated by trapezoidal integration of recorded speed. Distance-aligned deltas and running values are estimates, separate from recorded lap and sector timing.',
                        'Corner annotations are unavailable in this source. The circuit outline comes only from this selected lap’s recorded location samples.']}


def race_trace(car, location, origin, start, end):
    """Keep full-session recorded samples, including pit laps, and expose outages."""
    def matrix(rows, fields):
        values = np.array([[(pd.Timestamp(r['date'])-origin).total_seconds(),
                            *[r.get(f, np.nan) for f in fields]] for r in rows], dtype=float)
        if values.size == 0:
            raise ValueError('No recorded telemetry is available for this driver in this race.')
        values = values[np.isfinite(values).all(axis=1)]
        values = values[np.argsort(values[:, 0])]
        _, indices = np.unique(values[:, 0], return_index=True)
        return values[indices]
    c = matrix(car, ['speed', 'throttle', 'brake', 'n_gear', 'rpm'])
    p = matrix(location, ['x', 'y'])
    if min(len(c), len(p)) < 10:
        raise ValueError('Too few recorded samples to replay this driver’s race.')
    lower, upper = max(start, c[0, 0], p[0, 0]), min(end, c[-1, 0], p[-1, 0])
    c = c[(c[:, 0] >= lower) & (c[:, 0] <= upper)]
    if len(c) < 10:
        raise ValueError('Car and position telemetry do not overlap for this driver.')
    times = c[:, 0]
    samples = {'time': times.tolist(), 'speed': c[:, 1].tolist(),
               'throttle': c[:, 2].tolist(), 'brake': (c[:, 3] > 0).astype(int).tolist(),
               'gear': c[:, 4].tolist(), 'rpm': c[:, 5].tolist(),
               'x': np.interp(times, p[:, 0], p[:, 1]).tolist(),
               'y': np.interp(times, p[:, 0], p[:, 2]).tolist(),
               'distance': [None] * len(c)}
    gaps = [[float(rows[i, 0]), float(rows[i+1, 0])] for rows in (c, p)
            for i in range(len(rows)-1) if rows[i+1, 0]-rows[i, 0] > 3]
    return samples, gaps


def full_race(year, round_number, a, b):
    if a == b:
        raise ValueError('Choose two distinct drivers.')
    event, session = resolve_session(year, round_number, 'Race')
    key = session['session_key']
    summary = session_summary(year, round_number, 'Race')
    raw_laps = fetch('laps', session_key=key)
    starts = [pd.Timestamp(l['date_start']) for l in raw_laps
              if l.get('date_start') and l.get('lap_number') == 1]
    if not starts:
        raise ValueError('The race has no recorded lap-one start timestamps.')
    origin = min(starts)
    traces, participants = [], []
    for number in (a, b):
        driver = next((d for d in summary['drivers'] if d['id'] == number), None)
        if driver is None:
            raise ValueError(f'Driver {number} did not participate in this race. Choose two race participants.')
        rows = sorted([l for l in raw_laps if str(l['driver_number']) == number and l.get('date_start')],
                      key=lambda l: l['lap_number'])
        if not rows:
            raise ValueError(f'No recorded race laps are available for {driver["name"]}.')
        car = fetch('car_data', session_key=key, driver_number=int(number))
        pos = fetch('location', session_key=key, driver_number=int(number))
        telemetry_end = min(max((pd.Timestamp(r['date'])-origin).total_seconds() for r in car),
                            max((pd.Timestamp(r['date'])-origin).total_seconds() for r in pos)) if car and pos else 0
        intervals = []
        for index, row in enumerate(rows):
            start = (pd.Timestamp(row['date_start'])-origin).total_seconds()
            end = ((pd.Timestamp(rows[index+1]['date_start'])-origin).total_seconds() if index+1 < len(rows)
                   else start + row['lap_duration'] if row.get('lap_duration') else telemetry_end)
            lap = next((l for l in driver['laps'] if l['number'] == row['lap_number']), None)
            if lap:
                intervals.append({**lap, 'start': max(0, start), 'end': max(start, end)})
        if not intervals:
            raise ValueError(f'No race lap intervals are available for {driver["name"]}.')
        samples, gaps = race_trace(car, pos, origin, intervals[0]['start'], intervals[-1]['end'])
        traces.append({'driver': number, 'lap': driver['best_lap'] or intervals[0], 'samples': samples, 'gaps': gaps})
        known = {lap['number'] for lap in intervals}
        listed = intervals + [{**lap, 'start': None, 'end': None} for lap in driver['laps'] if lap['number'] not in known]
        participants.append({'driver': driver, 'laps': sorted(listed, key=lambda lap: lap['number']),
                             'end': intervals[-1]['end'], 'last_lap': max(l['number'] for l in driver['laps'])})
    race_end = max(((pd.Timestamp(l['date_start'])-origin).total_seconds() + l['lap_duration']
                    for l in raw_laps if l.get('date_start') and l.get('lap_duration')), default=0)
    winner = None
    try:
        classified = driver_metadata(year, round_number, 'Race')
        first = next(((number, record) for number, record in classified.items() if record.get('position') == 1), None)
        if first:
            number, record = first
            finishes = [(pd.Timestamp(l['date_start'])-origin).total_seconds() + l['lap_duration']
                        for l in raw_laps if str(l['driver_number']) == number and l.get('date_start') and l.get('lap_duration')]
            if finishes:
                winner = {'number': number, 'name': record['name'], 'team': record['team'],
                          'finish_time': max(finishes), 'source': 'FastF1 / Jolpica classified race result'}
    except Exception:
        # Never infer a race winner from a fastest lap or just the selected pair.
        pass
    return {'traces': traces, 'participants': participants, 'event': event['name'], 'session': 'Race',
            'year': year, 'corners': [], 'rotation': 0, 'source': summary['source'],
            'duration': max(race_end, max(p['end'] for p in participants)),
            'total_laps': max((l['lap_number'] for l in raw_laps), default=0),
            'origin': origin.isoformat(),
            'winner': winner,
            'warnings': ['Both drivers share recorded race time, rather than starting individual laps together.',
                         'Every recorded lap is included, including pit and untimed laps. Missing telemetry is hidden, not simulated.',
                         'Fastest highlights use the fastest lap passing the documented timing eligibility checks.',
                         'OpenF1 timestamps and positions are approximate; speed and position are interpolated between recorded samples.']}
