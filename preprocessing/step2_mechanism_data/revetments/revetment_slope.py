from pathlib import Path
import numpy as np

from preprocessing.step2_mechanism_data.revetments.project_utils.belastingen import waterstandsverloop, Hs_verloop, Tp_verloop, betahoek_verloop
from preprocessing.step2_mechanism_data.revetments.project_utils.DiKErnel import DIKErnelCalculations, write_JSON_to_file, read_JSON, read_prfl
from preprocessing.step2_mechanism_data.revetments.project_utils.bisection import bisection

class RevetmentSlope:
    def __init__(self, prfl_path: Path, data):
        self.orientation, self.kruinhoogte, self.dijkprofiel_x, self.dijkprofiel_y = read_prfl(prfl_path.joinpath(data['prfl']))
        self.GWS = data['gws']
        self.Amp = data['getij_amplitude']
        self.region = data['region']
        self.begin_grasbekleding = data['begin_grasbekleding']
        self.dwarsprofiel = data['dwarsprofiel']
        self.doorsnede = data['doorsnede']
        self.end_grasbekleding = self.kruinhoogte - 0.01

        #define a grid of transition levels
        self.check_crest_and_begin_gras()

        #check if GWS and Amp are filled in, otherwise fill with 0.0
        self.check_GWS_Amp()

    def check_crest_and_begin_gras(self):
        # try if begin_grasbekleding is larger than kruinhoogte, if so: error
        if self.begin_grasbekleding > self.kruinhoogte:
            print(f'ERROR: Begin grasbekleding ({self.begin_grasbekleding}) is groter dan de kruinhoogte afgelezen uit het dwarsprofiel (={self.kruinhoogte}) '
                  f'voor dwarsprofiel {self.dwarsprofiel}. Pas het begin_grasbekleding in de Bekledingen.csv aan of'
                  f'controleer het profielbestand')
            exit()
            
        



    def check_GWS_Amp(self):
        if np.isnan(self.GWS):
            self.GWS = 0.0
            print(f'WARNING: GWS voor {self.dwarsprofiel} is niet ingevuld. GWS=0.0 aangenomen.')
        if np.isnan(self.Amp):
            self.Amp = 0.0
            print(f'WARNING: Amp voor {self.dwarsprofiel} is niet ingevuld. Amp=0.0 aangenomen.')
