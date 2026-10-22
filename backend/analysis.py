"""Shared distance alignment and explicit numerical analysis of both recorded laps."""
import warnings
import numpy as np
from scipy.optimize import curve_fit
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

FEATURES = ['speed', 'throttle', 'brake', 'gear', 'rpm']


def align(comparison, count=400, required_features=None):
    arrays = []
    for trace in comparison['traces']:
        s = trace['samples']
        arr = np.array([s['distance'], s['time'], *[s[k] for k in FEATURES]], dtype=float).T
        required = [0, 1, *[FEATURES.index(f)+2 for f in (required_features or FEATURES)]]
        arr = arr[np.isfinite(arr[:, required]).all(axis=1)]
        arr = arr[np.argsort(arr[:, 0])]
        _, unique = np.unique(arr[:, 0], return_index=True)
        arrays.append(arr[unique])
    if any(len(a) < 10 for a in arrays):
        raise ValueError('Insufficient complete telemetry for shared mathematical analysis.')
    start, end = max(a[0,0] for a in arrays), min(a[-1,0] for a in arrays)
    if end <= start:
        raise ValueError('The selected laps have no overlapping recorded distance.')
    distance = np.linspace(start, end, count)
    aligned = []
    for a in arrays:
        columns = []
        for j in range(1, a.shape[1]):
            if j in (4, 5):  # brake and gear: preceding sample, never fractional states
                idx = np.clip(np.searchsorted(a[:,0], distance, side='right') - 1, 0, len(a)-1)
                columns.append(a[idx,j])
            else:
                columns.append(np.interp(distance, a[:,0], a[:,j]))
        aligned.append(np.array(columns).T)
    return distance, aligned


def analyze(comparison, degree=3, start=0, end=None, scale=True, features=None):
    selected = features or FEATURES
    distance, aligned = align(comparison, required_features=list(set(selected) | {'speed'}))
    indices = [FEATURES.index(k) for k in selected]
    raw = np.vstack([a[:,1:][:,indices] for a in aligned])
    scaler = StandardScaler(with_std=scale)
    centered = scaler.fit_transform(raw)
    if np.linalg.norm(centered) < 1e-10:
        raise ValueError('The selected telemetry channels have no variance in this comparison.')
    pca = PCA(n_components=len(indices), svd_solver='full')
    scores = pca.fit_transform(centered)
    u, singular, vt = np.linalg.svd(centered, full_matrices=False)
    covariance = np.cov(centered, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    reconstructed = (u * singular) @ vt
    ranks = []
    for rank in range(1, len(indices)+1):
        approximation = (u[:, :rank] * singular[:rank]) @ vt[:rank]
        restored = approximation * (scaler.scale_ if scale else 1) + scaler.mean_
        ranks.append({'rank': rank, 'relative_error': float(np.linalg.norm(centered-approximation)/np.linalg.norm(centered)),
                      'retained_energy': float(np.sum(singular[:rank]**2)/np.sum(singular**2)),
                      'feature_rmse': np.sqrt(np.mean((raw-restored)**2, axis=0)).tolist(),
                      'reconstructed': restored.tolist()})
    audit = {'raw': raw.tolist(), 'centered': centered.tolist(), 'pca_center': pca.mean_.tolist(),
             'u': u.tolist(), 'vt': vt.tolist(), 'ranks': ranks,
             'aligned_times': [a[:, 0].tolist() for a in aligned],
             'pca_contributions': ((centered-pca.mean_)[:, None, :] * pca.components_[None, :, :]).tolist(),
             'eigen_cv': [(covariance @ eigenvectors[:, i]).tolist() for i in order],
             'eigen_lambda_v': [(eigenvalues[i]*eigenvectors[:, i]).tolist() for i in order],
             'eigen_residuals': [float(np.linalg.norm(covariance @ eigenvectors[:, i] - eigenvalues[i]*eigenvectors[:, i])) for i in order],
             'orthogonality_error': float(np.linalg.norm(vt @ vt.T-np.eye(len(indices)))),
             'covariance_ddof': 1, 'standard_deviation_ddof': 0,
             'input_counts': [len(t['samples']['time']) for t in comparison['traces']],
             'source': comparison.get('source', 'Recorded comparison telemetry'),
             'pipeline': ['backend.analysis.align', 'sklearn.preprocessing.StandardScaler', 'numpy.cov',
                          'numpy.linalg.eigh', 'sklearn.decomposition.PCA', 'numpy.linalg.svd', 'scipy.optimize.curve_fit']}
    end = float(distance[-1]) if end is None else end
    mask = (distance >= start) & (distance <= end)
    x = distance[mask]
    if len(x) < degree + 3:
        raise ValueError('Choose a wider distance interval for this polynomial degree.')
    origin, span = float(x[0]), float(x[-1]-x[0])
    normalized = (x-origin)/span
    def polynomial(x_values, *coefficients):
        return np.polynomial.polynomial.polyval(x_values, coefficients)
    fits = []
    for arr in aligned:
        y = arr[mask,1]
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            coefficients, _ = curve_fit(polynomial, normalized, y, p0=np.zeros(degree+1), maxfev=10000)
        predicted = polynomial(normalized, *coefficients)
        residual = y-predicted
        total = np.sum((y-y.mean())**2)
        fits.append({'coefficients': coefficients.tolist(), 'observed': y.tolist(), 'fitted': predicted.tolist(),
                     'rmse': float(np.sqrt(np.mean(residual**2))),
                     'r_squared': float(1-np.sum(residual**2)/total) if total > 0 else None})
    n = len(distance)
    return {'audit': audit, 'distance': distance.tolist(), 'delta': (aligned[1][:,0]-aligned[0][:,0]).tolist(),
            'features': selected, 'scaled': scale, 'means': scaler.mean_.tolist(),
            'scales': scaler.scale_.tolist() if scale else [1.]*len(indices),
            'sample_count': len(centered), 'explained_variance': pca.explained_variance_ratio_.tolist(),
            'components': pca.components_.tolist(),
            'scores': [scores[:n,:].tolist(), scores[n:,:].tolist()],
            'covariance': covariance.tolist(), 'eigenvalues': eigenvalues[order].tolist(),
            'eigenvectors': eigenvectors[:,order].tolist(), 'singular_values': singular.tolist(),
            'svd_relative_error': float(np.linalg.norm(centered-reconstructed)/np.linalg.norm(centered)),
            'fit': {'degree': degree, 'distance': x.tolist(), 'origin': origin, 'span': span, 'drivers': fits}}
