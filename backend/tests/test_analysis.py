"""Synthetic numerical fixtures are test-only; the application never serves them."""
import unittest

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from backend.main import app
from backend.analysis import analyze, align
from backend.data import lap_info, scalar


def fixture():
    distance = np.linspace(0, 1000, 101)
    traces = []
    for i in range(2):
        traces.append({'samples': {'distance': distance.tolist(),
            'time': (distance/10+i*2).tolist(), 'speed': (100+.1*distance+i*3).tolist(),
            'throttle': (40+30*np.sin(distance/200+i*.2)).tolist(),
            'brake': (distance>500).astype(int).tolist(),
            'gear': (3+np.floor(distance/250)).tolist(),
            'rpm': (9000+distance*2+i*100).tolist()}})
    return {'traces':traces}


class NumericalTests(unittest.TestCase):
    def test_walkthrough_matrices_reproduce_each_returned_calculation(self):
        result = analyze(fixture(), features=['speed', 'throttle', 'gear'])
        audit = result['audit']
        raw, z = np.array(audit['raw']), np.array(audit['centered'])
        self.assertEqual(raw.shape, (800, 3))
        np.testing.assert_allclose(z, (raw-result['means'])/result['scales'], atol=1e-12)
        np.testing.assert_allclose(np.cov(z, rowvar=False), result['covariance'], atol=1e-12)
        contributions = np.array(audit['pca_contributions'])
        np.testing.assert_allclose(contributions.sum(axis=2), np.vstack(result['scores']), atol=1e-12)
        for i in range(3):
            np.testing.assert_allclose(audit['eigen_cv'][i], audit['eigen_lambda_v'][i], atol=1e-10)
        u, vt = np.array(audit['u']), np.array(audit['vt'])
        np.testing.assert_allclose((u*result['singular_values'])@vt, z, atol=1e-12)
        self.assertEqual(audit['input_counts'], [101, 101])
        self.assertLess(audit['orthogonality_error'], 1e-12)

    def test_rank_reconstructions_restore_units_and_report_honest_errors(self):
        for scaled in (True, False):
            result = analyze(fixture(), scale=scaled)
            audit = result['audit']
            raw, z = np.array(audit['raw']), np.array(audit['centered'])
            previous = float('inf')
            for record in audit['ranks']:
                restored = np.array(record['reconstructed'])
                approximation = (restored-result['means'])/result['scales']
                error = np.linalg.norm(z-approximation)/np.linalg.norm(z)
                self.assertAlmostEqual(error, record['relative_error'], places=10)
                self.assertLessEqual(record['relative_error'], previous+1e-12)
                self.assertAlmostEqual(record['relative_error']**2, 1-record['retained_energy'], places=10)
                np.testing.assert_allclose(np.sqrt(np.mean((raw-restored)**2, axis=0)), record['feature_rmse'], atol=1e-10)
                previous = record['relative_error']
            np.testing.assert_allclose(audit['ranks'][-1]['reconstructed'], raw, atol=1e-8)

    def test_shared_alignment_delta_and_discrete_channels(self):
        distance, arrays = align(fixture())
        self.assertEqual(len(distance),400)
        np.testing.assert_allclose(arrays[1][:,0]-arrays[0][:,0],2,atol=1e-12)
        self.assertTrue(set(arrays[0][:,3]).issubset({0,1}))
        self.assertTrue(np.all(arrays[0][:,4] == arrays[0][:,4].astype(int)))

    def test_eigenvalues_svd_and_pca_agree(self):
        result = analyze(fixture())
        eigen = np.array(result['eigenvalues'])
        singular = np.array(result['singular_values'])
        np.testing.assert_allclose(eigen,singular**2/(result['sample_count']-1),atol=1e-10)
        np.testing.assert_allclose(result['explained_variance'],eigen/eigen.sum(),atol=1e-10)
        self.assertLess(result['svd_relative_error'],1e-12)
        np.testing.assert_allclose(np.vstack(result['scores']).mean(axis=0),0,atol=1e-10)

    def test_linear_curve_fit_and_interval(self):
        result = analyze(fixture(),degree=1,start=200,end=700)
        self.assertGreaterEqual(result['fit']['distance'][0],200)
        self.assertLessEqual(result['fit']['distance'][-1],700)
        for fit in result['fit']['drivers']:
            self.assertLess(fit['rmse'],1e-7)
            self.assertAlmostEqual(fit['r_squared'],1,places=10)

    def test_no_overlap_fails_honestly(self):
        data = fixture()
        data['traces'][1]['samples']['distance'] = list(np.linspace(2000,3000,101))
        with self.assertRaisesRegex(ValueError,'overlapping'):
            analyze(data)

    def test_too_narrow_fit_rejected(self):
        with self.assertRaisesRegex(ValueError,'wider'):
            analyze(fixture(),start=10,end=11)

    def test_feature_selection_and_unscaled_centering(self):
        result = analyze(fixture(),features=['speed','throttle'],scale=False)
        self.assertEqual(result['scales'],[1,1])
        self.assertEqual(len(result['components']),2)
        self.assertAlmostEqual(result['means'][0],151.5)

    def test_bad_missing_channels_rejected(self):
        data = fixture()
        data['traces'][0]['samples']['rpm'] = [None]*101
        with self.assertRaisesRegex(ValueError,'Insufficient'):
            analyze(data)
        result = analyze(data, features=['speed','throttle'])
        self.assertEqual(result['features'], ['speed','throttle'])


class TimingAndAPITests(unittest.TestCase):
    def test_lap_eligibility_excludes_pits_deleted_generated(self):
        lap={'LapNumber':1,'LapTime':pd.Timedelta(seconds=90),'IsAccurate':True,
             'Deleted':False,'FastF1Generated':False,'PitInTime':pd.NaT,'PitOutTime':pd.NaT}
        self.assertTrue(lap_info(lap)['eligible'])
        self.assertIsNone(lap_info(lap)['sectors'][0])
        for key,value in [('Deleted',True),('IsAccurate',False),('IsAccurate',pd.NA),('FastF1Generated',True),('PitInTime',pd.Timedelta(seconds=50)),('LapTime',pd.NaT)]:
            self.assertFalse(lap_info({**lap,key:value})['eligible'],key)

    def test_scalar_nulls_and_numpy(self):
        self.assertIsNone(scalar(np.nan))
        self.assertEqual(scalar(np.int64(7)),7)
        self.assertIsInstance(scalar(np.bool_(True)),bool)

    def test_api_validation_and_expired_jobs(self):
        with TestClient(app) as client:
            self.assertEqual(client.get('/api/health').json()['status'],'ok')
            self.assertEqual(client.get('/api/jobs/expired').status_code,404)
            self.assertEqual(client.get('/api/schedule/2017').status_code,422)
            self.assertEqual(client.post('/api/compare',json={'year':2024,'round':1,'session':'Race','driver_a':'1','driver_b':'1','lap_a':1,'lap_b':1}).status_code,422)
            self.assertEqual(client.post('/api/analysis',json={'comparison_id':'expired'}).status_code,404)
            self.assertEqual(client.post('/api/analysis',json={'comparison_id':'expired','features':['speed','speed']}).status_code,422)
            self.assertEqual(client.post('/api/analysis',json={'comparison_id':'expired','start':100,'end':90}).status_code,422)


if __name__ == '__main__':
    unittest.main()
