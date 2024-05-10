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


    # 3 main directories: input, intermediate_results, vrtool_database
    input_files_dir = os.path.join(project_dir, "input_files")
    intermediate_results_dir = os.path.join(project_dir, "intermediate_results")
    vrtool_database_dir = os.path.join(project_dir, "vrtool_database")

    # Subdirectories of input_files
    database_path_HR_current = os.path.join(input_files_dir, "HR_databases", "2023")
    database_path_HR_future = os.path.join(input_files_dir, "HR_databases", "2100")
    hr_profielen_dir = os.path.join(input_files_dir, "prfl")
    default_files_dir = os.path.join(input_files_dir, "default_files")
    steentoets_dir = os.path.join(input_files_dir, "steentoets")

    vakindeling_dir = os.path.join(intermediate_results_dir, "vakindeling")
    hr_results_dir = os.path.join(intermediate_results_dir, "HR_results")
    waterlevel_dir = os.path.join(hr_results_dir, "waterlevel")
    overflow_dir = os.path.join(hr_results_dir, "overflow")
    bekleding_dir = os.path.join(intermediate_results_dir, "bekleding")
    profielen_dir = os.path.join(intermediate_results_dir, "profielen")
    ahn_profielen_dir = os.path.join(profielen_dir, "ahn_profielen")
    kar_profielen_dir = os.path.join(profielen_dir, "kar_profielen")
    repr_profielen_dir = os.path.join(profielen_dir, "repr_profielen")
    teenlijn_dir = os.path.join(intermediate_results_dir, "teenlijn")
    bebouwing_dir = os.path.join(intermediate_results_dir, "bebouwing")

    # remove first part (with project_dir) from bebouwing_dir:
    # print(os.path.relpath(bebouwing_dir, project_dir))

    # Create directories
    os.makedirs(project_dir)
    os.makedirs(input_files_dir)
    os.makedirs(intermediate_results_dir)
    os.makedirs(vrtool_database_dir)
    os.makedirs(database_path_HR_current)
    os.makedirs(database_path_HR_future)
    os.makedirs(hr_profielen_dir)
    os.makedirs(default_files_dir)
    os.makedirs(steentoets_dir)
    os.makedirs(vakindeling_dir)
    os.makedirs(hr_results_dir)
    os.makedirs(waterlevel_dir)
    os.makedirs(overflow_dir)
    os.makedirs(bekleding_dir)
    os.makedirs(profielen_dir)
    os.makedirs(ahn_profielen_dir)
    os.makedirs(kar_profielen_dir)
    os.makedirs(repr_profielen_dir)
    os.makedirs(teenlijn_dir)
    os.makedirs(bebouwing_dir)


    # Write paths to input.txt file
    with open(os.path.join(project_dir, "preprocessor.config"), "w") as f:
        f.write(f"[DEFAULT]\n\n")
        f.write(f"traject_id                = {traject_id} # Trajectnaam\n\n")

        f.write(f"project_dir               = {project_dir} # Project directory\n\n")
        f.write(f"input_files_dir           = {os.path.relpath(input_files_dir, project_dir)}           # Input files directory\n")
        f.write(f"intermediate_results_dir  = {os.path.relpath(intermediate_results_dir, project_dir)}  # Intermediate results directory\n")
        f.write(f"output_map_database       = {os.path.relpath(vrtool_database_dir, project_dir)}       # VRTool database directory\n\n")

        f.write(f"database_path_HR_current  = {os.path.relpath(database_path_HR_current, project_dir)}     # pad met de database voor de HR sommen (huidig)\n")
        f.write(f"database_path_HR_future   = {os.path.relpath(database_path_HR_future, project_dir)}     # pad met de database voor de HR sommen (toekomst)\n")
        f.write(f"hr_profielen_dir          = {os.path.relpath(hr_profielen_dir, project_dir)}                  # HR profielen directory\n")
        f.write(f"default_files_dir         = {os.path.relpath(default_files_dir, project_dir)}         # Default files directory\n")
        f.write(f"steentoets_map            = {os.path.relpath(steentoets_dir, project_dir)}            # Steentoets directory\n\n")

        f.write(f"output_map_vakindeling    = {os.path.relpath(vakindeling_dir, project_dir)}                             # aan te maken uitvoermap voor de vakindeling\n")
        f.write(f"hr_results_dir            = {os.path.relpath(hr_results_dir, project_dir)}                              # HR results directory\n")
        f.write(f"output_map_waterstand     = {os.path.relpath(waterlevel_dir, project_dir)}                   # Waterlevel directory\n")
        f.write(f"output_map_overslag       = {os.path.relpath(overflow_dir, project_dir)}                     # Overflow directory\n")
        f.write(f"output_map_bekleding      = {os.path.relpath(bekleding_dir, project_dir)}                               # Bekleding directory\n")
        f.write(f"output_map_profielen      = {os.path.relpath(profielen_dir, project_dir)}                               # Profielen directory\n")
        f.write(f"output_map_ahn_profielen  = {os.path.relpath(ahn_profielen_dir, project_dir)}                 # AHN profielen directory\n")
        f.write(f"karakteristieke_profielen_map = {os.path.relpath(kar_profielen_dir, project_dir)}             # KAR profielen directory\n")
        f.write(f"output_map_representatieve_profielen = {os.path.relpath(repr_profielen_dir, project_dir)}     # REPR profielen directory\n")
        f.write(f"output_map_teenlijn       = {os.path.relpath(teenlijn_dir, project_dir)}                                # Teenlijn directory\n")
        f.write(f"output_map_bebouwing      = {os.path.relpath(bebouwing_dir, project_dir)}                               # Bebouwing directory\n\n")

        f.write(f"vakindeling_csv           = {os.path.relpath(os.path.join(default_files_dir, 'Vakindeling.csv'), project_dir)}                    # pad naar de geojson (die gegenereerd is in stap vakindeling).\n")
        f.write(f"hr_input_csv              = {os.path.relpath(os.path.join(default_files_dir, 'HR_default.csv'), project_dir)}                     # pad naar de csv met de HR info.\n")
        f.write(f"bekleding_input_csv       = {os.path.relpath(os.path.join(default_files_dir, 'Bekleding_default.csv'), project_dir)}              # pad naar de csv met de bekleding info.\n")
        f.write(f"piping_input_csv          = {os.path.relpath(os.path.join(default_files_dir, 'Piping_default.csv'), project_dir)}                 # pad naar de csv met de piping info.\n")
        f.write(f"stabiliteit_input_csv     = {os.path.relpath(os.path.join(default_files_dir, 'Stabiliteit_default.csv'), project_dir)}            # pad naar de csv met de stabiliteit info.\n\n")

        f.write(f"bag_gebouwen_geopackage   = {os.path.relpath(os.path.join(bag_gebouwen_dir, 'bag-light.gpkg'), project_dir)}                   # pad naar de geopackage met de BAG gebouwen.\n\n")

        f.write(f"vakindeling_geojson       = {os.path.relpath(os.path.join(vakindeling_dir, f'vakindeling_{traject_id}.geojson'), project_dir)}     # pad naar de geojson met de vakindeling. Wordt gegenereerd in stap vakindeling en staat in output_map_vakindeling.\n")
        f.write(f"teenlijn_geojson          = {os.path.relpath(os.path.join(teenlijn_dir, f'teenlijn.geojson'), project_dir)}           # pad naar de geojson met de teenlijn. Wordt gegenereerd in stap teenlijn en staat in output_map_teenlijn.\n")

        f.write(f"profiel_info_csv          = {os.path.relpath(os.path.join(profielen_dir, 'traject_profiles.csv'), project_dir)}         # pad naar de csv met de informatie over de verzamelde profielen (uit een eerdere stap: genereer_dijkprofielen). Deze csv zou traject_profiles.csv moeten heten, tenzij de gebruiker de naam heeft aangepast.\n")
        f.write(f"karakteristieke_profielen_csv = {os.path.relpath(os.path.join(repr_profielen_dir, 'selected_profiles.csv'), project_dir)} # pad naar csv met karakteristieke profielen. Wordt afgeleid in stap selecteer_profiel en staat in output_map_representatieve_profielen. Normaliter met de naam selected_profiles.csv, tenzij aangepast door gebruiker.\n")
        f.write(f"gebouwen_csv              = {os.path.relpath(os.path.join(bebouwing_dir, f'building_count_traject{traject_id}.csv'), project_dir)}              # pad naar csv met getelde gebouwen. Wordt afgeleid in stap tel_gebouwen en staat in output_map_bebouwing met naam building_count_traject_traject_ID.csv, tenzij aangepast door gebruiker.\n\n")

        f.write(f"vrtool_database_naam      = database_{traject_id}.sqlite      # hier geef je de naam van de database die wordt aangemaakt als input voor de vrtool.\n\n")

        f.write(f"dx                        = 25       # stapgrootte bij het afleiden van dijkprofielen uit het AHN. Default is 25.\n")
        f.write(f"traject_shapefile         = False    # als deze op false staat, wordt de trajectshapefile uit het NBPW. Als het bestand afwijkt, moet hier een pad naar de juiste shapefile worden meegegeven.\n")
        f.write(f"flip_traject              = False    # gooit de vakindeling om, indien het de shapefile in de andere richting is gedefinieerd als de vakindeling. Werkt ook voor het genereren van AHN profielen.\n")
        f.write(f"flip_waterkant            = False    # belangrijk bij het genereren van AHN profielen. Er wordt een profiel getrokken met voor- en achterland. By default (False) wordt aangenomen dat het water rechts van de kering ligt, in de richting van oplopende vakindeling. Anders moet deze parameter op True worden gezet. Let op, als flip_traject op True staat, ligt het water rechts t.o.v. het geflipte traject!\n")

    print(f"\nProjectstructuur aangemaakt voor '{os.path.basename(project_folder)}'.")

if __name__ == "__main__":
    project_folder = r"c:\Repositories\VRSuite\Preprocessing\VrToolPreprocess\tests\test_data\31-1_v2"
    traject_id = "31-1"
    create_project_structure(project_folder, traject_id)
