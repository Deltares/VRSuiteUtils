import os
from pathlib import Path
import pandas as pd
from preprocessing.step2_mechanism_data.hydranl_read import HydraNLReadWaterLevel

def waterlevel_hydranl_main(file_path: Path,
                            work_dir_path: Path,
                            output_path: Path,
                            correct_uncer: bool):
    
    hr_data = pd.read_csv(file_path, sep=';', header=0)
    hr_koppel = hr_data['hr_koppel'].values
    doorsnede = hr_data['doorsnede'].values
    years = ['2023', '2100']
    
    for year in years:
        for ii,dsn in enumerate(doorsnede):

            hnl_work_dir_path = os.path.join(work_dir_path, year)
            output_dir = os.path.join(output_path, year, dsn)

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            json_file_name = os.path.join(output_dir, f'designtable_{dsn}.json')
        
            HydraNLReadWaterLevel(hnl_work_dir_path, hr_koppel[ii], correct_uncer).export_json(json_file_name)