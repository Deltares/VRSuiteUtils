from preprocessing.workflows.hydraring_overflow_workflow import overflow_main
from pathlib import Path


def test_default_case():
    # working directory:
    work_dir = Path(r"c:\VRM\test_hydraring_workflow_wdod\overslag")

    # path to Hydra-Ring:
    HydraRing_path = Path(
        r"c:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236"
    )
    # list of paths to databases to be considered
    database_paths = [
        Path(r"c:\VRM\test_hydraring_workflow_wdod\HR\2023"),
        Path(r"c:\VRM\test_hydraring_workflow_wdod\HR\2100"),
    ]
    file_name = r"c:\VRM\test_hydraring_workflow_wdod\HR_default.csv"
    overflow_main(work_dir, database_paths, HydraRing_path, file_name)
