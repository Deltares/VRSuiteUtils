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

    # @pytest.mark.parametrize("values, betas", [
    #     pytest.param([1, 2, 3, 5, 4], [0.1, 0.2, 0.3, 0.4, 0.5], id="unordered values"),
    # ])
    # def test_hydraring_input_with_unordered_values_fails(self, values, betas):
    #     #check if it raises an error:
    #     with pytest.raises(ValueError):
    #         HydraRingComputation.check_and_justify_HydraRing_data(values, betas, "test", "test")

    # @pytest.mark.parametrize("values, betas", [
    #     pytest.param([1, 2, 3, 4, 5], [0.1, 0.2, 0.3, 0.4, 0.5], id="ordered values"),
    # ])
    # def test_hydraring_input_with_ordered_values_succeeds(self, values, betas):
    #     #check if it succeeds:
    #     HydraRingComputation.check_and_justify_HydraRing_data(values, betas, "test", "test")

    # @pytest.mark.parametrize("values, betas", [
    #     pytest.param([1, 2, 3, 4, 5], [0.1, 0.2, 0.3, 0.2, 0.5], id="non-increasing values"),
    # ])
    # def test_hydraring_input_with_non_increasing_values_succeeds(self, values, betas):
    #     #check if it gives the right output:
    #     values, betas = HydraRingComputation.check_and_justify_HydraRing_data(values, betas, "test", "test")
    #     expected_betas = [0.1, 0.2, 0.3, 0.3, 0.5]
    #     assert betas == expected_betas


    def test_hydraring_design_table_with_non_increasing_betas(self):
        # Set paths to the design tables
        before_correction_path = test_data.joinpath("13-6", "intermediate_results", "HR_results", "waterlevel", "beta_not_increasing", "BeforeCorrection_DESIGNTABLE_13-6_0003.txt")
        design_table_path = test_data.joinpath("13-6", "intermediate_results", "HR_results", "waterlevel", "beta_not_increasing", "DESIGNTABLE_13-6_0003.txt")
        after_correction_path = test_data.joinpath("13-6", "intermediate_results", "HR_results", "waterlevel", "beta_not_increasing", "AfterCorrection_DESIGNTABLE_13-6_0003.txt")

        # overwrite starting design table, with the before correction design table
        shutil.copy(before_correction_path, design_table_path)

        # this is what the result should look like
        expected_design_table = read_design_table(after_correction_path)

        # read the design table
        design_table = read_design_table(design_table_path)

        # check if the function works correctly
        design_table = HydraRingComputation.check_and_justify_HydraRing_data(design_table, "Waterstand", "13-6_0003", design_table_path)

        assert design_table.equals(expected_design_table)

    def test_hydraring_design_table_beta_below_threshold(self):
        # Set paths to the design tables
        before_correction_path = test_data.joinpath("13-6", "intermediate_results", "HR_results", "waterlevel", "beta_below_threshold", "BeforeCorrection_DESIGNTABLE_13-6_0003.txt")
        design_table_path = test_data.joinpath("13-6", "intermediate_results", "HR_results", "waterlevel", "beta_below_threshold", "DESIGNTABLE_13-6_0003.txt")
        after_correction_path = test_data.joinpath("13-6", "intermediate_results", "HR_results", "waterlevel", "beta_below_threshold", "AfterCorrection_DESIGNTABLE_13-6_0003.txt")

        # overwrite starting design table, with the before correction design table
        shutil.copy(before_correction_path, design_table_path)

        # this is what the result should look like
        expected_design_table = read_design_table(after_correction_path)

        # read the design table
        design_table = read_design_table(design_table_path)

        # check if the function works correctly
        design_table = HydraRingComputation.check_and_justify_HydraRing_data(design_table, "Waterstand", "13-6_0003", design_table_path)

        assert design_table.equals(expected_design_table)


    def test_hydraring_design_table_with_ordered_values(self):
        # Set paths to the design tables
        design_table_path = test_data.joinpath("13-6", "intermediate_results", "HR_results", "waterlevel", "ordered_values", "DESIGNTABLE_13-6_0003.txt")
        
        # this is what the result should look like
        expected_design_table = read_design_table(design_table_path)

        # read the design table
        design_table = read_design_table(design_table_path)

        # check if the function works correctly
        design_table = HydraRingComputation.check_and_justify_HydraRing_data(design_table, "Waterstand", "13-6_0003", design_table_path)

        assert design_table.equals(expected_design_table)

    def test_hydraring_design_table_with_unordered_values(self):
        # Set paths to the design tables
        design_table_path = test_data.joinpath("13-6", "intermediate_results", "HR_results", "waterlevel", "unordered_values", "DESIGNTABLE_13-6_0003.txt")
        
        # read the design table
        design_table = read_design_table(design_table_path)

        with pytest.raises(ValueError):
        # check if the function works correctly
            design_table = HydraRingComputation.check_and_justify_HydraRing_data(design_table, "Waterstand", "13-6_0003", design_table_path)