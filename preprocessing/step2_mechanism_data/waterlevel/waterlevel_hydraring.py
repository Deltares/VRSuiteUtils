import fileinput
import os
import shutil
import sys

from preprocessing.step2_mechanism_data.hydraring_computation import (
    HydraRingComputation,
)


class WaterlevelComputationInput(HydraRingComputation):
    def __init__(
        self,
        HRING_path=r"C:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236\MechanismComputation.exe",
    ):
        self.CalculationTypeID = 0
        self.MechanismID = 1
        # Prototype initialization 3.x:
        super().__init__(HRING_path=HRING_path)

    def fill_data(self, data):
        self.name = str(data.doorsnede)
        self.h_min = data.ondergrens
        self.h_max = data.bovengrens
        self.HRLocation = data.hrlocation

    def make_SQL_file(self, path, reference_file, step_size=0.25, t_2100=False):
        new_sql = path.joinpath(self.name + ".sql")
        shutil.copy(reference_file, new_sql)

        # changes values in sql
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace("LocationName", self.name))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace("HLCDID", str(self.HRLocation)))

        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(
                line.replace("TIMEINTEGRATION", str(self.TimeIntegrationScheme))
            )
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            if not t_2100:
                sys.stdout.write(line.replace("Hmin", str(self.h_min)))
            else:
                sys.stdout.write(line.replace("Hmin", str(self.h_min + 0.75)))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            if not t_2100:
                sys.stdout.write(line.replace("Hmax", str(self.h_max)))
            else:
                sys.stdout.write(line.replace("Hmax", str(self.h_max + 0.75)))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace("Hstep", str(0.25)))
