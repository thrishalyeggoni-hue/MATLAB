"""Regressions for the calendar stall: disk reuse, bounded failure and UTC matching."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from backend.calendar import decode, event_schedule


def fixture():
    row = dict(round_number=1, country='Bahrain', location='Sakhir',
               official_event_name='Bahrain GP', event_name='Bahrain Grand Prix',
               event_date='2024-03-02T18:00:00', gmt_offset='+03:00',
               event_format='conventional', f1_api_support=True)
    for i in range(1, 6):
        row[f'session{i}'] = 'Race' if i == 5 else 'Qualifying' if i == 4 else f'Practice {i}'
        row[f'session{i}_date'] = '2024-03-01T19:00:00' if i == 4 else '2024-03-02T18:00:00'
    return {key: {'0': value} for key, value in row.items()}


class CalendarTests(unittest.TestCase):
    def test_recorded_local_times_become_exact_utc_and_still_make_fastf1_sessions(self):
        events = decode(fixture(), 2024)
        event = events.get_event_by_round(1)
        self.assertEqual(str(event['Session4DateUtc']), '2024-03-01 16:00:00')
        self.assertEqual(event.get_session('Qualifying').name, 'Qualifying')

    def test_saved_historical_calendar_never_waits_for_network_even_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, '2024.json').write_text(json.dumps(fixture()))
            with patch('backend.calendar.CACHE', Path(directory)), patch('backend.calendar.httpx.Client') as client:
                self.assertEqual(len(event_schedule(2024)), 1)
                self.assertEqual(len(event_schedule(2024)), 1)
                client.assert_not_called()

    def test_timeout_is_actionable_and_not_cached_as_success(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('backend.calendar.CACHE', Path(directory)), patch('backend.calendar.httpx.Client') as client:
                client.return_value.__enter__.return_value.get.side_effect = httpx.ReadTimeout('stalled')
                with self.assertRaisesRegex(ValueError, 'time limit.*Retry'):
                    event_schedule(2024)
                self.assertFalse(Path(directory, '2024.json').exists())
                self.assertLessEqual(client.call_args.kwargs['timeout'].read, 8)

    def test_download_is_saved_but_malformed_responses_do_not_poison_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('backend.calendar.CACHE', Path(directory)), patch('backend.calendar.httpx.Client') as client:
                response = client.return_value.__enter__.return_value.get.return_value
                response.json.return_value = fixture()
                event_schedule(2024)
                self.assertEqual(json.loads(Path(directory, '2024.json').read_text()), fixture())
                response.json.return_value = {'error': 'not a calendar'}
                with self.assertRaises(ValueError):
                    event_schedule(2025)
                self.assertFalse(Path(directory, '2025.json').exists())

    def test_stale_current_calendar_survives_network_outage(self):
        from datetime import datetime, timezone
        year = datetime.now(timezone.utc).year
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, f'{year}.json')
            target.write_text(json.dumps(fixture())); os.utime(target, (0, 0))
            with patch('backend.calendar.CACHE', Path(directory)), patch('backend.calendar.httpx.Client') as client:
                client.return_value.__enter__.return_value.get.side_effect = httpx.ReadTimeout('offline')
                self.assertEqual(len(event_schedule(year)), 1)
