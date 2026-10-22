"""Full-race replay preserves laps and gaps instead of repeating a best lap."""
import unittest
from unittest.mock import patch
import pandas as pd
from backend import main  # Configure FastF1 cache before importing the adapter.
from backend.open_data import full_race, race_trace


class RaceTests(unittest.TestCase):
    def test_full_session_trace_keeps_outages_explicit(self):
        origin = pd.Timestamp('2024-01-01T00:00:00Z')
        car, position = [], []
        for elapsed in [0, 1, 2, 3, 4, 10, 11, 12, 13, 14, 15]:
            stamp = (origin + pd.Timedelta(seconds=elapsed)).isoformat()
            car.append(dict(date=stamp, speed=100+elapsed, throttle=90, brake=0, n_gear=4, rpm=8000))
            position.append(dict(date=stamp, x=elapsed*10, y=elapsed*20))
        samples, gaps = race_trace(car, position, origin, 0, 15)
        self.assertIn([4., 10.], gaps)
        self.assertNotIn(6, samples['time'])
        self.assertEqual(samples['speed'][-1], 115)
        self.assertEqual(samples['time'][0], 0)

    def test_pit_and_untimed_laps_remain_listed_and_race_continues_after_retirement(self):
        origin = pd.Timestamp('2024-01-01T00:00:00Z')
        drivers, raw = [], []
        for number in ('1', '16'):
            laps = [dict(number=1, time=100, eligible=True),
                    dict(number=2, time=110, eligible=False, reason='Pit lane recorded'),
                    dict(number=3, time=None, eligible=False, reason='No start timestamp')]
            drivers.append(dict(id=number, name=number, laps=laps, best_lap=laps[0]))
            raw.extend([dict(driver_number=int(number), lap_number=1, date_start=origin.isoformat(), lap_duration=100),
                        dict(driver_number=int(number), lap_number=2, date_start=(origin+pd.Timedelta(seconds=100)).isoformat(), lap_duration=110),
                        dict(driver_number=int(number), lap_number=3, date_start=None, lap_duration=None)])
        raw.append(dict(driver_number=99, lap_number=57, date_start=(origin+pd.Timedelta(seconds=5400)).isoformat(), lap_duration=90))
        with patch('backend.open_data.resolve_session', return_value=({'name':'Test Grand Prix'}, {'session_key':100})), \
             patch('backend.open_data.session_summary', return_value={'drivers':drivers, 'source':'test fixture'}), \
             patch('backend.open_data.driver_metadata', return_value={'99':{'position':1, 'name':'Other winner', 'team':'Other team'}}), \
             patch('backend.open_data.fetch', side_effect=lambda endpoint, **params: raw if endpoint=='laps' else [{'date':(origin+pd.Timedelta(seconds=210)).isoformat()}]), \
             patch('backend.open_data.race_trace', return_value=({'time':[0,210]}, [])):
            race = full_race(2024, 1, '1', '16')
        self.assertEqual(race['total_laps'], 57)
        self.assertEqual(race['duration'], 5490)
        self.assertEqual(race['winner']['number'], '99')
        self.assertEqual(race['winner']['finish_time'], 5490)
        self.assertEqual(len(race['participants'][0]['laps']), 3)
        self.assertFalse(race['participants'][0]['laps'][1]['eligible'])
        self.assertIsNone(race['participants'][0]['laps'][2]['start'])
        self.assertEqual(race['participants'][0]['driver']['best_lap']['number'], 1)


if __name__ == '__main__':
    unittest.main()
