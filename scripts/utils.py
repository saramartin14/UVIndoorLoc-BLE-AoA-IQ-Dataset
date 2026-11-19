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

def merge_node_data_iq(dfs_list, tolerance=0.020):
    """
    Sincroniza las 4 anclas buscando coincidencia exacta en el contador
    de paquetes (pac) y canal publicitario (channel/ch), con tolerancia temporal <= 20 ms.
    """
    if not dfs_list or len(dfs_list) < 4:
        return pd.DataFrame()

    # 1. Normalizar nombres de columnas de canal en todas las anclas
    for df in dfs_list:
        if 'ch' in df.columns and 'channel' not in df.columns:
            df.rename(columns={'ch': 'channel'}, inplace=True)

    master_df = dfs_list[0].sort_values('timestamp').reset_index(drop=True)

    # 2. Si 'pac' y 'channel' existen en todas las anclas, hacer merge por ['pac', 'channel']
    has_pac = all('pac' in df.columns for df in dfs_list)
    has_chan = all('channel' in df.columns for df in dfs_list)

    if has_pac and has_chan:
        for next_df in dfs_list[1:]:
            next_sorted = next_df.sort_values('timestamp').reset_index(drop=True)
            master_df = pd.merge(
                master_df,
                next_sorted,
                on=['pac', 'channel'],
                suffixes=('', '_next')
            )
            # Filtrar parejas si la diferencia de tiempo real supera los 20 ms
            if 'timestamp_next' in master_df.columns:
                time_diff = (master_df['timestamp'] - master_df['timestamp_next']).abs()
                master_df = master_df[time_diff <= tolerance].drop(columns=['timestamp_next'])

        return master_df.dropna().reset_index(drop=True)

    # Fallback si por alguna razón faltara 'pac' en algún archivo
    for next_df in dfs_list[1:]:
        master_df = pd.merge_asof(
            master_df.sort_values('timestamp'),
            next_df.sort_values('timestamp'),
            on='timestamp',
            by='channel' if has_chan else None,
            direction='nearest',
            tolerance=tolerance
        )

    return master_df.dropna().reset_index(drop=True)

def get_set_type(pid):
    """Classification: Training < 100, Test >= 100."""
    if pid is None: return "OTHERS"
    return "TRAIN" if pid < 100 else "TEST"

def apply_aoa_math(value, offset):
    """Correction formula: (-Azimuth + Anchor_Orientation) % 360."""
    return (-value + offset) % 360