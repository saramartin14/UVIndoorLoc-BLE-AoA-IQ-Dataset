import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.ticker import MultipleLocator
from matplotlib.markers import MarkerStyle

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10

def parse_float_val(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).strip()
    cleaned = re.sub(r'[^\d.-]', '', val_str)
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def load_anchor_positions(room_path, config_name):
    file_options = [
        f"anchor_coordinates_{config_name}.csv", 
        f"anchors_coordinates_{config_name}.csv",
        f"anchor_coordinates.csv",
        f"anchors_coordinates.csv"
    ]
    for opt in file_options:
        path = os.path.join(room_path, "coordinates", opt)
        if os.path.exists(path):
            try:
                df_anc = pd.read_csv(path, skipinitialspace=True)
                df_anc.columns = [str(c).strip().lower() for c in df_anc.columns]
                
                col_x = 'x' if 'x' in df_anc.columns else 'x_coordinate'
                col_y = 'y' if 'y' in df_anc.columns else 'y_coordinate'
                col_z = 'z' if 'z' in df_anc.columns else 'z_coordinate'
                
                col_orient = next((c for c in df_anc.columns if c in [
                    'orientation', 'orientation_deg', 'heading', 'angle', 
                    'azimuth', 'boresight', 'orient', 'theta'
                ]), None)
                
                df_anc['idx'] = df_anc['anchor'].astype(str).str.extract(r'(\d+)').astype(int)
                df_anc = df_anc.sort_values('idx')

                pos_map = {}
                for _, row in df_anc.iterrows():
                    a_num = str(row['idx'])
                    orient_val = parse_float_val(row[col_orient]) if col_orient else 0.0
                    pos_map[a_num] = [
                        parse_float_val(row[col_x]), 
                        parse_float_val(row[col_y]), 
                        parse_float_val(row.get(col_z, 0.0)),
                        orient_val
                    ]
                return pos_map
            except Exception as e:
                print(f"[ERROR] Failed to read {opt}: {e}")
    return None

def get_ray_endpoints(x0, y0, angle_deg, xlim, ylim):
    """Computes the intersection of a ray starting at (x0, y0) with angle_deg against plot boundaries."""
    rad = np.radians(angle_deg)
    dx, dy = np.cos(rad), np.sin(rad)
    t_vals = []
    if abs(dx) > 1e-9:
        for bx in xlim:
            t = (bx - x0) / dx
            if t > 0:
                y_hit = y0 + t * dy
                if ylim[0] <= y_hit <= ylim[1]:
                    t_vals.append(t)
    if abs(dy) > 1e-9:
        for by in ylim:
            t = (by - y0) / dy
            if t > 0:
                x_hit = x0 + t * dx
                if xlim[0] <= x_hit <= xlim[1]:
                    t_vals.append(t)
    t_end = min(t_vals) if t_vals else 25.0
    return x0 + t_end * dx, y0 + t_end * dy

