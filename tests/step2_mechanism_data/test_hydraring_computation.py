import shutil
from pathlib import Path

import pytest
from vrtool.orm.models import *
from vrtool.orm.orm_controllers import *
from tests import test_data, test_results
from preprocessing.step4_build_sqlite_db.read_intermediate_outputs import *
from preprocessing.step4_build_sqlite_db.write_database import *
import pandas as pd

from preprocessing.step2_mechanism_data.hydraring_computation import HydraRingComputation

class TestHydraRingComputation:

    @pytest.mark.parametrize("values, betas", [
        pytest.param([1, 2, 3, 5, 4], [0.1, 0.2, 0.3, 0.4, 0.5], id="unordered values"),
    ])
    def test_hydraring_input_with_unordered_values_fails(self, values, betas):
        #check if it raises an error:
        with pytest.raises(ValueError):
            HydraRingComputation.check_and_justify_HydraRing_data(values, betas, "test", "test")

    @pytest.mark.parametrize("values, betas", [
        pytest.param([1, 2, 3, 4, 5], [0.1, 0.2, 0.3, 0.4, 0.5], id="ordered values"),
    ])
    def test_hydraring_input_with_ordered_values_succeeds(self, values, betas):
        #check if it raises an error:
        HydraRingComputation.check_and_justify_HydraRing_data(values, betas, "test", "test")

    @pytest.mark.parametrize("values, betas", [
        pytest.param([1, 2, 3, 4, 5], [0.1, 0.2, 0.3, 0.2, 0.5], id="non-increasing values"),
    ])
    def test_hydraring_input_with_non_increasing_values_succeeds(self, values, betas):
        #check if it raises an error:
        values, betas = HydraRingComputation.check_and_justify_HydraRing_data(values, betas, "test", "test")
        expected_betas = [0.1, 0.2, 0.3, 0.3, 0.5]
        assert betas == expected_betas