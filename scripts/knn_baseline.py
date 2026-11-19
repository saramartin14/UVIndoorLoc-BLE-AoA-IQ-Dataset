import os
import glob
import itertools
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import RobustScaler, MinMaxScaler, StandardScaler
import warnings
warnings.filterwarnings("ignore")

DATASET_ROOT = "./"
SCENARIO_ORDER = ['Laboratory', 'Corridor', 'Meeting Room', 'Auditorium']
TOPOLOGIES = ['45Inward', 'FacetoFace']
FEATURE_MODES = ['angles_only', 'hybrid']

N_FOLDS = 5
RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_iq(val, expected_len=164):
    if isinstance(val, (list, np.ndarray)):
        arr = np.asarray(val, dtype=float)
        return arr if arr.size == expected_len else None
    if isinstance(val, str):
        s = val.strip().strip('[]')
        for sep in [' ', ',']:
            try:
                arr = np.fromstring(s, sep=sep)
                if arr.size == expected_len:
                    return arr
            except Exception:
                pass
    return None


def iq_to_complex(iq):
    return iq[0::2] + 1j * iq[1::2]


def extract_features(df_subset, mode='hybrid'):
    """
    mode='angles_only' -> only az/el/rssi per anchor (firmware outputs)
    mode='hybrid'       -> angles_only + features derived from raw IQ

    Also returns 'groups': the physical point ID (e.g., S01P101) to which
    each row belongs. This is ESSENTIAL for leak-free CV: each point generates
    hundreds of nearly identical rows (60s capture at ~10Hz from a fixed
    position), so rows from the same point must NEVER be split between
    train and validation within the same fold.
    """
    X, y, groups = [], [], []
    for _, row in df_subset.iterrows():
        feats = []
        if 'ch' in row:
            feats.append(float(row['ch']) / 36.0)

        valid = True
        for i in range(1, 5):
            az_rad = np.radians(row[f'az_ublox_anchor{i}'])
            el_rad = np.radians(row[f'el_ublox_anchor{i}'])
            rssi_val = row[f'rssi_anchor{i}']
            feats.extend([np.sin(az_rad), np.cos(az_rad),
                          np.sin(el_rad), np.cos(el_rad), rssi_val])

            if mode == 'hybrid':
                iq_arr = parse_iq(row[f'iq_anchor{i}'])
                if iq_arr is None:
                    valid = False
                    break
                S = iq_to_complex(iq_arr)
                amp = np.abs(S)
                phase = np.unwrap(np.angle(S))
                t = np.arange(len(phase))
                # NOTE: assumes the first 8 samples correspond to the
                # reference period (single-antenna). Visually verify
                # amp/phase of those 8 samples before relying on this.
                p = np.polyfit(t[:8], phase[:8], 1)
                detrended = phase - np.polyval(p, t)
                feats.extend([np.mean(amp), np.std(amp), np.var(detrended[8:])])

        if valid:
            X.append(feats)
            y.append([row['real_x'], row['real_y'], row['real_z']])
            groups.append(row['id'])  # e.g., 'S01P101'

    return np.array(X), np.array(y), np.array(groups)


# ---------------------------------------------------------------------------
# Model selection WITHOUT data leakage
# ---------------------------------------------------------------------------

def select_best_config_cv(X_tr_raw, y_tr, groups_tr, coord_dim):
    """
    Selects (scaler, k, metric, weight) using GroupKFold CV *only* on train,
    grouping by physical point (groups_tr). This ensures that no row from a
    point in the validation fold has "twins" from the same point in the
    training fold. Never touches test.
    """
    scalers = {
        'robust': RobustScaler,
        'minmax': MinMaxScaler,
        'standard': StandardScaler
    }
    k_vals = [1, 3, 5, 7, 9]
    metrics = ['manhattan', 'euclidean']
    weights = ['distance', 'uniform']

    n_groups = len(np.unique(groups_tr))
    n_splits = min(N_FOLDS, n_groups)
    if n_splits < 2:
        raise ValueError(f"Only {n_groups} distinct points in train; "
                         f"cannot perform grouped CV.")
    gkf = GroupKFold(n_splits=n_splits)

    best_params = None
    best_cv_median = float('inf')

    for s_name, scaler_cls in scalers.items():
        for k, metric, weight in itertools.product(k_vals, metrics, weights):
            fold_errors = []
            for tr_idx, val_idx in gkf.split(X_tr_raw, y_tr, groups=groups_tr):
                scaler = scaler_cls()
                X_tr_fold = scaler.fit_transform(X_tr_raw[tr_idx])
                X_val_fold = scaler.transform(X_tr_raw[val_idx])

                knn = KNeighborsRegressor(n_neighbors=k, weights=weight, metric=metric)
                knn.fit(X_tr_fold, y_tr[tr_idx, :coord_dim])
                preds = knn.predict(X_val_fold)

                errs = np.linalg.norm(preds - y_tr[val_idx, :coord_dim], axis=1)
                fold_errors.append(errs)

            all_fold_errors = np.concatenate(fold_errors)
            cv_median = np.median(all_fold_errors)

            if cv_median < best_cv_median:
                best_cv_median = cv_median
                best_params = (s_name, k, metric, weight)

    return best_params, best_cv_median


