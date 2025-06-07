import pytest
from pathlib import Path
import pandas as pd
from preprocessing.step4_build_sqlite_db.read_intermediate_outputs import *
from tests import test_data

@pytest.mark.parametrize(
    "traject,piping_csv",
    [('35-1', test_data.joinpath('35-1', 'input_files', 'default_files', 'Piping_default.csv'))]
)
class TestPipingInput:
    def test_read_piping_csv(self, traject, piping_csv):
        df_piping = read_piping_data(piping_csv)
        _reference_file = piping_csv.parent.parent.parent.joinpath('reference_data', 'Piping_default.csv')
        df_piping_ref = read_piping_data(piping_csv)
        assert df_piping.equals(df_piping_ref), f"Files are not the same"

    def test_parameterized_piping_input_works(self, traject, piping_csv):
        df_piping = read_piping_data(piping_csv)
        df_piping = df_piping.iloc[0:1, :]
        validate_piping_data(df_piping)

    def test_double_piping_input_crashes(self, traject, piping_csv):
        df_piping = read_piping_data(piping_csv)
        df_piping = df_piping.iloc[1:2, :]
        with pytest.raises(ValueError):
            validate_piping_data(df_piping)

    def test_direct_piping_input_works(self, traject, piping_csv):
        df_piping = read_piping_data(piping_csv)
        df_piping = df_piping.iloc[2:3, :]
        validate_piping_data(df_piping)