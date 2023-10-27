## This script runs a multitude of HBN calculations for various locations read from an Excel sheet.
## It uses reference HBN calculation files which it copies many times.

import fileinput
import shutil
import sys

import numpy as np
import pandas as pd

from preprocessing.step2_mechanism_data.hydraring_computation import (
    HydraRingComputation,
)

# import matplotlib.pyplot as plt


class OverflowComputationInput(HydraRingComputation):
    def __init__(self):
        self.CalculationTypeID = 6
        self.MechanismID = 101

    def get_critical_discharge(self, discharge_path):
        critical_discharges = pd.read_csv(discharge_path, index_col=0)
        try:
            subset = critical_discharges.loc[self.sod_class]

        except:
            raise Exception("Zodeklasse {} niet gevonden".format(self.sod_class))

        if isinstance(subset, pd.Series):
            pass
        else:
            subset = subset.loc[subset.Golfhoogteklasse == self.wave_class].squeeze()

        self.mu = subset.mu
        self.sigma = subset.sigma

    def fill_data(self, data):
        self.name = str(data.doorsnede)
        self.orientation = data.orientatie
        self.dike_height = data.dijkhoogte
        self.sod_class = data.zodeklasse
        self.wave_class = data.bovengrens_golfhoogteklasse
        self.HRLocation = data.hrlocation

    def get_prfl(self, fileName):
        prfl = {}
        count_for = ""
        for line in fileinput.input(fileName):
            if "VERSIE" in line:
                if line.split()[1] != "4.0":
                    raise Exception("prfl moet versie 4.0 zijn")
            elif "ID" in line:
                prfl["ID"] = line.split()[1]
            elif "RICHTING" in line:
                try:
                    prfl["RICHTING"] = np.int_(line.split()[1])
                except:
                    prfl["RICHTING"] = np.float_(line.split()[1])
                # TODO: maybe add a check with orientation property
            elif "VOORLAND" in line:
                count_for = "VOORLAND"
                count = 0
                total_count = np.int_(line.split()[1])
                voorland_array = np.empty((total_count, 3))
            elif "KRUINHOOGTE" in line:
                prfl["KRUINHOOGTE"] = np.float_(line.split()[1])
            elif "DIJK" in line:
                count_for = "DIJK"
                count = 0
                total_count = np.int_(line.split()[1])
                dijk_array = np.empty((total_count, 3))
                pass
            elif "DAMWAND" in line:  # not used in Riskeer
                pass
            elif "DAMHOOGTE" in line:
                prfl["DAMHOOGTE"] = line.split()[1]
            elif "DAM" in line:  # damtype
                prfl["DAM"] = line.split()[1]
            elif "MEMO" in line:
                pass
            else:
                if count_for != "":
                    if total_count == count:
                        count = 0
                        count_for = ""
                    # add points for voorland or dijk
                    elif count_for == "VOORLAND":
                        voorland_array[count, :] = np.array(
                            line.split(), dtype=np.float32
                        )
                        count += 1
                    elif count_for == "DIJK":
                        dijk_array[count, :] = np.array(line.split(), dtype=np.float32)
                        count += 1
                    # if total_count == count:
                    #     count = 0
                    #     count_for = ''
                else:
                    pass

        prfl["DIJK"] = dijk_array
        prfl["VOORLAND"] = voorland_array
        if prfl["DAM"] != "0":
            raise Exception(
                "Profiel {} bevat een dam, dit is niet ondersteund".format(
                    fileName.stem
                )
            )
        self.prfl = prfl

    def make_SQL_file(
        self, path, reference_file, lower_bound=-1, upper_bound=2, step_size=0.25
    ):
        new_sql = path.joinpath(self.name + ".sql")
        shutil.copy(reference_file, new_sql)

        # changes values in sql for Location, orientation, claculation method and variables
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace("LocationName", self.name))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace("HLCDID", str(self.HRLocation)))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace("ORIENTATION", str(self.prfl["RICHTING"])))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(
                line.replace("TIMEINTEGRATION", str(self.TimeIntegrationScheme))
            )
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(
                line.replace("Hmin", str(self.prfl["KRUINHOOGTE"] + lower_bound))
            )
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(
                line.replace("Hmax", str(self.prfl["KRUINHOOGTE"] + upper_bound))
            )
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace("Hstep", str(step_size)))
        # insert the correct parameters
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace("KRUINHOOGTE", str(self.prfl["KRUINHOOGTE"])))

        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace("MU_QC", str(self.mu / 1000)))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace("SIGMA_QC", str(self.sigma / 1000)))

        # TODO add proper Numerics settings

        # write profiles to file
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            if "INSERTPROFILES" in line:
                # loop over points:
                for k in range(0, self.prfl["DIJK"].shape[0]):
                    sys.stdout.write(
                        "INSERT INTO [Profiles] VALUES ({:d}, {:d}, {:.3f}, {:.3f});".format(
                            1, k + 1, self.prfl["DIJK"][k, 0], self.prfl["DIJK"][k, 1]
                        )
                        + "\n"
                    )
            elif "INSERTCALCULATIONPROFILE" in line:
                # loop over points:
                for k in range(0, self.prfl["DIJK"].shape[0]):
                    sys.stdout.write(
                        "INSERT INTO [CalculationProfiles] VALUES ({:d}, {:d}, {:.3f}, {:.3f}, {:.3f});".format(
                            1,
                            k + 1,
                            self.prfl["DIJK"][k, 0],
                            self.prfl["DIJK"][k, 1],
                            self.prfl["DIJK"][k, 2],
                        )
                        + "\n"
                    )
            elif "INSERTFORELANDGEOMETRY" in line:
                # loop over points:
                for k in range(0, self.prfl["VOORLAND"].shape[0]):
                    sys.stdout.write(
                        "INSERT INTO [FORELANDS] VALUES ({:d}, {:d}, {:.3f}, {:.3f});".format(
                            1,
                            k + 1,
                            self.prfl["VOORLAND"][k, 0],
                            self.prfl["VOORLAND"][k, 1],
                        )
                        + "\n"
                    )
            elif "INSERTBREAKWATER" in line:
                pass
            elif "ADDNUMERICSHERE" in line:
                # add the different fields from Numerics and write them to the file
                for count, k in self.NumericsTable.iterrows():
                    sys.stdout.write(
                        "INSERT INTO [Numerics] VALUES (1, {}, 1, 1, {}, {}, {}, {}, {}, {}, {}, {}, {}, 3, {}, {}, {}, {}, {}, {});".format(
                            int(k.MechanismID),
                            int(k.SubMechanismID),
                            int(k.CalculationMethod),
                            int(k.FORM_StartMethod),
                            int(k.FORM_NIterations),
                            k.FORM_RelaxationFactor,
                            k.FORM_EpsBeta,
                            k.FORM_EpsHOH,
                            k.FORM_EpsZFunc,
                            int(k.DS_StartMethod),
                            int(k.DS_Min),
                            int(k.DS_Max),
                            k.DS_VarCoefficient,
                            int(k.NI_UMin),
                            int(k.NI_UMax),
                            int(k.NI_NumberSteps),
                        )
                        + "\n"
                    )

            else:
                sys.stdout.write(line)
