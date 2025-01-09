import preprocessing.api as api
import filecmp
import pytest
import shutil
from tests import test_data, test_results

@pytest.mark.parametrize("project_folder, decim_type",
                         [pytest.param("14-1", "decim_simple", id = '14-1_decim_simple'),
                          pytest.param("14-1", "decim_10", id = '14-1_decim_10')])
def test_hydranl_overflow_workflow(project_folder:str,  decim_type: str, request: pytest.FixtureRequest):
    #specify the output path for results:
    _output_path = test_results.joinpath(request.node.name)
    if _output_path.exists():
        shutil.rmtree(_output_path)

    #run the hydranl overflow workflow to generate the relevant results
    api.evaluate_hydranl_overflow_computations(test_data.joinpath(project_folder, "preprocessor.config"), _output_path, True, decim_type, 1)

    #compare the results with the reference results for all *.json files in the subdirectories of the subdirectories in _output_dir
    for file in _output_path.rglob("*.json"):
        _reference_file = test_data.joinpath(project_folder, decim_type, file.relative_to(_output_path))
        assert filecmp.cmp(file, _reference_file, shallow=False) == True