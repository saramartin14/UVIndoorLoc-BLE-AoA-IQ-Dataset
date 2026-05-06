import matplotlib.pyplot as plt
import pandas as pd
import os
import re
from matplotlib.lines import Line2D
from matplotlib.markers import MarkerStyle
from utils import ensure_dir

def get_clean_num(val):
    try:
        s = re.sub(r'[^0-9.\-]', '', str(val))
        return float(s) if s else 0.0
    except: return 0.0

def get_color(pid_raw, room_type):
    s = re.sub(r'\D', '', str(pid_raw))
    pid = int(s) % 1000 if s else 0
    room = room_type.lower()
    if "lab" in room: return 'red' if 50 <= pid <= 77 else 'yellow'
    if "corridor" in room: return 'red' if 1 <= pid <= 26 else 'yellow'
    if "meeting" in room: return 'red' if 1 <= pid <= 60 else 'yellow'
    if "auditorium" in room: return 'red' if 1 <= pid <= 27 else 'yellow'
    return 'yellow'

def plot_points_and_anchors(ax, room_path, room_type, anchor_file):
    path_p = os.path.join(room_path, "coordinates/points_coordinates.csv")
    if os.path.exists(path_p):
        df_p = pd.read_csv(path_p)
        df_p.columns = [c.strip().lower() for c in df_p.columns]
        
        for _, row in df_p.iterrows():
            x, y = get_clean_num(row['x']), get_clean_num(row['y'])
            ang = get_clean_num(row['orientation'])
            raw_id = row['id']
            color = get_color(raw_id, room_type)
            
            m = MarkerStyle("^")
            m._transform.rotate_deg(ang - 90)
            ax.scatter(x, y, marker=m, s=150, color=color, edgecolors='black', linewidths=0.5, zorder=3)

    path_a = os.path.join(room_path, "coordinates", anchor_file)
    if os.path.exists(path_a):
        df_a = pd.read_csv(path_a)
        df_a.columns = [c.strip().lower() for c in df_a.columns]
        for _, row in df_a.iterrows():
            ax_x, ax_y = get_clean_num(row['x_coordinate']), get_clean_num(row['y_coordinate'])
            ax_ang = get_clean_num(row['orientation'])
            aid_num = int(get_clean_num(row['anchor']))
            
            m = MarkerStyle("^")
            m._transform.rotate_deg(ax_ang - 90)
            ax.scatter(ax_x, ax_y, marker=m, s=350, color='black', edgecolors='white', zorder=10)
            
            # Lógica de etiquetas: Meeting Room (1,2 abajo) | Otros (1,3 abajo)
            if "meeting" in room_type.lower() or "auditorium" in room_type.lower():
                offset = -0.4 if aid_num in [1, 2] else 0.4
            else:
                offset = -0.6 if aid_num in [1, 3] else 0.6
            
            ax.text(ax_x, ax_y + offset, f"A{aid_num}", 
                    fontweight='bold', ha='center', fontsize=11, 
                    va='top' if offset < 0 else 'bottom')

def generate_final_pngs():
    ensure_dir("1_Laboratory_and_Corridor/map")
    ensure_dir("2_Meeting_Room/map")
    ensure_dir("3_Auditorium/map")
    plt.rcParams.update({'font.family': 'serif', 'font.size': 10})
    
    legend_elements = [
        Line2D([0], [0], marker='^', color='w', markerfacecolor='red', markersize=10, label='Training Point'),
        Line2D([0], [0], marker='^', color='w', markerfacecolor='yellow', markersize=10, label='Test Point'),
        Line2D([0], [0], marker='^', color='w', markerfacecolor='black', markersize=12, label='Anchor')
    ]

    # --- MAP 1: LAB & CORRIDOR ---
    fig1, ax1 = plt.subplots(figsize=(25, 12))
    plot_points_and_anchors(ax1, "1_Laboratory_and_Corridor/Laboratory", "lab", "anchor_coordinates_45Inward.csv")
    plot_points_and_anchors(ax1, "1_Laboratory_and_Corridor/Corridor", "corridor", "anchor_coordinates_FacetoFace.csv")
    ax1.set_aspect('equal')
    ax1.grid(True, linestyle=':', alpha=0.3)
    ax1.set_xlim(-22, 42)
    ax1.set_ylim(-3, 10)
    ax1.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.20), ncol=3)
    fig1.savefig("1_Laboratory_and_Corridor/map/1_lab_corridor.png", dpi=300, bbox_inches='tight')
    plt.close(fig1)

    # --- MAP 2: MEETING ROOM ---
    fig2, ax2 = plt.subplots(figsize=(12, 18))
    plot_points_and_anchors(ax2, "2_Meeting_Room", "meeting", "anchor_coordinates_45Inward.csv")
    ax2.set_aspect('equal')
    ax2.grid(True, linestyle=':', alpha=0.3)
    ax2.set_xlim(-3, 9) 
    ax2.set_ylim(-2, 19)
    ax2.set_xlabel("X-coordinate (m)", fontweight='bold')
    ax2.set_ylabel("Y-coordinate (m)", fontweight='bold')
    ax2.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.12), ncol=3)
    fig2.savefig("2_Meeting_Room/map/2_meeting_room.png", dpi=300, bbox_inches='tight')
    plt.close(fig2)

    # --- MAP 3: AUDITORIUM ---
    fig3, ax3 = plt.subplots(figsize=(15, 15))
    plot_points_and_anchors(ax3, "3_Auditorium", "auditorium", "anchors_coordinates_45Inward.csv")
    ax3.set_aspect('equal')
    ax3.grid(True, linestyle=':', alpha=0.3)
    ax3.relim()
    ax3.autoscale_view()
    ax3.set_xlabel("X-coordinate (m)", fontweight='bold')
    ax3.set_ylabel("Y-coordinate (m)", fontweight='bold')
    ax3.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.12), ncol=3)
    fig3.savefig("3_Auditorium/map/3_auditorium.png", dpi=300, bbox_inches='tight')
    plt.close(fig3)

    print("Generated maps.")

if __name__ == "__main__":
    generate_final_pngs()
