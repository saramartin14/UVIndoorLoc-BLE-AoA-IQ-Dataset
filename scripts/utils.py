import pandas as pd
import os
import re

def ensure_dir(path):
    """Creates the directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def extract_id(filename):
    """
    Extracts the numeric ID from the filename.
    Supports both 'P' prefix (S01P025) and 'ID' prefix (ID62).
    """
    if isinstance(filename, str):
        match_p = re.search(r'P(\d+)', filename)
        if match_p:
            return int(match_p.group(1))
        
        match_id = re.search(r'ID(\d+)', filename)
        if match_id:
            return int(match_id.group(1))
            
    return None

def merge_node_data_iq(dfs_list, tolerance=0.08):
    if not dfs_list: return pd.DataFrame()
    master_df = dfs_list[0]
    for next_df in dfs_list[1:]:
        master_df = pd.merge_asof(
            master_df, next_df, 
            on='timestamp', direction='nearest', 
            tolerance=tolerance
        )
    return master_df.dropna()

def get_set_type(pid):
    """Classification: Training < 100, Test >= 100."""
    if pid is None: return "OTHERS"
    return "TRAIN" if pid < 100 else "TEST"

def apply_aoa_math(value, offset):
    """Correction formula: (-Azimuth + Anchor_Orientation) % 360."""
<<<<<<< HEAD
    return (-value + offset) % 360
=======
    return (-value + offset) % 360
>>>>>>> 3c36856 (Repository structure and scripts)
