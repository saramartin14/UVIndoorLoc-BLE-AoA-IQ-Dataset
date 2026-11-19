import os
import argparse
import glob
from typing import List, Tuple, Optional, Dict

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

SCENARIO_ORDER = ['Laboratory', 'Corridor', 'Meeting Room', 'Auditorium']
TOPOLOGY_LABELS = {
    '45Inward': '45° Inward',
    'FacetoFace': 'Face-to-Face'
}

SCENARIO_COLORS = {
    'Laboratory':   '#1f77b4',
    'Corridor':     '#ff7f0e',
    'Meeting Room': '#2ca02c',
    'Auditorium':   '#d62728',
}

SCENARIO_COLORS_LIGHT = {
    'Laboratory':   '#7fb3d5',
    'Corridor':     '#ffbb78',
    'Meeting Room': '#98df8a',
}

SEVEN_CONFIGS = [
    ('Laboratory',   '45Inward',   SCENARIO_COLORS['Laboratory']),
    ('Laboratory',   'FacetoFace', SCENARIO_COLORS_LIGHT['Laboratory']),
    ('Corridor',     '45Inward',   SCENARIO_COLORS['Corridor']),
    ('Corridor',     'FacetoFace', SCENARIO_COLORS_LIGHT['Corridor']),
    ('Meeting Room', '45Inward',   SCENARIO_COLORS['Meeting Room']),
    ('Meeting Room', 'FacetoFace', SCENARIO_COLORS_LIGHT['Meeting Room']),
    ('Auditorium',   '45Inward',   SCENARIO_COLORS['Auditorium']),
]

LINESTYLE_BY_TOPOLOGY = {
    '45Inward': '-',
    'FacetoFace': '--',
}

BEST_TOPOLOGY = {
    'Laboratory':   '45Inward',
    'Corridor':     'FacetoFace',
    'Meeting Room': '45Inward',
    'Auditorium':   '45Inward',
}

LABEL_SIZE = 11
TITLE_SIZE = 12
TICK_SIZE = 9

plt.rcParams.update({
    'font.size': TICK_SIZE,
    'figure.dpi': 150,
    'savefig.dpi': 600,
    'axes.labelsize': LABEL_SIZE,
    'axes.titlesize': TITLE_SIZE,
    'xtick.labelsize': TICK_SIZE,
    'ytick.labelsize': TICK_SIZE,
    'legend.fontsize': 9,
    'lines.linewidth': 1.3,
    'axes.grid': True,
    'grid.alpha': 0.25,
})

SCENARIO_MAP = {
    '1_Laboratory_and_Corridor': {'Laboratory': 'Laboratory', 'Corridor': 'Corridor'},
    '2_Meeting_Room': 'Meeting Room',
    '3_Auditorium': 'Auditorium'
}

# ---------------------------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------------------------

def parse_iq_column(val, expected_len: int = 164) -> Optional[np.ndarray]:
    if isinstance(val, (list, np.ndarray)):
        arr = np.asarray(val, dtype=float)
        return arr if arr.size == expected_len else None
    if isinstance(val, str):
        s = val.strip()
        if s.startswith('[') and s.endswith(']'):
            s = s[1:-1]
        for sep in [',', ' ']:
            try:
                arr = np.fromstring(s, sep=sep)
                if arr.size == expected_len:
                    return arr
            except Exception:
                continue
        try:
            arr = np.array(s.split(), dtype=float)
            if arr.size == expected_len:
                return arr
        except Exception:
            pass
    return None


def iq_to_complex(iq_array: np.ndarray) -> np.ndarray:
    return iq_array[0::2] + 1j * iq_array[1::2]


def infer_scenario_from_path(filepath: str) -> str:
    parts = os.path.normpath(filepath).split(os.sep)
    scenario_folder = None
    subfolder = None
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


