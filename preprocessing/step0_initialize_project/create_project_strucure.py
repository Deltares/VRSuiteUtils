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

The necessary paths are written to the input.txt file in the input_files directory.

'''

import os

def create_project_structure(project_folder, traject_id):
    # Define directory paths
    project_dir = project_folder
    input_files_dir = os.path.join(project_dir, "input_files")
    intermediate_results_dir = os.path.join(project_dir, "intermediate_results")
    vrtool_database_dir = os.path.join(project_dir, "vrtool_database")
    hr_databases_dir = os.path.join(input_files_dir, "HR_databases")
    hr_profielen_dir = os.path.join(input_files_dir, "HR_profielen")
    default_files_dir = os.path.join(input_files_dir, "default_files")
    hr_database_huidig_dir = os.path.join(hr_databases_dir, "HR_database_huidig")
    hr_database_toekomst_dir = os.path.join(hr_databases_dir, "HR_database_toekomst")
    profielen_dir = os.path.join(intermediate_results_dir, "profielen")
    ahn_profielen_dir = os.path.join(profielen_dir, "ahn_profielen")
    kar_profielen_dir = os.path.join(profielen_dir, "kar_profielen")
    repr_profielen_dir = os.path.join(profielen_dir, "repr_profielen")
    hr_results_dir = os.path.join(intermediate_results_dir, "HR_results")

    # Create directories
    os.makedirs(project_dir)
    os.makedirs(input_files_dir)
    os.makedirs(intermediate_results_dir)
    os.makedirs(vrtool_database_dir)
    os.makedirs(hr_databases_dir)
    os.makedirs(hr_profielen_dir)
    os.makedirs(default_files_dir)
    os.makedirs(hr_database_huidig_dir)
    os.makedirs(hr_database_toekomst_dir)
    os.makedirs(profielen_dir)
    os.makedirs(ahn_profielen_dir)
    os.makedirs(kar_profielen_dir)
    os.makedirs(repr_profielen_dir)
    os.makedirs(hr_results_dir)
    os.makedirs(os.path.join(hr_results_dir, "waterlevel"))
    os.makedirs(os.path.join(hr_results_dir, "overflow"))

    # Remaining directories
    for directory in ["database_bekleding", "steentoets", "bag_gebouwen", "vakindeling", "bekleding", "teenlijn", "bebouwing"]:
        os.makedirs(os.path.join(input_files_dir, directory))
        os.makedirs(os.path.join(intermediate_results_dir, directory))

    # Write paths to input.txt file
    with open(os.path.join(input_files_dir, "input.txt"), "w") as f:
        f.write(f"[DEFAULT]\n\n")
        f.write(f"traject_id = {traject_id} # Trajectnaam\n\n")
        f.write(f"project_dir = {project_dir} # Project directory\n")
        f.write(f"input_files_dir = {input_files_dir} # Input files directory\n")
        f.write(f"intermediate_results_dir = {intermediate_results_dir} # Intermediate results directory\n")
        f.write(f"vrtool_database_dir = {vrtool_database_dir} # VRTool database directory\n")
        f.write(f"hr_databases_dir = {hr_databases_dir} # HR databases directory\n")
        f.write(f"hr_profielen_dir = {hr_profielen_dir} # HR profielen directory\n")
        f.write(f"default_files_dir = {default_files_dir} # Default files directory\n")
        f.write(f"hr_database_huidig_dir = {hr_database_huidig_dir} # HR database huidig directory\n")
        f.write(f"hr_database_toekomst_dir = {hr_database_toekomst_dir} # HR database toekomst directory\n")
        f.write(f"profielen_dir = {profielen_dir} # Profielen directory\n")
        f.write(f"ahn_profielen_dir = {ahn_profielen_dir} # AHN profielen directory\n")
        f.write(f"kar_profielen_dir = {kar_profielen_dir} # KAR profielen directory\n")
        f.write(f"repr_profielen_dir = {repr_profielen_dir} # REPR profielen directory\n")
        f.write(f"hr_results_dir = {hr_results_dir} # HR results directory\n")

    # TO DO:
    # - Add the remaining paths to CSV and GEOJSON files (input and files that are created in workflows) the input.txt file
    # Add default parameter values, e.g.: dx, flip_traject, flip_waterkant, etc.


    print(f"Project structure created for '{os.path.basename(project_folder)}'.")

if __name__ == "__main__":
    project_folder = "c:/vrm_test/test_folder_structure22"
    traject_id = "7-2"
    create_project_structure(project_folder, traject_id)
