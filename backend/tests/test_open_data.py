"""Verify the free-source adapter with explicit, test-only numerical fixtures."""
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from backend import main
from backend.open_data import _trace, deleted_laps, normalize_lap, resolve_session, enrich_drivers


class OpenDataTests(unittest.TestCase):
    def test_identity_match_requires_number_and_code_and_preserves_timing(self):
        drivers = [dict(number='16', code='LEC', name='Open name', team='Open team',
                        laps=[{'number':12}], color='#ff0000'),
                   dict(number='2', code='SAR', name='Logan Sargeant')]
        metadata = {'16': {'name':'Charles Leclerc', 'team':'Ferrari', 'code':'LEC'},
                    '2': {'name':'Different participant', 'code':'VAN'}}
        with patch('backend.open_data.driver_metadata', return_value=metadata):
            source = enrich_drivers(drivers, 2024, 1, 'Qualifying')
        self.assertIn('1/2 matched', source)
        self.assertEqual(drivers[0]['name'], 'Charles Leclerc')
        self.assertEqual(drivers[0]['laps'], [{'number':12}])
        self.assertEqual(drivers[0]['color'], '#ff0000')
        self.assertEqual(drivers[1]['name'], 'Logan Sargeant')

    def test_metadata_failure_reports_fallback_without_losing_participants(self):
        drivers = [dict(number='16', code='LEC', name='Charles Leclerc')]
        with patch('backend.open_data.driver_metadata', side_effect=ValueError('offline')):
            source = enrich_drivers(drivers, 2024, 1, 'Qualifying')
        self.assertIn('metadata unavailable', source)
        self.assertEqual(len(drivers), 1)
        self.assertEqual(drivers[0]['name'], 'Charles Leclerc')

    def test_exact_event_match_never_substitutes_a_session(self):
        event={'round':8,'country':'Monaco','sessions':[{'name':'Qualifying','date':'2024-05-25T14:00:00+00:00','completed':True}]}
        with patch('backend.open_data.schedule',return_value=[event]),patch('backend.open_data.fetch',return_value=[{'country_name':'Monaco','date_start':'2024-05-24T14:00:00+00:00'}]):
            with self.assertRaisesRegex(ValueError,'Nothing was substituted'):
                resolve_session(2024,8,'Qualifying')
        with self.assertRaisesRegex(ValueError,'starts in 2023'):
            resolve_session(2022,8,'Qualifying')

    def test_deletion_and_reinstatement_match_exact_driver_and_clock(self):
        deleted={'date':'2024-01-01T00:00:00Z','driver_number':16,'message':'CAR 16 LAP TIME 1:29.165 DELETED - TRACK LIMITS'}
        reinstated={**deleted,'date':'2024-01-01T00:01:00Z','message':'CAR 16 LAP TIME 1:29.165 REINSTATED'}
        self.assertIn((16,89165),deleted_laps([deleted]))
        self.assertNotIn((16,89165),deleted_laps([reinstated,deleted]))

    def test_lap_eligibility_and_compound_have_recorded_provenance(self):
        lap={'driver_number':16,'lap_number':5,'lap_duration':90.,'date_start':'2024-01-01T00:00:00Z',
             'duration_sector_1':30.,'duration_sector_2':40.,'duration_sector_3':20.,'is_pit_out_lap':False}
        stints=[{'driver_number':16,'lap_start':4,'lap_end':7,'compound':'SOFT','tyre_age_at_start':2}]
        normalized=normalize_lap(lap,stints,set(),set())
        self.assertTrue(normalized['eligible'])
        self.assertEqual(normalized['compound'],'SOFT')
        self.assertEqual(normalized['tyre_life'],3)
        self.assertIsNone(normalize_lap(lap,[],set(),set())['compound'])
        self.assertFalse(normalize_lap(lap,[],{(16,90000)},set())['eligible'])
        self.assertFalse(normalize_lap(lap,[],set(),{(16,5)})['eligible'])
        self.assertFalse(normalize_lap({**lap,'duration_sector_3':21},[],set(),set())['eligible'])
        self.assertFalse(normalize_lap({**lap,'segments_sector_3':[2064]},[],set(),set())['eligible'])

    def test_recorded_time_join_integrates_speed_in_metres(self):
        start=pd.Timestamp('2024-01-01T00:00:00Z')
        car=[];position=[]
        for elapsed in np.arange(0,10.01,.5):
            stamp=(start+pd.Timedelta(seconds=float(elapsed))).isoformat()
            car.append({'date':stamp,'speed':360,'throttle':90,'brake':100 if elapsed>5 else 0,'n_gear':7,'rpm':10000})
            position.append({'date':stamp,'x':float(elapsed)*10,'y':float(elapsed)**2})
        with patch('backend.open_data.fetch',side_effect=lambda endpoint,**params:car if endpoint=='car_data' else position):
            trace=_trace(100,'16',{'time':10,'number':5},{'date_start':start.isoformat()})
        self.assertAlmostEqual(trace['samples']['distance'][-1],1000,places=8)
        self.assertEqual(trace['samples']['time'][0],0)
        self.assertEqual(trace['samples']['time'][-1],10)
        self.assertEqual(set(trace['samples']['brake']),{0,1})
        self.assertEqual(set(trace['samples']['gear']),{7})


if __name__=='__main__':
    unittest.main()