def infer_split_and_topology(filepath: str) -> Tuple[str, str]:
    parts = os.path.normpath(filepath).split(os.sep)
    filename = os.path.basename(filepath).lower()
    path_lower = filepath.lower()

    split = 'unknown'
    topology = 'unknown'

    for part in parts:
        pl = part.lower()
        if pl in ['train', 'test1', 'test2']:
            split = pl
        if part in ['45Inward', 'FacetoFace']:
            topology = part

    if split == 'unknown':
        if '_train' in filename:   split = 'train'
        elif '_test1' in filename: split = 'test1'
        elif '_test2' in filename: split = 'test2'

    if topology == 'unknown':
        if '45inward' in path_lower or '45_inward' in path_lower:
            topology = '45Inward'
        elif 'facetoface' in path_lower or 'face_to_face' in path_lower:
            topology = 'FacetoFace'

    return split, topology


def find_all_csvs(dataset_root: str, tier_name: str) -> List[str]:
    pattern = os.path.join(dataset_root, '**', tier_name, '**', '*.csv')
    return sorted(list(set(glob.glob(pattern, recursive=True))))


def load_tier(dataset_root: str, tier_name: str,
              allowed_splits: Optional[List[str]] = None,
              allowed_topologies: Optional[List[str]] = None) -> pd.DataFrame:
    files = find_all_csvs(dataset_root, tier_name)
    if not files:
        raise FileNotFoundError(f"No CSV files found for '{tier_name}'")

    dfs = []
    for f in files:
        scenario = infer_scenario_from_path(f)
        split, topology = infer_split_and_topology(f)

        # Force topology in TEST2 when detected as unknown
        if topology == 'unknown' and scenario in BEST_TOPOLOGY:
            topology = BEST_TOPOLOGY[scenario]
        if topology == 'unknown' and scenario == 'Auditorium':
            topology = '45Inward'

        if allowed_splits is not None and split not in allowed_splits:
            continue
        if allowed_topologies is not None and topology not in allowed_topologies:
            continue

        try:
            df = pd.read_csv(f)
            df['scenario'] = scenario
            df['split'] = split
            df['topology'] = topology
            df['source_file'] = f
            dfs.append(df)
        except Exception as e:
            print(f"[WARN] Error reading {f}: {e}")

    if not dfs:
        raise ValueError(f"No data for tier={tier_name}")
    return pd.concat(dfs, ignore_index=True)


def detect_columns(df: pd.DataFrame) -> dict:
    cols = list(df.columns)
    result = {'iq': [], 'rssi': [], 'az': [], 'el': [], 'id': None}
    for c in cols:
        cl = c.lower()
        if any(x in cl for x in ['iq_anchor', 'iq_a', 'iq_data', 'raw_iq']):
            result['iq'].append(c)
        if any(x in cl for x in ['rssi_anchor', 'rssi_a']) or cl == 'rssi':
            result['rssi'].append(c)
        if any(x in cl for x in ['az_ublox', 'az_anchor', 'azimuth']) and 'el' not in cl:
            result['az'].append(c)
        if any(x in cl for x in ['el_ublox', 'el_anchor', 'elevation']):
            result['el'].append(c)
        if cl in ['id', 'point_id', 'session_id', 'point']:
            result['id'] = c
    return result


# ---------------------------------------------------------------------------
# FIGURES
# ---------------------------------------------------------------------------

