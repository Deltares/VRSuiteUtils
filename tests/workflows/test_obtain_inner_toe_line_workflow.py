import preprocessing.api as api
import filecmp

from pathlib import Path
import preprocessing.api as api
import geopandas as gpd
import pytest
import shutil


from tests import test_data, test_results
from preprocessing.common_functions import read_config_file

@pytest.mark.parametrize("project_folder",
                         [pytest.param("31-1_v2", id = '31-1')])
def test_obtain_inner_toe_line_workflow(project_folder:str,  request: pytest.FixtureRequest):
    #specify the output path for results:
    _output_path = test_results.joinpath(request.node.name)
    if _output_path.exists():
        shutil.rmtree(_output_path)

    # #run the workflow to generate the relevant results
    api.obtain_inner_toe_line(test_data.joinpath(project_folder, "preprocessor.config"), _output_path)

    #compare selected_profiles.csv in both dirs
    for file in _output_path.rglob("teenlijn.geojson"):
        _reference_file = test_data.joinpath(project_folder, file.relative_to(_output_path))
        assert filecmp.cmp(file, _reference_file, shallow=False) == True


        