def main():
    print("=" * 75)
    print("SINGLE-SAMPLE POSITIONING ILLUSTRATION GENERATOR (LSTSQ vs. KNN)")
    print("=" * 75)
    
    scenario_map = {
        "1": ("Laboratory", "1_Laboratory_and_Corridor/Laboratory"),
        "2": ("Corridor", "1_Laboratory_and_Corridor/Corridor"),
        "3": ("Meeting_Room", "2_Meeting_Room"),
        "4": ("Auditorium", "3_Auditorium")
    }
    print("Select scenario (recommended: [1] Laboratory or [3] Meeting_Room or [4] Auditorium):")
    for k, v in scenario_map.items():
        print(f"  [{k}] {v[0]}")
    choice_scen = input("Scenario (1-4): ").strip()
    if choice_scen not in scenario_map:
        return
    scenario_name, base_path = scenario_map[choice_scen]
    
    if scenario_name == "Auditorium":
        config_name = "45Inward"
    else:
        choice_conf = input("Topology configuration ([1] 45Inward, [2] FaceToFace): ").strip()
        config_name = "45Inward" if choice_conf == "1" else "FaceToFace"
        
    split_name = input("Evaluation split ([1] TEST1, [2] TEST2) [default 1]: ").strip()
    split_name = "TEST2" if split_name == "2" else "TEST1"
    
    test_csv = f"{base_path}/final_dataset/Dataset_{scenario_name}_{config_name}_{split_name}.csv"
    train_csv = f"{base_path}/final_dataset/Dataset_{scenario_name}_{config_name}_TRAIN.csv"
    anchors_pos = load_anchor_positions(base_path, config_name)
    
    if not os.path.exists(test_csv) or not os.path.exists(train_csv) or not anchors_pos:
        print("[WARN] Missing CSV files (both TEST and TRAIN splits are required to illustrate KNN).")
        return

    df_test = pd.read_csv(test_csv)
    df_train = pd.read_csv(train_csv)
    
    all_ids = df_test['id'].unique()
    print(f"\nAvailable reference points in {split_name}: {', '.join(all_ids[:8])} ... (Total: {len(all_ids)})")
    selected_id = input("Enter reference point ID (e.g., S03P109 or S02P115): ").strip().upper()
    df_point = df_test[df_test['id'] == selected_id].reset_index(drop=True)
    
    if df_point.empty:
        print(f"[WARN] Reference point {selected_id} was not found.")
        return

    keys = list(anchors_pos.keys())
    feat_cols = [f'az_ublox_anchor{k}' for k in keys] + [f'el_ublox_anchor{k}' for k in keys] + [f'rssi_anchor{k}' for k in keys]
    feat_cols = [c for c in feat_cols if c in df_train.columns]
    
    train_clean = df_train.dropna(subset=feat_cols).copy()
    means = train_clean[feat_cols].mean()
    stds = train_clean[feat_cols].std().replace(0, 1)
    X_train_norm = ((train_clean[feat_cols] - means) / stds).values
    train_xy = train_clean[['real_x', 'real_y']].values
    k_neighbors = 5

    best_row_idx = 0
    best_combined_err = float('inf')
    best_lstsq_err = 0.0
    best_knn_err = 0.0
    best_unique_locs = 0
    
    for idx, row in df_point.iterrows():
        if row[feat_cols].isna().any():
            continue
        A, B = [], []
        for a_num in keys:
            local_az = row[f'az_ublox_anchor{a_num}']
            orient_deg = anchors_pos[a_num][3]
            global_az_rad = np.radians((-local_az + orient_deg) % 360.0)
            x_a, y_a = anchors_pos[a_num][0], anchors_pos[a_num][1]
            s, c = np.sin(global_az_rad), np.cos(global_az_rad)
            A.append([s, -c])
            B.append(s * x_a - c * y_a)
            
        pt, _, _, _ = np.linalg.lstsq(np.array(A), np.array(B), rcond=None)
        err_l = np.hypot(pt[0] - row['real_x'], pt[1] - row['real_y'])
        
        x_sample_norm = ((row[feat_cols].astype(float) - means) / stds).values
        dists = np.linalg.norm(X_train_norm - x_sample_norm, axis=1)
        nn_idx = np.argpartition(dists, k_neighbors)[:k_neighbors]
        w = 1.0 / (dists[nn_idx] + 1e-6)
        w /= w.sum()
        knn_pt = np.sum(train_xy[nn_idx] * w[:, None], axis=0)
        err_k = np.hypot(knn_pt[0] - row['real_x'], knn_pt[1] - row['real_y'])
        
        n_unique_locs = len(np.unique(np.round(train_xy[nn_idx], 3), axis=0))
        diversity_penalty = (k_neighbors - n_unique_locs) * 4.0
        
        score = max(err_l, err_k) + 0.3 * (err_l + err_k) + diversity_penalty
        if score < best_combined_err:
            best_combined_err = score
            best_row_idx = idx
            best_lstsq_err = err_l
            best_knn_err = err_k
            best_unique_locs = n_unique_locs

    row_input = input(
        f"Packet row index to plot (0 to {len(df_point)-1}) "
        f"[Press Enter for optimal #{best_row_idx} ({best_unique_locs} distinct neighbors): LSTSQ={best_lstsq_err:.2f}m, KNN={best_knn_err:.2f}m]: "
    ).strip()
    row_idx = int(row_input) if row_input.isdigit() and int(row_input) < len(df_point) else best_row_idx
    sample = df_point.iloc[row_idx]

    gt_x, gt_y = sample['real_x'], sample['real_y']

    # --- METHOD 1: GEOMETRIC TRIANGULATION (LSTSQ) ---
    A, B = [], []
    ray_data = []
    for a_num in keys:
        local_az = sample[f'az_ublox_anchor{a_num}']
        orient_deg = anchors_pos[a_num][3]
        global_az_deg = (-local_az + orient_deg) % 360.0
        global_az_rad = np.radians(global_az_deg)
        x_a, y_a = anchors_pos[a_num][0], anchors_pos[a_num][1]
        s, c = np.sin(global_az_rad), np.cos(global_az_rad)
        A.append([s, -c])
        B.append(s * x_a - c * y_a)
        ray_data.append((a_num, x_a, y_a, orient_deg, local_az, global_az_deg))

    lstsq_pt, _, _, _ = np.linalg.lstsq(np.array(A), np.array(B), rcond=None)
    lstsq_x, lstsq_y = lstsq_pt[0], lstsq_pt[1]
    err_lstsq = np.hypot(gt_x - lstsq_x, gt_y - lstsq_y)

    # --- METHOD 2: FINGERPRINTING BASELINE (KNN, k=5) ---
    x_sample_norm = ((sample[feat_cols].astype(float) - means) / stds).values
    dists = np.linalg.norm(X_train_norm - x_sample_norm, axis=1)
    train_clean['feat_dist'] = dists
    nearest_samples = train_clean.nsmallest(k_neighbors, 'feat_dist')
    weights = 1.0 / (nearest_samples['feat_dist'].values + 1e-6)
    weights /= weights.sum()
    
    knn_x = np.sum(nearest_samples['real_x'].values * weights)
    knn_y = np.sum(nearest_samples['real_y'].values * weights)
    err_knn = np.hypot(gt_x - knn_x, gt_y - knn_y)

    # --- COMPACT TWO-PANEL VISUALIZATION WITH SHARED LEGEND ---
    all_x = [anchors_pos[k][0] for k in keys]
    all_y = [anchors_pos[k][1] for k in keys]
    xlim = (min(all_x) - 1.5, max(all_x) + 1.5)
    ylim = (min(all_y) - 2.0, max(all_y) + 1.8)
    y_median = np.median(all_y)
    center_x = np.mean(all_x)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.2, 6.2), sharey=True)
    plt.subplots_adjust(wspace=0.08)

    def draw_base_room(ax):
        for a_num, coords in anchors_pos.items():
            anc_x, anc_y, _, predef_ori = coords
            rot_angle_deg = predef_ori - 90
            marker_style = MarkerStyle('^', fillstyle='full')
            marker_style._transform = marker_style.get_transform().rotate_deg(rot_angle_deg)
            ax.plot(anc_x, anc_y, marker=marker_style, markersize=12, color='black', zorder=5)
            
            offset_y = 0.65 if anc_y > y_median else -1.25
            ha_align = 'left' if anc_x < center_x else 'right'
            ax.text(anc_x + (-0.35 if anc_x < center_x else 0.25), anc_y + offset_y, f"A{a_num}", fontweight='bold', fontsize=10, ha=ha_align)

        ax.plot(gt_x, gt_y, marker='o', markersize=8.5, color='#2ca02c', zorder=6)
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.xaxis.set_major_locator(MultipleLocator(1))
        ax.yaxis.set_major_locator(MultipleLocator(2))
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel('X Coordinate [m]', fontsize=10)

    # PANEL (a): GEOMETRIC TRIANGULATION (LSTSQ)
    draw_base_room(ax1)
    ax1.set_ylabel('Y Coordinate [m]')

    for a_num, x_a, y_a, orient_deg, local_az, global_az_deg in ray_data:
        ax1.plot([x_a, gt_x], [y_a, gt_y], color='#2ca02c', linestyle='--', alpha=0.45, linewidth=1.3)
        end_x, end_y = get_ray_endpoints(x_a, y_a, global_az_deg, xlim, ylim)
        ax1.plot([x_a, end_x], [y_a, end_y], color='#d62728', linestyle=':', alpha=0.85, linewidth=2.0)

    ax1.plot(lstsq_x, lstsq_y, marker='X', markersize=9.5, color='#d62728', markeredgecolor='black', zorder=7)

    # PANEL (b): FINGERPRINTING BASELINE (KNN)
    draw_base_room(ax2)

    unique_train_pts = train_clean[['id', 'real_x', 'real_y']].drop_duplicates()
    ax2.scatter(unique_train_pts['real_x'], unique_train_pts['real_y'], color='#b0b0b0', alpha=0.45, s=28, zorder=2)

    unique_neighbors = nearest_samples[['real_x', 'real_y']].drop_duplicates()
    for _, n_row in unique_neighbors.iterrows():
        nx, ny = n_row['real_x'], n_row['real_y']
        ax2.plot([knn_x, nx], [knn_y, ny], color='#ff7f0e', linestyle='--', linewidth=1.4, alpha=0.85, zorder=5)
        ax2.scatter(nx, ny, color='#ff7f0e', edgecolor='black', linewidth=0.9, s=60, zorder=6)

    ax2.plot(knn_x, knn_y, marker='D', markersize=8.5, color='#9467bd', markeredgecolor='black', zorder=8)

    # UNIFIED SHARED LEGEND PLACED WELL BELOW THE AXES
    shared_handles = [
        mlines.Line2D([], [], color='black', marker='^', markersize=8, linestyle='None', label='Anchor Arrays'),
        mlines.Line2D([], [], color='#2ca02c', linestyle='--', linewidth=1.3, alpha=0.6, label='True Geometric Bearing'),
        mlines.Line2D([], [], color='#b0b0b0', marker='o', markersize=6, linestyle='None', label='Training Grid Points'),
        
        mlines.Line2D([], [], color='#2ca02c', marker='o', markersize=8, linestyle='None', label='Ground Truth'),
        mlines.Line2D([], [], color='#d62728', linestyle=':', linewidth=2.0, label='Reported Firmware Ray'),
        mlines.Line2D([], [], color='#ff7f0e', marker='o', markeredgecolor='black', markersize=7, linestyle='None', label=f'Top-{k_neighbors} Signal Neighbors'),
        
        mlines.Line2D([], [], color='#ff7f0e', linestyle='--', linewidth=1.4, label='Similarity Weighting'),
        mlines.Line2D([], [], color='#d62728', marker='X', markeredgecolor='black', markersize=9, linestyle='None', label=f'LSTSQ Estimate ({err_lstsq:.2f} m)'),
        mlines.Line2D([], [], color='#9467bd', marker='D', markeredgecolor='black', markersize=8, linestyle='None', label=f'KNN Estimate ({err_knn:.2f} m)')
    ]
    
    fig.legend(handles=shared_handles, loc='upper center', bbox_to_anchor=(0.51, 0.02), ncol=3, frameon=True, fontsize=8.8, columnspacing=1.5)

    out_pdf = f'results/fig_single_sample_illustration_{scenario_name}_{config_name}_{selected_id}_row{row_idx}.pdf'
    plt.savefig(out_pdf, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved successfully as '{out_pdf}'")
    plt.show()

if __name__ == '__main__':
    main()