def fig_iq_constellation_merged(final_df, col_map, output_dir, n_samples=4000):
    iq_cols = col_map['iq']
    if not iq_cols:
        print("[SKIP] iq_constellation_merged")
        return

    per_config_data = []
    for scen, topo, color in SEVEN_CONFIGS:
        sub = final_df[(final_df['scenario'] == scen) & (final_df['topology'] == topo)]
        if len(sub) > n_samples:
            sub = sub.sample(n_samples, random_state=42)
        all_I, all_Q, all_amp = [], [], []
        for _, row in sub.iterrows():
            for c in iq_cols:
                iq = parse_iq_column(row[c])
                if iq is not None:
                    S = iq_to_complex(iq)
                    all_I.extend(S.real)
                    all_Q.extend(S.imag)
                    all_amp.extend(np.abs(S))
        per_config_data.append((scen, topo, color, all_I, all_Q, all_amp))

    all_I_global = np.concatenate([d[3] for d in per_config_data if d[3]])
    all_Q_global = np.concatenate([d[4] for d in per_config_data if d[4]])
    all_amp_global = np.concatenate([d[5] for d in per_config_data if d[5]])
    iq_lim = max(np.max(np.abs(all_I_global)), np.max(np.abs(all_Q_global))) * 1.05
    amp_xlim = np.percentile(all_amp_global, 99.0) * 1.03

    n_cols = len(per_config_data)
    fig = plt.figure(figsize=(2.6 * n_cols, 6.8))
    gs = fig.add_gridspec(2, n_cols, hspace=0.38, wspace=0.15)

    for col, (scen, topo, color, all_I, all_Q, all_amp) in enumerate(per_config_data):
        ax = fig.add_subplot(gs[0, col])
        if all_I:
            ax.scatter(all_I, all_Q, s=0.3, alpha=0.22, c=color, rasterized=True)
        ax.set_xlim(-iq_lim, iq_lim)
        ax.set_ylim(-iq_lim, iq_lim)
        ax.set_aspect('equal')
        ax.set_title(f"{scen}\n{TOPOLOGY_LABELS[topo]}", fontsize=TITLE_SIZE-1)
        if col == 0: ax.set_ylabel('Quadrature (Q)', fontsize=LABEL_SIZE)
        else: ax.tick_params(labelleft=False)

        ax = fig.add_subplot(gs[1, col])
        if all_amp:
            ax.hist(all_amp, bins=50, color=color, alpha=0.85, edgecolor='black', linewidth=0.2)
        ax.set_xlim(0, amp_xlim)
        if col == 0: ax.set_ylabel('Count', fontsize=LABEL_SIZE)
        else: ax.tick_params(labelleft=False)
        ax.set_xlabel(r'$|S_k|$', fontsize=LABEL_SIZE-1)

    plt.savefig(os.path.join(output_dir, 'iq_constellation_merged.pdf'), bbox_inches='tight')
    plt.close()
    print("[OK] iq_constellation_merged.pdf")


def fig_rssi_cdf(final_df, col_map, output_dir):
    rssi_cols = col_map['rssi']
    if not rssi_cols:
        print("[SKIP] rssi_cdf")
        return

    fig, ax = plt.subplots(figsize=(6.5, 5))
    for scen, topo, color in SEVEN_CONFIGS:
        sub = final_df[(final_df['scenario'] == scen) & (final_df['topology'] == topo)]
        vals = []
        for c in rssi_cols:
            if c in sub.columns:
                vals.extend(sub[c].dropna().values)
        if not vals:
            continue
        vals_sorted = np.sort(vals)
        cdf = np.arange(1, len(vals_sorted)+1) / len(vals_sorted)
        ax.plot(vals_sorted, cdf, color=color, linestyle=LINESTYLE_BY_TOPOLOGY[topo],
                label=f"{scen} ({TOPOLOGY_LABELS[topo]})")

    ax.set_xlabel('RSSI [dBm]', fontsize=LABEL_SIZE+2)
    ax.set_ylabel('CDF', fontsize=LABEL_SIZE+2)
    ax.set_ylim(0, 1)
    ax.legend(fontsize=9, loc='upper left', framealpha=0.9)
    ax.grid(alpha=0.25)
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'rssi_cdf.pdf'), bbox_inches='tight')
    plt.close()
    print("[OK] rssi_cdf.pdf")


def fig_firmware_angles_cdf(final_df, col_map, output_dir):
    _fig_angle_cdf(final_df, col_map, output_dir, 'az', 'Azimuth',
                   'firmware_azimuth_cdf.pdf', (-95, 95))
    _fig_angle_cdf(final_df, col_map, output_dir, 'el', 'Elevation',
                   'firmware_elevation_cdf.pdf', (-120, 90))


