import pandas as pd
import glob
import os
import re
from utils import ensure_dir, extract_id

SCENARIOS = {
    "Laboratory": {
        "path": "1_Laboratory_and_Corridor/Laboratory",
        "configs": ["45Inward", "FacetoFace"],
        "best_config": "45Inward",
        "prefix": "S01",
        "nlos_file": "laboratory_nlos.csv"
    },
    "Corridor": {
        "path": "1_Laboratory_and_Corridor/Corridor",
        "configs": ["45Inward", "FacetoFace"],
        "best_config": "FacetoFace",
        "prefix": "S01",
        "nlos_file": "corridor_nlos.csv"
    },
    "Meeting_Room": {
        "path": "2_Meeting_Room",
        "configs": ["45Inward", "FacetoFace"],
        "best_config": "45Inward",
        "prefix": "S02",
        "nlos_file": "meeting_room_nlos.csv"
    },
    "Auditorium": {
        "path": "3_Auditorium",
        "configs": ["45Inward"],
        "best_config": "45Inward",
        "prefix": "S03",
        "nlos_file": "auditorium_nlos.csv"
    }
}

def load_nlos_labels(base_path, nlos_filename):
    nlos_path = os.path.join(base_path, "nlos_labels", nlos_filename)
    if not os.path.exists(nlos_path):
        print(f"  [INFO] No NLoS file found at: {nlos_path}")
        return None

    df_nlos = pd.read_csv(nlos_path)
    df_nlos.columns = [c.strip() for c in df_nlos.columns]

    if "id" not in df_nlos.columns:
        print(f"  [WARN] 'id' column missing in {nlos_path}")
        return None

    df_nlos["id"] = df_nlos["id"].astype(str).str.strip()

    rename_map = {}
    for i in range(1, 5):
        for candidate in [f"A{i}", f"a{i}", f"anchor{i}", f"nlos_a{i}"]:
            if candidate in df_nlos.columns:
                rename_map[candidate] = f"nlos_anchor{i}"
                break

    df_nlos = df_nlos.rename(columns=rename_map)
    nlos_cols = [f"nlos_anchor{i}" for i in range(1, 5) if f"nlos_anchor{i}" in df_nlos.columns]

    if not nlos_cols:
        print(f"  [WARN] No anchor LoS/NLoS columns found in {nlos_path}")
        return None

    df_nlos = df_nlos[["id"] + nlos_cols].drop_duplicates(subset=["id"])
    for col in nlos_cols:
        df_nlos[col] = pd.to_numeric(df_nlos[col], errors="coerce").astype("Int64")

    return df_nlos

def clean_scenarios():
    current_root = os.getcwd()

    for name, info in SCENARIOS.items():
        base_path = os.path.join(current_root, info['path'])
        best_cfg = info.get("best_config", "45Inward").lower()
        scen_prefix = info.get("prefix", "S01")
        nlos_filename = info.get("nlos_file", f"{name.lower()}_nlos.csv")

        df_nlos = load_nlos_labels(base_path, nlos_filename)

        for config in info['configs']:
            print(f"\n--- Processing {name} ({config}) ---")

            input_dir = os.path.join(base_path, "processed_iq_fusion")
            coords_path = os.path.join(base_path, "coordinates", "points_coordinates.csv")
            output_dir = os.path.join(base_path, "final_dataset")

            if not os.path.exists(input_dir) or not os.path.exists(coords_path):
                print(f"  [WARN] Missing input_dir or coords_path for {name} ({config})")
                continue

            ensure_dir(output_dir)
            df_coords = pd.read_csv(coords_path)
            df_coords.columns = [c.strip().lower() for c in df_coords.columns]

            all_found_files = glob.glob(os.path.join(input_dir, "**/*.csv"), recursive=True)
            files = []

            config_l = config.lower()
            for f in all_found_files:
                f_l = f.lower()

                if config_l in f_l:
                    files.append(f)
                elif ("test2" in f_l or "auditorium" in f_l) and (config_l == best_cfg):
                    files.append(f)

            if not files:
                print(f"  No files were found for {config}")
                continue

            data_by_set = {}

            for f in files:
                pid = extract_id(os.path.basename(f))
                if pid is None:
                    continue

                f_l = f.lower()
                if "test2" in f_l: set_label = "test2"
                elif "test1" in f_l: set_label = "test1"
                elif "train" in f_l: set_label = "train"
                else: set_label = "general"

                search_id = f"P{str(pid).zfill(3)}"
                gt = df_coords[df_coords['id'].astype(str).str.contains(search_id)]
                if gt.empty:
                    continue

                df = pd.read_csv(f)
                df.columns = [c.lower() for c in df.columns]

                rename_map = {'channel': 'ch'}
                for col in df.columns:
                    num_match = re.search(r'anchor(\d+)', col)
                    if num_match:
                        n = num_match.group(1)
                        if 'az_' in col: rename_map[col] = f'az_ublox_anchor{n}'
                        elif 'el_' in col: rename_map[col] = f'el_ublox_anchor{n}'
                        elif 'rssi_' in col: rename_map[col] = f'rssi_anchor{n}'
                        elif 'iq_' in col: rename_map[col] = f'iq_anchor{n}'

                df = df.rename(columns=rename_map)

                # Assign dynamic scenario point ID (S01, S02, S03)
                df['id'] = f"{scen_prefix}P{str(pid).zfill(3)}"

                # Ground truth positions
                df['real_x'] = gt.iloc[0]['x']
                df['real_y'] = gt.iloc[0]['y']
                col_z = next((c for c in df_coords.columns if c in ['z', 'real_z', 'z_coordinate']), None)
                df['real_z'] = gt.iloc[0][col_z] if col_z else 0.0

                # Tag orientation from points_coordinates.csv
                col_orient = next((c for c in df_coords.columns if c in ['orientation', 'tag_orientation', 'orient']), None)
                if col_orient and col_orient in gt.columns:
                    df['tag_orientation_deg'] = gt.iloc[0][col_orient]

                # Zone flag (e.g., inside / outside_partition)
                col_zone = next((c for c in df_coords.columns if c in ['zone', 'area', 'region']), None)
                if col_zone and col_zone in gt.columns:
                    df['zone'] = gt.iloc[0][col_zone]

                if set_label not in data_by_set:
                    data_by_set[set_label] = []
                data_by_set[set_label].append(df)

            for set_label, data_list in data_by_set.items():
                final_df = pd.concat(data_list, ignore_index=True)

                if df_nlos is not None and "id" in final_df.columns:
                    final_df["id"] = final_df["id"].astype(str).str.strip()
                    final_df = pd.merge(final_df, df_nlos, on="id", how="left")

                ordered_cols = ['id', 'timestamp', 'ch']
                for i in range(1, 5):
                    ordered_cols += [
                        f'az_ublox_anchor{i}',
                        f'el_ublox_anchor{i}',
                        f'rssi_anchor{i}',
                        f'iq_anchor{i}',
                        f'nlos_anchor{i}'
                    ]
                ordered_cols += ['real_x', 'real_y', 'real_z', 'tag_orientation_deg', 'zone']

                existing_cols = [c for c in ordered_cols if c in final_df.columns]
                final_df = final_df[existing_cols].sort_values(by=['id', 'timestamp'])

                save_filename = f"Dataset_{name}_{config}_{set_label.upper()}.csv"
                final_df.to_csv(os.path.join(output_dir, save_filename), index=False)
                print(f"  Saved: {save_filename} ({len(final_df)} samples)")

if __name__ == "__main__":
    clean_scenarios()