import os
import glob
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

SCENARIO_MAP = {
    '1_Laboratory_and_Corridor': {'Laboratory': 'Laboratory', 'Corridor': 'Corridor'},
    '2_Meeting_Room': 'Meeting Room',
    '3_Auditorium': 'Auditorium'
}

BEST_TOPOLOGY = {
    'Laboratory':   '45Inward',
    'Corridor':     'FacetoFace',
    'Meeting Room': '45Inward',
    'Auditorium':   '45Inward'
}

def infer_scenario_from_path(filepath: str) -> str:
    parts = os.path.normpath(filepath).split(os.sep)
    scenario_folder, subfolder = None, None
    for i, part in enumerate(parts):
        if part.startswith(('1_', '2_', '3_')):
            scenario_folder = part
            if i + 1 < len(parts) and parts[i + 1] in ['Laboratory', 'Corridor']:
                subfolder = parts[i + 1]
            break
    if not scenario_folder:
        return 'Unknown'
    mapping = SCENARIO_MAP.get(scenario_folder, scenario_folder)
    if isinstance(mapping, dict):
        return mapping.get(subfolder, subfolder or scenario_folder)
    return mapping

def infer_split_and_topology(filepath: str):
    parts = os.path.normpath(filepath).split(os.sep)
    filename = os.path.basename(filepath).lower()
    split, topology = 'unknown', 'unknown'
    for part in parts:
        pl = part.lower()
        if pl in ['train', 'test1', 'test2']: split = pl
        if part in ['45Inward', 'FacetoFace']: topology = part
    if split == 'unknown':
        if '_train' in filename: split = 'train'
        elif '_test1' in filename: split = 'test1'
        elif '_test2' in filename: split = 'test2'
    if topology == 'unknown':
        if '45inward' in filename or '45_inward' in filename: topology = '45Inward'
        elif 'facetoface' in filename or 'face_to_face' in filename: topology = 'FacetoFace'
    return split, topology

def load_final_dataset(dataset_root: str = ".") -> pd.DataFrame:
    pattern = os.path.join(dataset_root, '**', 'final_dataset', '**', '*.csv')
    files = sorted(list(set(glob.glob(pattern, recursive=True))))
    if not files:
        files = sorted(glob.glob(os.path.join(dataset_root, '*.csv')))
    if not files:
        return pd.DataFrame()

    dfs = []
    for f in files:
        scenario = infer_scenario_from_path(f)
        split, topology = infer_split_and_topology(f)
        if topology == 'unknown' and scenario in BEST_TOPOLOGY:
            topology = BEST_TOPOLOGY[scenario]
        if split not in ['test1', 'test2']:
            continue
        try:
            df = pd.read_csv(f)
            df['scenario'] = scenario
            df['split'] = split
            df['topology'] = topology
            dfs.append(df)
        except Exception as e:
            pass
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

def remove_outliers(arr):
    if len(arr) == 0: return arr
    q25, q75 = np.percentile(arr, [25, 75])
    iqr = q75 - q25
    return arr[(arr >= q25 - 1.5 * iqr) & (arr <= q75 + 1.5 * iqr)]

def evaluate_azimuth_repeatability_mannwhitney(df: pd.DataFrame) -> pd.DataFrame:
    scenarios = ['Laboratory', 'Corridor', 'Meeting Room', 'Auditorium']
    results = []
    id_col = 'id' if 'id' in df.columns else 'point_id'
    az_cols = [c for c in df.columns if 'az_ublox' in c.lower()]

    for scen in scenarios:
        target_topo = BEST_TOPOLOGY[scen]
        sub1 = df[(df['scenario'] == scen) & (df['split'] == 'test1') & (df['topology'] == target_topo)]
        sub2 = df[(df['scenario'] == scen) & (df['split'] == 'test2') & (df['topology'] == target_topo)]

        if len(sub1) == 0 or len(sub2) == 0:
            continue

        std1_list, std2_list = [], []
        common_pts = set(sub1[id_col].unique()).intersection(set(sub2[id_col].unique()))
        
        for col in az_cols:
            for pt_id in common_pts:
                g1 = sub1[sub1[id_col] == pt_id][col].dropna()
                g2 = sub2[sub2[id_col] == pt_id][col].dropna()
                if len(g1) >= 5 and len(g2) >= 5:
                    std1_list.append(g1.std())
                    std2_list.append(g2.std())

        std1 = np.array(std1_list)
        std2 = np.array(std2_list)

        if len(std1) == 0 or len(std2) == 0:
            continue

        stat_all, p_all = mannwhitneyu(std1, std2, alternative='two-sided')
        std1_clean = remove_outliers(std1)
        std2_clean = remove_outliers(std2)
        stat_clean, p_clean = mannwhitneyu(std1_clean, std2_clean, alternative='two-sided')

        results.append({
            'Scenario': scen,
            'Topology': target_topo,
            'N_pairs': len(std1),
            'p_val_with_outliers': round(p_all, 4),
            'p_val_no_outliers': round(p_clean, 4),
            'H0_accepted': p_all > 0.05 and p_clean > 0.05
        })

    return pd.DataFrame(results)

if __name__ == '__main__':
    df = load_final_dataset()
    if not df.empty:
        res = evaluate_azimuth_repeatability_mannwhitney(df)
        print(res.to_string(index=False))
    else:
        print("No final dataset available to analyze.")