def _fig_angle_cdf(final_df, col_map, output_dir, col_key, angle_name, filename, xlim):
    cols = col_map.get(col_key, [])
    if not cols:
        print(f"[SKIP] {filename}")
        return

    fig, ax = plt.subplots(figsize=(6.5, 5))

    for scen, topo, color in SEVEN_CONFIGS:
        sub = final_df[(final_df['scenario'] == scen) & (final_df['topology'] == topo)]
        vals = []
        for c in cols:
            if c in sub.columns:
                vals.extend(sub[c].dropna().values)
        if not vals:
            continue
        vals_sorted = np.sort(vals)
        cdf = np.arange(1, len(vals_sorted)+1) / len(vals_sorted)
        ax.plot(vals_sorted, cdf, color=color, linestyle=LINESTYLE_BY_TOPOLOGY[topo],
                label=f"{scen} ({TOPOLOGY_LABELS[topo]})")

    ax.set_xlabel(f'{angle_name} [°]', fontsize=LABEL_SIZE+2)
    ax.set_ylabel('CDF', fontsize=LABEL_SIZE+2)
    ax.set_xlim(xlim)
    ax.set_ylim(0, 1)
    ax.legend(fontsize=8.5, loc='upper left', framealpha=0.9)
    ax.grid(alpha=0.25)
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, filename), bbox_inches='tight')
    plt.close()
    print(f"[OK] {filename}")


def fig_temporal_repeatability(final_df, col_map, output_dir):
    rssi_cols = col_map['rssi']
    if not rssi_cols:
        print("[SKIP] temporal_repeatability")
        return

    id_col = col_map['id']
    all_split_data = {}
    global_max = 0.0

    for split in ['test1', 'test2']:
        data = []
        for scen in SCENARIO_ORDER:
            topo = BEST_TOPOLOGY[scen]
            sub = final_df[(final_df['scenario']==scen) & (final_df['split']==split) & (final_df['topology']==topo)]
            point_stds = []
            group_key = id_col if id_col else 'source_file'
            for _, grp in sub.groupby(group_key):
                vals = []
                for c in rssi_cols:
                    vals.extend(grp[c].dropna().values)
                if len(vals) >= 5:
                    point_stds.append(np.std(vals))
            data.append(point_stds)
            if point_stds:
                global_max = max(global_max, max(point_stds))
        all_split_data[split] = data

    ylim = global_max * 1.08 if global_max > 0 else None

    for split in ['test1', 'test2']:
        data = all_split_data[split]
        fig, ax = plt.subplots(figsize=(6.5, 5))
        bp = ax.boxplot(data, patch_artist=True, widths=0.6)
        labels = [f"{scen}\n({TOPOLOGY_LABELS[BEST_TOPOLOGY[scen]]})" for scen in SCENARIO_ORDER]
        ax.set_xticklabels(labels, rotation=12, fontsize=TICK_SIZE+2)
        for patch, scen in zip(bp['boxes'], SCENARIO_ORDER):
            patch.set_facecolor(SCENARIO_COLORS[scen])
            patch.set_alpha(0.78)
        if ylim:
            ax.set_ylim(0, ylim)
        ax.set_title(split.upper(), fontsize=TITLE_SIZE+1)
        ax.set_ylabel(r'$\sigma_{\mathrm{RSSI}}$ [dB]', fontsize=LABEL_SIZE+2)
        plt.tight_layout()
        fig.savefig(os.path.join(output_dir, f'temporal_repeatability_{split}.pdf'), bbox_inches='tight')
        plt.close()
        print(f"[OK] temporal_repeatability_{split}.pdf")


