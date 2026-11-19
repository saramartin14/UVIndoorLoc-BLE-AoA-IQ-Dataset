# UVIndoorLoc-BLE-AoA&IQ Dataset

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19823027.svg)](https://doi.org/10.5281/zenodo.19823027)
![Python Version](https://img.shields.io/badge/python-3.13.13-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-orange.svg)

This repository contains the **UVIndoorLoc-BLE-AoA&IQ Dataset**, a collection of In-phase and Quadrature (I/Q) signal samples and Angle-of-Arrival (AoA) measurements based on the Bluetooth Low Energy (BLE) 5.1 specification. The project focuses on providing a BLE 5.1 AoA dataset by collecting data in three distinct real-world scenarios at the Escola Tècnica Superior d'Enginyeria (ETSE) of the University of Valencia (UV).

> [!NOTE]
> **Version Information:**
> - **Version 2.0 (Current):** Updated dataset release including per-anchor binary LoS/NLoS visibility annotations (`0` for LoS, `1` for NLoS) stored in `nlos_labels/` and integrated as `nlos_anchor1`–`nlos_anchor4` columns in `final_dataset/`, a strict 20 ms cross-anchor synchronization window, and updated processing, visualization, and baseline scripts.
> - **Version 1.0 (`v1.0-ipin2026`):** Initial release associated with the IPIN 2026 paper (80 ms synchronization window, without LoS/NLoS labels). Available via the GitHub release `v1.0-ipin2026` and Zenodo version history to reproduce the IPIN 2026 results.

## :file_folder: Repository Structure

The project is organized into the following directories: 
- [`1_Laboratory_and_Corridor`](1_Laboratory_and_Corridor): Data and coordinates for Laboratory (59.286 $m^2$) and Corridor (135.235 $m^2$).
  - [`Corridor`](1_Laboratory_and_Corridor/Corridor)
    - [`coordinates`](1_Laboratory_and_Corridor/Corridor/coordinates): Contains CSV files with Cartesian (x,y,z) coordinates for anchors (Face-to-Face and 45º Inward topologies) and Ground Truth points.
    - [`final_dataset`](1_Laboratory_and_Corridor/Corridor/final_dataset): The final, cleaned CSV files ready for positioning analysis.
    - [`nlos_labels`](1_Laboratory_and_Corridor/Corridor/nlos_labels): Per-anchor binary LoS/NLoS annotations (`0` = LoS, `1` = NLoS) per reference point.
    - [`processed_iq_fusion`](1_Laboratory_and_Corridor/Corridor/processed_iq_fusion): Contains synchronized CSV files where data from all four anchors have been merged into a single stream using [`iq_fusion.py`](scripts/iq_fusion.py).
    - [`raw_data`](1_Laboratory_and_Corridor/Corridor/raw_data): Organized by subset (train, test1, test2) and topology. It contains the original CSV files for each individual anchor (4 files per point).
  - [`Laboratory`](1_Laboratory_and_Corridor/Laboratory)
    - [`coordinates`](1_Laboratory_and_Corridor/Laboratory/coordinates): Contains CSV files with Cartesian (x,y,z) coordinates for anchors (Face-to-Face and 45º Inward topologies) and Ground Truth points.
    - [`final_dataset`](1_Laboratory_and_Corridor/Laboratory/final_dataset): The final, cleaned CSV files ready for positioning analysis.
    - [`nlos_labels`](1_Laboratory_and_Corridor/Laboratory/nlos_labels): Per-anchor binary LoS/NLoS annotations (`0` = LoS, `1` = NLoS) per reference point.
    - [`processed_iq_fusion`](1_Laboratory_and_Corridor/Laboratory/processed_iq_fusion): Contains synchronized CSV files where data from all four anchors have been merged into a single stream using [`iq_fusion.py`](scripts/iq_fusion.py).
    - [`raw_data`](1_Laboratory_and_Corridor/Laboratory/raw_data): Organized by subset (train, test1, test2) and topology. It contains the original CSV files for each individual anchor (4 files per point).
  - [`map`](1_Laboratory_and_Corridor/map): Map of the experimental setup for Scenario 1.
    - [`1_lab_corridor.png`](1_Laboratory_and_Corridor/map/1_lab_corridor.png)
- [`2_Meeting_Room`](2_Meeting_Room): Data and coordinates for Meeting Room (153.024 $m^2$) and its exterior corridor (34.368 $m^2$).
  - [`coordinates`](2_Meeting_Room/coordinates): Contains CSV files with Cartesian (x,y,z) coordinates for anchors (Face-to-Face and 45º Inward topologies) and Ground Truth points.
  - [`final_dataset`](2_Meeting_Room/final_dataset): The final, cleaned CSV files ready for positioning analysis.
  - [`nlos_labels`](2_Meeting_Room/nlos_labels): Per-anchor binary LoS/NLoS annotations (`0` = LoS, `1` = NLoS) per reference point.
  - [`map`](2_Meeting_Room/map): Map of the experimental setup for Scenario 2.
    - [`2_meeting_room.png`](2_Meeting_Room/map/2_meeting_room.png)
  - [`processed_iq_fusion`](2_Meeting_Room/processed_iq_fusion): Contains synchronized CSV files where data from all four anchors have been merged into a single stream using [`iq_fusion.py`](scripts/iq_fusion.py).
  - [`raw_data`](2_Meeting_Room/raw_data): Organized by subset (train, test1, test2) and topology. It contains the original CSV files for each individual anchor (4 files per point).
- [`3_Auditorium`](3_Auditorium): Data and coordinates for the 3D Auditorium scenario (152.170 $m^2$).
  - [`coordinates`](3_Auditorium/coordinates): Contains CSV files with Cartesian (x,y,z) coordinates for anchors (45º Inward topology) and Ground Truth points.
  - [`final_dataset`](3_Auditorium/final_dataset): The final, cleaned CSV files ready for positioning analysis.
  - [`nlos_labels`](3_Auditorium/nlos_labels): Per-anchor binary LoS/NLoS annotations (`0` = LoS, `1` = NLoS) per reference point.
  - [`map`](3_Auditorium/map): Map of the experimental setup for Scenario 3.
    - [`3_auditorium.png`](3_Auditorium/map/3_auditorium.png)
  - [`processed_iq_fusion`](3_Auditorium/processed_iq_fusion): Contains synchronized CSV files where data from all four anchors have been merged into a single stream using [`iq_fusion.py`](scripts/iq_fusion.py).
  - [`raw_data`](3_Auditorium/raw_data): Organized by subset (train, test1, test2). It contains the original CSV files for each individual anchor (4 files per point).
- [`scripts`](scripts): Processing, visualization, statistical analysis, and baseline scripts:
  - [`dataset_cleaning.py`](scripts/dataset_cleaning.py): Data cleaning, Ground Truth assignment, and per-anchor LoS/NLoS label integration.
  - [`generate_maps.py`](scripts/generate_maps.py): Map visualization.
  - [`generate_dataset_paper_figures.py`](scripts/generate_dataset_paper_figures.py): Generates signal characterization and data quality figures.
  - [`generate_single_sample_figure.py`](scripts/generate_single_sample_figure.py): Generates single-sample positioning example figure.
  - [`iq_fusion.py`](scripts/iq_fusion.py): Synchronizes raw anchor data.
  - [`mann_whitney_test_rssi.py`](scripts/mann_whitney_test_rssi.py): Mann-Whitney statistical tests on RSSI.
  - [`mann_whitney_test_azimuth.py`](scripts/mann_whitney_test_azimuth.py): Mann-Whitney statistical tests on azimuth.
  - [`knn_baseline.py`](scripts/knn_baseline.py): k-NN fingerprinting baseline grid search (`angles_only` vs. `hybrid`).
  - [`utils.py`](scripts/utils.py): Common helper functions for directory management and coordinate handling.
- [`requirements.txt`](requirements.txt): List of Python dependencies required to run the processing pipeline.



> [!NOTE]
> The folders _raw_data_, _processed_iq_fusion_, _final_dataset_ and _nlos_labels_ are currently empty in this repository due to GitHub's file size limits. The full dataset is hosted on [Zenodo](https://doi.org/10.5281/zenodo.19823027).

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
Merges the independent data streams from the four u-blox anchors using a strict 20 ms (`0.02 s`) temporal matching window.
```
python scripts/iq_fusion.py
```
- Output: _processed_iq_fusion/_.
  
### 3. Dataset Cleaning and Labeling
Cleans synchronized packets, removes incomplete sessions, assigns Ground Truth coordinates, and attaches per-anchor LoS/NLoS labels.
```
python scripts/dataset_cleaning.py
```
- Output: _final_dataset/_.

### 4. Visualization & Baseline Evaluation
Generate scenario maps, signal/quality figures, and run the k-NN fingerprinting baseline: 
```
python scripts/generate_maps.py
python scripts/generate_dataset_paper_figures.py --dataset_root . --output_dir ./figures
python scripts/knn_baseline.py
```

## :bar_chart: Dataset Summary
The dataset distribution is as follows:
| Scenario  | Training Points | Evaluation Points | Total Area |
| ------------- | ------------- | ------------- | ------------- |
| 1.a Laboratory  | 28  | 18  | $59.286\text{ m}^2$ | 
| 1.b Corridor  | 26  |  21  | $135.235\text{ m}^2$  |
| 2. Meeting Room  | 60  | 30  | $187.392\text{ m}^2$  | 
| 3. Auditorium  | 25  |  20  | $152.170\text{ m}^2$  |

## :memo: Citation
If you use this code or results, please cite:

Source Dataset:
> Martín Frechina, S., Dura, E., & Torres-Sospedra, J. (2026). UVIndoorLoc-BLE-AoA&IQ Dataset [Data set]. Zenodo. https://doi.org/10.5281/zenodo.19823027

## :page_facing_up: License
This project is licensed under the [Apache License 2.0](LICENSE).
