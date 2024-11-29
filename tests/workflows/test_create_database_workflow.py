import preprocessing.api as api
import filecmp

from pathlib import Path
import preprocessing.api as api
import geopandas as gpd
import pytest
import shutil
import sqlite3

from tests import test_data, test_results
from preprocessing.common_functions import read_config_file

@pytest.mark.parametrize("project_folder",
                         [pytest.param("31-1_v2", id = '31-1')])
def test_create_database_workflow(project_folder:str,  request: pytest.FixtureRequest):
    #specify the output path for results:
    _output_path = test_results.joinpath(request.node.name)
    if _output_path.exists():
        shutil.rmtree(_output_path)

    # #run the hydraring overflow workflow to generate the relevant results
    api.create_database(test_data.joinpath(project_folder, "preprocessor.config"), _output_path)

    #compare sqlite database in both dirs
    for file in _output_path.rglob("database_31-1.sqlite"):
        #Shallow comparison is not enough, because the database contains binary data
        _reference_file = test_data.joinpath(project_folder, file.relative_to(_output_path))
        #compare the tables in the database using sqlite3
        conn = sqlite3.connect(file)
        conn_ref = sqlite3.connect(_reference_file)
        cursor = conn.cursor()
        cursor_ref = conn_ref.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        cursor_ref.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables_ref = cursor_ref.fetchall()
        assert tables == tables_ref
        #compare the content of the tables
        for table in tables:
            cursor.execute(f"SELECT * FROM {table[0]}")
            rows = cursor.fetchall()
            cursor_ref.execute(f"SELECT * FROM {table[0]}")
            rows_ref = cursor_ref.fetchall()
            assert rows == rows_ref
        conn.close()
        conn_ref.close()
    
    #compare config file in both dirs
    for file in _output_path.rglob("config.json"):
        _reference_file = test_data.joinpath(project_folder, file.relative_to(_output_path))
        assert filecmp.cmp(file, _reference_file, shallow=False) == True


        

