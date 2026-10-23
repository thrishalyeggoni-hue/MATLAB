"""F1 Driver DNA API, with background loading and local FastF1 caching."""
from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Literal

import fastf1
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

CACHE_DIR = Path(__file__).resolve().parent.parent / '.cache' / 'fastf1'
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.configure(cache_dir=str(CACHE_DIR))
from backend import data, open_data  # noqa: E402
from backend.analysis import analyze  # noqa: E402

app = FastAPI(title='F1 Driver DNA', version='1.0.0')
app.add_middleware(CORSMiddleware,
    allow_origin_regex=r'http://(localhost|127\.0\.0\.1)(:\d+)?',
    allow_methods=['GET', 'POST'], allow_headers=['*'])
POOL = ThreadPoolExecutor(max_workers=2)
JOBS: dict = {}
JOB_KEYS: dict = {}
JOB_LOCK = Lock()
log = logging.getLogger(__name__)


class SessionRequest(BaseModel):
    year: int = Field(ge=2018, le=datetime.now(timezone.utc).year)
    round: int = Field(ge=1, le=30)
    session: str = Field(min_length=1, max_length=32)
    refresh: bool = False
    provider: Literal['fastf1', 'openf1'] = 'fastf1'


class CompareRequest(SessionRequest):
    driver_a: str = Field(pattern=r'^\d{1,3}$')
    driver_b: str = Field(pattern=r'^\d{1,3}$')
    lap_a: int = Field(ge=1, le=200)
    lap_b: int = Field(ge=1, le=200)

    @model_validator(mode='after')
    def different_drivers(self):
        if self.driver_a == self.driver_b:
            raise ValueError('Select two different drivers.')
        return self


class RaceRequest(SessionRequest):
    driver_a: str = Field(pattern=r'^\d{1,3}$')
    driver_b: str = Field(pattern=r'^\d{1,3}$')


class AnalysisRequest(BaseModel):
    comparison_id: str
    degree: int = Field(default=3, ge=1, le=5)
    start: float = Field(default=0, ge=0)
    end: float | None = Field(default=None, gt=0)
    scale: bool = True
    features: list[Literal['speed','throttle','brake','gear','rpm']] = Field(default=['speed','throttle','brake','gear','rpm'], min_length=2, max_length=5)

    @model_validator(mode='after')
    def validate_range(self):
        if self.end is not None and self.end <= self.start:
            raise ValueError('End distance must exceed start distance.')
        if len(set(self.features)) != len(self.features):
            raise ValueError('Choose each channel only once.')
        return self


def submit(key, fn, *args, refresh=False):
    with JOB_LOCK:
        existing = JOB_KEYS.get(key)
        if existing and JOBS[existing]['status'] != 'error' and not refresh:
            return {'job_id': existing}
        # Bound retained comparison payloads without evicting active work.
        if len(JOBS) >= 32:
            for old in list(JOBS):
                if JOBS[old]['status'] in ('done','error'):
                    JOBS.pop(old)
                    for k,v in list(JOB_KEYS.items()):
                        if v == old:
                            JOB_KEYS.pop(k)
                    break
        job_id = uuid.uuid4().hex
        JOBS[job_id] = {'status': 'loading', 'message': 'Retrieving recorded session data. First downloads can take a minute.'}
        JOB_KEYS[key] = job_id
    def run():
        try:
            result = fn(*args)
            JOBS[job_id] = {'status': 'done', 'data': result}
        except Exception as exc:
            log.exception('Data job failed')
            message = str(exc) if isinstance(exc, ValueError) else 'FastF1 could not retrieve this data. Check your connection or choose another recorded session, then retry.'
            JOBS[job_id] = {'status': 'error', 'message': message}
    POOL.submit(run)
    return {'job_id': job_id}


@app.get('/api/health')
def health():
    return {'status': 'ok', 'service': 'F1 Driver DNA'}


@app.get('/api/seasons')
def seasons():
    return {'seasons': list(range(datetime.now(timezone.utc).year, 2017, -1))}


@app.get('/api/schedule/{year}')
def schedule(year: int):
    if not 2018 <= year <= datetime.now(timezone.utc).year:
        raise HTTPException(422, 'FastF1 telemetry seasons start in 2018.')
    return submit(('schedule',year), data.schedule, year)


@app.post('/api/session')
def session(request: SessionRequest):
    loader = open_data.session_summary if request.provider == 'openf1' else data.session_summary
    return submit(('session',request.provider,request.year,request.round,request.session), loader, request.year,request.round,request.session,request.refresh,refresh=request.refresh)


@app.post('/api/compare')
def compare(request: CompareRequest):
    loader = open_data.compare if request.provider == 'openf1' else data.compare
    return submit(('compare', *request.model_dump().values()), loader,
                  request.year,request.round,request.session,request.driver_a,request.lap_a,request.driver_b,request.lap_b)


@app.get('/api/jobs/{job_id}')
def job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, 'This data job has expired. Load the session again.')
    return JOBS[job_id]


@app.post('/api/race')
def full_race(request: RaceRequest):
    return submit(('race', request.year, request.round, request.driver_a, request.driver_b),
                  open_data.full_race, request.year, request.round, request.driver_a, request.driver_b)


@app.post('/api/analysis')
def analysis(request: AnalysisRequest):
    comparison = JOBS.get(request.comparison_id)
    if not comparison or comparison['status'] != 'done' or 'traces' not in comparison['data']:
        raise HTTPException(404, 'Comparison is unavailable. Compare the selected laps again.')
    try:
        return analyze(comparison['data'],request.degree,request.start,request.end,request.scale,request.features)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
