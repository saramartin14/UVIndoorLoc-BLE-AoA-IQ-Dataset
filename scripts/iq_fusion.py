import pandas as pd
import glob
import os
import re
from utils import ensure_dir, merge_node_data_iq, get_set_type

def load_coords(room_path, config_type):
    """
    Loads ground truth points and anchor coordinates from the room's metadata folder.
    """
    coord_dir = os.path.join(room_path, "coordinates")
    
    # Load Real Points (Ground Truth)
    pts_file = os.path.join(coord_dir, "points_coordinates.csv")
    pts_map = pd.read_csv(pts_file).set_index('id')[['x', 'y']].to_dict('index') if os.path.exists(pts_file) else {}

    # Load Anchor Coordinates (Sensor positions)
    anchor_pattern = os.path.join(coord_dir, f"*anchor*_{config_type}.csv")
    anchor_files = glob.glob(anchor_pattern)
    anchor_df = pd.read_csv(anchor_files[0]) if anchor_files else None
    
    if anchor_df is not None:
        anchor_df.columns = anchor_df.columns.str.strip()
    
    return pts_map, anchor_df

def process_leaf_folder(folder_path, room_path):
    """
    Processes a specific raw data folder and saves the results in:
    [room_path]/processed_iq_fusion/[sub_folder_structure]
    """
    if "3_Auditorium" in folder_path:
        config_type = "45Inward"

    elif "test2" in folder_path:
        if "/Corridor/" in folder_path:
            config_type = "FacetoFace"  
        else:
            config_type = "45Inward"    

    else:
        if "FacetoFace" in folder_path:
            config_type = "FacetoFace"
        else:
            config_type = "45Inward"
    pts_map, anchor_df = load_coords(room_path, config_type)
    
    all_files = glob.glob(os.path.join(folder_path, "capture_Anchor*.csv"))
    if not all_files:
        return

    # Group files by ID (ignoring timestamp drift in filenames)
    ids_in_folder = {}
    for f in all_files:
        match = re.search(r'ID(\d+)', os.path.basename(f))
        if match:
            id_str = match.group(0)
            if id_str not in ids_in_folder:
                ids_in_folder[id_str] = []
            ids_in_folder[id_str].append(f)

    # Output directory logic
    # Replicate the structure (e.g., train/45Inward) inside processed_iq_fusion
    raw_base_dir = os.path.join(room_path, "raw_data")
    sub_structure = os.path.relpath(folder_path, raw_base_dir)
    
    output_dir = os.path.join(room_path, "processed_iq_fusion", sub_structure)
    ensure_dir(output_dir)

    print(f"  Processing: {sub_structure} -> {len(ids_in_folder)} IDs detected")

    for id_tag, session_files in ids_in_folder.items():
        # Identify unique anchors present for this ID
        anchors_found = set(re.search(r'Anchor\d', f).group(0) for f in session_files)
        
        # Only proceed if we have all 4 anchors
        if len(anchors_found) < 4:
            continue

        final_files_to_merge = []
        for a in sorted(anchors_found):
            # Pick the first file found for each specific anchor
            anchor_file = [f for f in session_files if a in f][0]
            final_files_to_merge.append(anchor_file)

        dfs_to_merge = []
        for f in sorted(final_files_to_merge):
            anchor_name = re.search(r'Anchor\d', f).group(0)
            df = pd.read_csv(f)
            df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp']).sort_values('timestamp')

            # Dynamic renaming for node identification
            df = df.rename(columns={
                'rssi': f'rssi_{anchor_name}',
                'iq_data': f'iq_{anchor_name}',
                'az_ublox': f'az_{anchor_name}',
                'el_ublox': f'el_{anchor_name}',
                'ch': 'channel'
            })

            # Inject Anchor physical positions
            if anchor_df is not None:
                anchor_num = int(anchor_name[-1])
                row = anchor_df[anchor_df['Anchor'] == anchor_num]
                if not row.empty:
                    df[f'ax_{anchor_name}'] = row['X_coordinate'].values[0]
                    df[f'ay_{anchor_name}'] = row['Y_coordinate'].values[0]

            # Select relevant columns for fusion
            cols = ['timestamp', 'channel'] if len(dfs_to_merge) == 0 else ['timestamp']
            cols += [c for c in df.columns if anchor_name in c]
            dfs_to_merge.append(df[cols])

        # Perform time-based fusion
        # Using a tolerance to handle initial clock differences
        final_df = merge_node_data_iq(dfs_to_merge, tolerance=0.08)

        if not final_df.empty:
            id_num = int(id_tag.replace("ID", ""))
            set_type = get_set_type(id_num)
            
            # Inject Ground Truth coordinates
            if id_num in pts_map:
                final_df['real_x'] = pts_map[id_num]['x']
                final_df['real_y'] = pts_map[id_num]['y']

            final_df['config'] = config_type
            
            output_name = f"Fused_IQ_{set_type}_{id_tag}.csv"
            final_df.to_csv(os.path.join(output_dir, output_name), index=False)

def main():
    rooms = [
        "1_Laboratory_and_Corridor/Corridor",
        "1_Laboratory_and_Corridor/Laboratory",
        "2_Meeting_Room",
        "3_Auditorium"
    ]
    
    print("Starting IQ Fusion...")
    for room in rooms:
        print(f"\n>>> Scenario: {room}")
        raw_base = os.path.join(room, "raw_data")
        if not os.path.exists(raw_base):
            print(f"  [!] raw_data folder not found in {room}")
            continue
        
        # Recursively search for leaf folders containing capture files
        for root, dirs, files in os.walk(raw_base):
            if any(f.startswith('capture_Anchor') for f in files):
                process_leaf_folder(root, room)

if __name__ == "__main__":
    main()