def evaluate_on_test(X_tr_raw, y_tr, X_te_raw, y_te, coord_dim, params):
    """Trains ONCE on full train and evaluates ONCE on test (no leakage)."""
    s_name, k, metric, weight = params
    scalers = {'robust': RobustScaler(), 'minmax': MinMaxScaler(), 'standard': StandardScaler()}
    scaler = scalers[s_name]

    X_tr_s = scaler.fit_transform(X_tr_raw)
    X_te_s = scaler.transform(X_te_raw)

    knn = KNeighborsRegressor(n_neighbors=k, weights=weight, metric=metric)
    knn.fit(X_tr_s, y_tr[:, :coord_dim])
    preds = knn.predict(X_te_s)

    errors = np.linalg.norm(preds - y_te[:, :coord_dim], axis=1)
    return {
        'median': np.median(errors),
        'mae': np.mean(errors),
        'std': np.std(errors),
        'p75': np.percentile(errors, 75),
        'p95': np.percentile(errors, 95),
        'n_test': len(errors)
    }


def run_scenario(train_df, test_df, scenario_name, mode):
    X_tr_raw, y_tr, groups_tr = extract_features(train_df, mode=mode)
    X_te_raw, y_te, _ = extract_features(test_df, mode=mode)

    if len(X_tr_raw) == 0 or len(X_te_raw) == 0:
        return None

    coord_dim = 3 if scenario_name == 'Auditorium' else 2

    # 1) Hyperparameter selection ONLY with train (GroupKFold per point)
    best_params, cv_median = select_best_config_cv(X_tr_raw, y_tr, groups_tr, coord_dim)

    # 2) Final evaluation, ONCE, on test, with the chosen config
    test_res = evaluate_on_test(X_tr_raw, y_tr, X_te_raw, y_te, coord_dim, best_params)

    return best_params, cv_median, test_res


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_final_dataset():
    files = glob.glob(os.path.join(DATASET_ROOT, '**/final_dataset/*.csv'), recursive=True)
    if not files:
        files = glob.glob(os.path.join(DATASET_ROOT, '*.csv'))

    dfs = []
    for f in files:
        df = pd.read_csv(f)
        fname = os.path.basename(f).lower()

        if 'laboratory' in fname:
            df['scenario'] = 'Laboratory'
        elif 'corridor' in fname:
            df['scenario'] = 'Corridor'
        elif 'meeting' in fname:
            df['scenario'] = 'Meeting Room'
        elif 'auditorium' in fname:
            df['scenario'] = 'Auditorium'
        else:
            df['scenario'] = 'Unknown'

        if '45inward' in fname:
            df['topology'] = '45Inward'
        elif 'facetoface' in fname:
            df['topology'] = 'FacetoFace'
        else:
            df['topology'] = 'Unknown'

        if '_train' in fname:
            df['split'] = 'train'
        elif '_test1' in fname:
            df['split'] = 'test1'
        elif '_test2' in fname:
            df['split'] = 'test2'
        else:
            df['split'] = 'unknown'

        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


if __name__ == '__main__':
    print("Loading dataset...")
    df = load_final_dataset()

    results = []

    for scen in SCENARIO_ORDER:
        for topo in TOPOLOGIES:
            if scen == 'Auditorium' and topo == 'FacetoFace':
                continue

            sub = df[(df['scenario'] == scen) & (df['topology'] == topo)]
            train = sub[sub['split'] == 'train']

            # Evaluate test1 and test2 SEPARATELY (different days, independent
            # sessions) instead of mixing them: this allows direct comparison
            # against reference tables and verifies temporal stability.
            test_splits = {
                'test1': sub[sub['split'] == 'test1'],
                'test2': sub[sub['split'] == 'test2'],
            }

            if len(train) == 0:
                continue

            print(f"\n{'='*70}")
            print(f"{scen} | {topo}")

            for mode in FEATURE_MODES:
                for split_name, test_df in test_splits.items():
                    if len(test_df) == 0:
                        continue

                    out = run_scenario(train, test_df, scen, mode)
                    if out is None:
                        continue
                    params, cv_median, res = out
                    scaler_name, k, metric, weight = params

                    coord_dim = 3 if scen == 'Auditorium' else 2
                    dim_label = '3D' if coord_dim == 3 else '2D'

                    print(f"  [{mode:12s}|{split_name}] {dim_label} -> "
                          f"CV median (train): {cv_median:.3f} m | "
                          f"TEST median: {res['median']:.3f} m | "
                          f"TEST MAE: {res['mae']:.3f}+-{res['std']:.3f} m | "
                          f"P75: {res['p75']:.3f} m | P95: {res['p95']:.3f} m | "
                          f"n_test={res['n_test']}")
                    print(f"      params: scaler={scaler_name}, k={k}, metric={metric}, weight={weight}")

                    results.append({
                        'scenario': scen, 'topology': topo, 'mode': mode,
                        'test_split': split_name, 'coord_dim': dim_label,
                        'cv_median': cv_median, **res, 'params': params
                    })

    results_df = pd.DataFrame(results)
    results_df.to_csv('results/knn_baseline_results.csv', index=False)
    print(f"\nResults saved to results/knn_baseline_results.csv")