'''
This script initializes the project structure. It creates a folder with "project_name", which is given by the user. The
folder with project_name, contains the following directories:
- input_files
- intermediate_results
- vrtool_database

The input_files directory contains the following directories:
- default_files
- HR_databases (with subdirectory "HR_databases/HR_database_huidig" and "HR_databases/HR_database_toekomst")
- HR_profielen
- database_bekleding
- steentoets
- bag_gebouwen

The intermediate_results directory contains the following directories:
- vakindeling
- HR_results (with subdirectory "HR_results/waterlevel" and "HR_results/overflow")
- bekleding
- profielen (with subdirectory "profielen/ahn_profielen" and "profielen/kar_profielen" and "profielen/repr_profielen")
- teenlijn
- bebouwing

The vrtool_database directory doesn't contain any subdirectories.
'''

import os
import shutil
import sys

def create_project_structure(project_name):
    """
    Function that creates the project structure for the VR-tool. The project structure is as follows:
    - project_name
        - input_files
            - default_files
            - HR_databases
                - HR_database_huidig
                - HR_database_toekomst
            - HR_profielen
            - database_bekleding
            - steentoets
            - bag_gebouwen
        - intermediate_results
            - vakindeling
            - HR_results
                - waterlevel
                - overflow
            - bekleding
            - profielen
                - ahn_profielen
                - kar_profielen
                - repr_profielen
            - teenlijn
            - bebouwing
        - vrtool_database
    """
    # Create the project folder
    project_folder = os.path.join(os.getcwd(), project_name)
    os.makedirs(project_folder, exist_ok=True)

    # Create the input_files folder
    input_files_folder = os.path.join(project_folder, "input_files")
    os.makedirs(input_files_folder, exist_ok=True)

    # Create the default_files folder
    default_files_folder = os.path.join(input_files_folder, "default_files")
    os.makedirs(default_files_folder, exist_ok=True)

    # Create the HR_databases folder
    HR_databases_folder = os.path.join(input_files_folder, "HR_databases")
    os.makedirs(HR_databases_folder, exist_ok=True)

    # Create the HR_database_huidig folder
    HR_database_huidig_folder = os.path.join(HR_databases_folder, "HR_database_huidig")
    os.makedirs(HR_database_huidig_folder, exist_ok=True)

    # Create the HR_database_toekomst folder
    HR_database_toekomst_folder = os.path.join(HR_databases_folder, "HR_database_toekomst")
    os.makedirs(HR_database_toekomst_folder, exist_ok=True)

    # Create the HR_profielen folder
    HR_profielen_folder = os.path.join(input_files_folder, "HR_profielen")
    os.makedirs(HR_profielen_folder, exist_ok=True)

    # Create the database_bekleding folder
    database_bekleding_folder = os.path.join(input_files_folder, "database_bekleding")
    os.makedirs(database_bekleding_folder, exist_ok=True)

    # Create the steentoets folder
    steentoets_folder = os.path.join(input_files_folder, "steentoets")
    os.makedirs(steentoets_folder, exist_ok=True)

    # Create the bag_gebouwen folder
    bag_gebouwen_folder = os.path.join(input_files_folder, "bag_gebouwen")
    os.makedirs(bag_gebouwen_folder, exist_ok=True)

    # Create the intermediate_results folder
    intermediate_results_folder = os.path.join(project_folder, "intermediate_results")
    os.makedirs(intermediate_results_folder, exist_ok=True)

    # Create the vakindeling folder
    vakindeling_folder = os.path.join(intermediate_results_folder, "vakindeling")
    os.makedirs(vakindeling_folder, exist_ok=True)

    # Create the HR_results folder
    HR_results_folder = os.path.join(intermediate_results_folder, "HR_results")
    os.makedirs(HR_results_folder, exist_ok=True)

    # Create the waterlevel folder
    waterlevel_folder = os.path.join(HR_results_folder, "waterlevel")
    os.makedirs(waterlevel_folder, exist_ok=True)

    # Create the overflow folder
    overflow_folder = os.path.join(HR_results_folder, "overflow")
    os.makedirs(overflow_folder, exist_ok=True)

    # Create the bekleding folder
    bekleding_folder = os.path.join(intermediate_results_folder, "bekleding")
    os.makedirs(bekleding_folder, exist_ok=True)

    # Create the profielen folder
    profielen_folder = os.path.join(intermediate_results_folder, "profielen")
    os.makedirs(profielen_folder, exist_ok=True)

    # Create the ahn_profielen folder
    ahn_profielen_folder = os.path.join(profielen_folder, "ahn_profielen")
    os.makedirs(ahn_profielen_folder, exist_ok=True)

    # Create the kar_profielen folder
    kar_profielen_folder = os.path.join(profielen_folder, "kar_profielen")
    os.makedirs(kar_profielen_folder, exist_ok=True)

    # Create the repr_profielen folder
    repr_profielen_folder = os.path.join(profielen_folder, "repr_profielen")
    os.makedirs(repr_profielen_folder, exist_ok=True)

    # Create the teenlijn folder
    teenlijn_folder = os.path.join(intermediate_results_folder, "teenlijn")
    os.makedirs(teenlijn_folder, exist_ok=True)

    # Create the bebouwing folder
    bebouwing_folder = os.path.join(intermediate_results_folder, "bebouwing")
    os.makedirs(bebouwing_folder, exist_ok=True)

    # Create the vrtool_database folder
    vrtool_database_folder = os.path.join(project_folder, "vrtool_database")
    os.makedirs(vrtool_database_folder, exist_ok=True)

    print(f"Project structure for project {project_name} has been created.")

if __name__ == "__main__":
    create_project_structure(r"c:\vrm_test\test_folder_structure")

