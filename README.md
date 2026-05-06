# UVIndoorLoc-BLE-AoA&IQ Dataset

This repository contains the **UVIndoorLoc-BLE-AoA&IQ Dataset**, a collection of In-phase and Quadrature (I/Q) signal samples and Angle-of-Arrival (AoA) measurements based on the Bluetooth Low Energy (BLE) 5.1 specification. The project focuses on providing a BLE 5.1 AoA dataset by collecting data in three distinct real-world scenarios at the Escola Tècnica Superior d'Enginyeria (ETSE) of the University of Valencia (UV).

## :file_folder: Repository Structure

The project is organized into the following directories: 
- [`1_Laboratory_and_Corridor`](1_Laboratory_and_Corridor): Data and coordinates for Laboratory (59.286 $m^2$) and Corridor (135.235 $m^2$).
  - [`Corridor`](1_Laboratory_and_Corridor/Corridor)
    - [`coordinates`](1_Laboratory_and_Corridor/Corridor/coordinates): Contains CSV files with Cartesian (x,y,z) coordinates for anchors (Face-to-Face and 45º Inward topologies) and Ground Truth points.
    - [`final_dataset`](1_Laboratory_and_Corridor/Corridor/final_dataset): The final, cleaned CSV files ready for positioning analysis.
    - [`processed_iq_fusion`](1_Laboratory_and_Corridor/Corridor/processed_iq_fusion): Contains synchronized CSV files where data from all four anchors have been merged into a single stream using [`iq_fusion.py`](scripts/iq_fusion.py).
    - [`raw_data`](1_Laboratory_and_Corridor/Corridor/raw_data): Organized by subset (train, test1, test2) and topology. It contains the original CSV files for each individual anchor (4 files per point).
  - [`Laboratory`](1_Laboratory_and_Corridor/Laboratory)
    - [`coordinates`](1_Laboratory_and_Corridor/Laboratory/coordinates): Contains CSV files with Cartesian (x,y,z) coordinates for anchors (Face-to-Face and 45º Inward topologies) and Ground Truth points.
    - [`final_dataset`](1_Laboratory_and_Corridor/Laboratory/final_dataset): The final, cleaned CSV files ready for positioning analysis.
    - [`processed_iq_fusion`](1_Laboratory_and_Corridor/Laboratory/processed_iq_fusion): Contains synchronized CSV files where data from all four anchors have been merged into a single stream using [`iq_fusion.py`](scripts/iq_fusion.py).
    - [`raw_data`](1_Laboratory_and_Corridor/Laboratory/raw_data): Organized by subset (train, test1, test2) and topology. It contains the original CSV files for each individual anchor (4 files per point).
  - [`map`](1_Laboratory_and_Corridor/map): Map of the experimental setup for Scenario 1.
    - [`1_lab_corridor.png`](1_Laboratory_and_Corridor/map/1_lab_corridor.png)
- [`2_Meeting_Room`](2_Meeting_Room): Data and coordinates for Meeting Room (153.024 $m^2$) and its exterior corridor (34.368 $m^2$).
  - [`coordinates`](2_Meeting_Room/coordinates): Contains CSV files with Cartesian (x,y,z) coordinates for anchors (Face-to-Face and 45º Inward topologies) and Ground Truth points.
  - [`final_dataset`](2_Meeting_Room/final_dataset): The final, cleaned CSV files ready for positioning analysis.
  - [`map`](2_Meeting_Room/map): Map of the experimental setup for Scenario 2.
    - [`2_meeting_room.png`](2_Meeting_Room/map/2_meeting_room.png)
  - [`processed_iq_fusion`](2_Meeting_Room/processed_iq_fusion): Contains synchronized CSV files where data from all four anchors have been merged into a single stream using [`iq_fusion.py`](scripts/iq_fusion.py).
  - [`raw_data`](2_Meeting_Room/raw_data): Organized by subset (train, test1, test2) and topology. It contains the original CSV files for each individual anchor (4 files per point).
