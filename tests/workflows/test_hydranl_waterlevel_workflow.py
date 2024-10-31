import preprocessing.api as api
import filecmp
import pytest
import shutil
from tests import test_data, test_results

@pytest.mark.parametrize("project_folder",
                         [pytest.param("14-1", id = '14-1')])
def test_hydranl_waterlevel_workflow(project_folder:str,  request: pytest.FixtureRequest):
    #specify the output path for results:
    _output_path = test_results.joinpath(request.node.name)
    if _output_path.exists():
        shutil.rmtree(_output_path)

    #run the hydranl waterlevel workflow to generate the relevant results
    api.evaluate_hydranl_waterlevel_computations(test_data.joinpath(project_folder, "preprocessor.config"), _output_path, True)

    #compare the results with the reference results for all *.json files in the subdirectories of the subdirectories in _output_dir
    for file in _output_path.rglob("*.json"):
        _reference_file = test_data.joinpath(project_folder, file.relative_to(_output_path))
        assert filecmp.cmp(file, _reference_file, shallow=False) == True
        

