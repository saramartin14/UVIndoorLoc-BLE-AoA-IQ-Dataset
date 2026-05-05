# BLE-AoA-ETSEUV-Dataset
This repository contains the **ETSE-UV BLE AoA dataset**, a collection of In-phase and Quadrature (I/Q) signal samples and Angle-of-Arrival (AoA) measurements based on the Bluetooth Low Energy (BLE) 5.1 specification. The project focuses on providing a BLE 5.1 AoA dataset by collecting data in three distinct real-world scenarios at the Escola Tècnica Superior d'Enginyeria (ETSE) of the University of Valencia (UV).

## :file_folder: Repository Structure
The project is organized into the following directories: 
- [`1_Laboratory_and_Corridor`](1_Laboratory_and_Corridor): Data and coordinates for Laboratory (59.286 $m^2$) and Corridor (135.235 $m^2$).
  - [`Corridor`](Corridor)
    - [`coordinates`]
    - [`final_dataset`]
    - [`processed_iq_fusion`]
    - [`raw_data`]
  - [`Laboratory`](Laboratory)
    - [`coordinates`]
    - [`final_dataset`]
    - [`processed_iq_fusion`]
    - [`raw_data`]
  - [`map`](map)
    - [`1_lab_corridor.png`]
- [`2_Meeting_Room`](2_Meeting_Room): Data and coordinates for the Meeting Room (153.024 $m^2$) and its exterior corridor (34.368 $m^2$).
  - [`coordinates`]
  - [`final_dataset`]
  - [`map`]
    - [`2_meeting_room.png`]
  - [`processed_iq_fusion`]
  - [`raw_data`]
- [`3_Auditorium`](3_Auditorium): Data and coordinates for the 3D Auditorium scenario (152.170 $m^2$).
  - [`coordinates`]
  - [`final_dataset`]
  - [`map`]
    - [`3_auditorium.png`]
  - [`processed_iq_fusion`]
  - [`raw_data`]
- [`scripts`](scripts): The core execution pipeline consisting of four scripts:
  - [`dataset_cleaning.py`](scripts/dataset_cleaning.py): Data cleaning and Ground Truth labeling
  - [`generate_maps.py`](scripts/generate_maps.py): Map visualization
  - [`iq_fusion.py`](scripts/iq_fusion.py): Synchronizes raw anchor data
  - [`utils.py`](scripts/utils.py): Common helper functions for directory management and coordinate handling.
- [`requirements.txt`](requirements.txt): List of Python dependencies required to run the processing pipeline.