- [`3_Auditorium`](3_Auditorium): Data and coordinates for the 3D Auditorium scenario (152.170 $m^2$).
  - [`coordinates`](3_Auditorium/coordinates): Contains CSV files with Cartesian (x,y,z) coordinates for anchors (45º Inward topology) and Ground Truth points.
  - [`final_dataset`](3_Auditorium/final_dataset): The final, cleaned CSV files ready for positioning analysis.
  - [`map`](3_Auditorium/map): Map of the experimental setup for Scenario 3.
    - [`3_auditorium.png`](3_Auditorium/map/3_auditorium.png)
  - [`processed_iq_fusion`](3_Auditorium/processed_iq_fusion): Contains synchronized CSV files where data from all four anchors have been merged into a single stream using [`iq_fusion.py`](scripts/iq_fusion.py).
  - [`raw_data`](3_Auditorium/raw_data): Organized by subset (train, test1, test2). It contains the original CSV files for each individual anchor (4 files per point).
- [`scripts`](scripts): The core execution pipeline consisting of four scripts:
  - [`dataset_cleaning.py`](scripts/dataset_cleaning.py): Data cleaning and Ground Truth labeling.
  - [`generate_maps.py`](scripts/generate_maps.py): Map visualization.
  - [`iq_fusion.py`](scripts/iq_fusion.py): Synchronizes raw anchor data.
  - [`utils.py`](scripts/utils.py): Common helper functions for directory management and coordinate handling.
- [`requirements.txt`](requirements.txt): List of Python dependencies required to run the processing pipeline.



> [!NOTE]
> The folders _raw_data_, _processed_iq_fusion_, and _final_dataset_ are currently empty in this repository due to GitHub's file size limits. The full dataset is hosted on [Zenodo](https://doi.org/10.5281/zenodo.19823027).

## :rocket: Workflow

> [!IMPORTANT]
> All Python scripts must be executed from the **root directory** of this repository to ensure that relative file paths resolve correctly.

To replicate the results of the paper, execute the scripts in numerical order:

### 1. Environment Setup
Install all necessary dependencies.
```
pip install -r requirements.txt
```

### 2. Data Synchronization (IQ Fusion)
The first step in the pipeline involves merging the independent data streams from the four u-blox anchors. Since each anchor recorded data locally on a Raspberry Pi 5, this script uses a sub-millisecond temporal matching algorithm (with an empirical tolerance window of 80 ms) to ensure that the I/Q and angular samples from all nodes correspond to the same BLE advertising event.  
```
python scripts/iq_fusion.py
```
- Output: _processed_iq_fusion/_.
  
### 3. Dataset Cleaning and Labeling
Once synchronized, the data must be cleaned and aligned with the physical environment. This script performs noise reduction, removes incomplete sessions (fewer than four synchronized anchor responses), and maps the firmware-estimated angles to the global Cartesian coordinate system. It also assigns the precise Ground Truth (GT) coordinates to each sample based on the measurements captured via laser distance measurer.  
```
python scripts/dataset_cleaning.py
```
- Output: _final_dataset/_.

### 4. Visualization
To verify the experimental setup, anchor topologies, and point distribution, you can generate the scenario maps. This script generates scenario maps with anchor topologies and reference points (Training and Test).  
```
python scripts/generate_maps.py
```
- Output: PNG image showing the experimental setup for each of the three scenarios.

## :bar_chart: Dataset Summary
The dataset distribution is as follows:
| Scenario  | Training Points | Evaluation Points | Total Area |
| ------------- | ------------- | ------------- | ------------- |
| 1.a Laboratory  | 28  | 18  | $59.286\text{ m}^2$ | 
| 1.b Corridor  | 26  |  21  | $135.235\text{ m}^2$  |
| 2. Meeting Room  | 60  | 30  | $187.392\text{ m}^2$  | 
| 3. Auditorium  | 25  |  20  | $152.170\text{ m}^2$  |