def fig_firmware_angle_stability(df, col_map, output_dir):
    """Same Y scale in TEST1 and TEST2."""
    az_cols = sorted(col_map.get('az', []))
    if not az_cols:
        print("[SKIP] firmware_angle_stability")
        return

    # Pass 1: data + global maximum
    all_splits_data = {}
    global_max = 0.0

    for split in ['test1', 'test2']:
        split_data = []
        pos = 0
        for scen in SCENARIO_ORDER:
            topo = BEST_TOPOLOGY[scen]
            sub = df[(df['scenario']==scen) & (df['split']==split) & (df['topology']==topo)]
            print(f"    {split} | {scen} | {topo} → {len(sub)} rows")

            for col in az_cols:
                point_stds = []
                if not sub.empty:
                    group_key = col_map['id'] if col_map['id'] else 'source_file'
                    for _, grp in sub.groupby(group_key):
                        vals = grp[col].dropna().values
                        if len(vals) >= 5:
                            point_stds.append(np.std(vals))
                split_data.append(point_stds)
                if point_stds:
                    global_max = max(global_max, max(point_stds))
            pos += len(az_cols) + 0.9

        all_splits_data[split] = split_data

    ylim = global_max * 1.08 if global_max > 0 else None
    print(f"  → Common Y scale: 0 – {ylim:.1f}°" if ylim else "")

    # Pass 2: plot
    for split in ['test1', 'test2']:
        split_data = all_splits_data[split]

        fig, ax = plt.subplots(figsize=(3.2 * len(SCENARIO_ORDER) + 2.0, 4.8))

        positions, colors = [], []
        scen_centers, scen_labels = [], []
        anchor_positions, anchor_labels = [], []

        pos = 0
        idx = 0
        for scen in SCENARIO_ORDER:
            topo = BEST_TOPOLOGY[scen]
            scen_start = pos
            for i in range(len(az_cols)):
                positions.append(pos)
                colors.append(SCENARIO_COLORS[scen])
                anchor_positions.append(pos)
                anchor_labels.append(f'A{i+1}')
                pos += 1
                idx += 1
            scen_centers.append(scen_start + (len(az_cols)-1)/2.0)
            scen_labels.append(f"{scen}\n({TOPOLOGY_LABELS[topo]})")
            pos += 0.9

        bp = ax.boxplot(split_data, positions=positions, widths=0.65, patch_artist=True)
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.78)

        ax.set_xticks(scen_centers)
        ax.set_xticklabels(scen_labels, fontsize=TICK_SIZE+1)
        ax.tick_params(axis='x', pad=14)

        ax_anchor = ax.secondary_xaxis('bottom')
        ax_anchor.set_xticks(anchor_positions)
        ax_anchor.set_xticklabels(anchor_labels, fontsize=8, color='dimgray')
        ax_anchor.tick_params(axis='x', length=3, pad=2)
        ax_anchor.spines['bottom'].set_visible(False)

        if ylim is not None:
            ax.set_ylim(0, ylim)

        ax.set_ylabel(r'$\sigma_{\mathrm{Azimuth}}$ [°]', fontsize=LABEL_SIZE+2)
        ax.set_title(f'{split.upper()} — selected topology (raw firmware azimuth)', fontsize=TITLE_SIZE)
        plt.tight_layout()
        fig.savefig(os.path.join(output_dir, f'firmware_angle_stability_{split}.pdf'), bbox_inches='tight')
        plt.close()
        print(f"[OK] firmware_angle_stability_{split}.pdf")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_root', default='./')
    parser.add_argument('--output_dir', default='./figures')
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    print("="*35)
    print("UVIndoorLoc-BLE-AoA&IQ — Figures")
    print("="*35)

    # 1. Signal-Level Characterization
    print("\n[1/2] Loading processed_iq_fusion (test1)...")
    df_signal = load_tier(args.dataset_root, 'processed_iq_fusion',
                          allowed_splits=['test1'],
                          allowed_topologies=['45Inward', 'FacetoFace'])
    col_map_signal = detect_columns(df_signal)

    print("\nGenerating characterization figures...")
    fig_iq_constellation_merged(df_signal, col_map_signal, args.output_dir)
    fig_rssi_cdf(df_signal, col_map_signal, args.output_dir)
    fig_firmware_angles_cdf(df_signal, col_map_signal, args.output_dir)

    # 2. Data Quality Assessment
    print("\n[2/2] Loading data for quality assessment...")
    df_angle = load_tier(args.dataset_root, 'processed_iq_fusion',
                         allowed_splits=['test1', 'test2'])
    col_map_angle = detect_columns(df_angle)

    print("\n[CHECK] Rows per scenario/split/topology:")
    print(df_angle.groupby(['scenario', 'split', 'topology']).size().unstack(fill_value=0))

    fig_firmware_angle_stability(df_angle, col_map_angle, args.output_dir)

    df_quality = load_tier(args.dataset_root, 'final_dataset',
                           allowed_splits=['test1', 'test2'])
    col_map_quality = detect_columns(df_quality)
    fig_temporal_repeatability(df_quality, col_map_quality, args.output_dir)

    print("\n" + "="*70)
    print("Figures generated in:", os.path.abspath(args.output_dir))
    print("="*70)


if __name__ == '__main__':
    main()