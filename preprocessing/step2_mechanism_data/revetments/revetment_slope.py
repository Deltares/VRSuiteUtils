from pathlib import Path
import numpy as np

from preprocessing.step2_mechanism_data.revetments.project_utils.readSteentoetsFile import read_steentoets_file
from preprocessing.step2_mechanism_data.revetments.project_utils.belastingen import waterstandsverloop, Hs_verloop, Tp_verloop, betahoek_verloop
from preprocessing.step2_mechanism_data.revetments.project_utils.DiKErnel import DIKErnelCalculations, write_JSON_to_file, read_JSON, read_prfl
from preprocessing.step2_mechanism_data.revetments.project_utils.bisection import bisection
from preprocessing.step2_mechanism_data.revetments.slope_part import SlopePart
from preprocessing.step2_mechanism_data.revetments.project_utils.functions_integrate import issteen

class RevetmentSlope:
    def __init__(self, prfl_path: Path, data):
        self.orientation, self.kruinhoogte, self.dijkprofiel_x, self.dijkprofiel_y = read_prfl(prfl_path.joinpath(data['prfl']))
        self.GWS = data['gws']
        self.Amp = data['getij_amplitude']
        self.region = data['region']
        self.begin_grasbekleding = data['begin_grasbekleding']
        if isinstance(data['steentoetsfile'], str):
            self.steentoetsfile = Path(data['steentoetsfile'])
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

    def add_steentoets(self, steentoets_path):
        if hasattr(self, 'steentoetsfile'):
            steentoets_df = read_steentoets_file(steentoets_path.joinpath(self.steentoetsfile), self.dwarsprofiel)
            self.zst = True
            #add stone slope parts to the slope
            self.slope_parts = []
            for index, row in steentoets_df.iterrows():
                self.slope_parts.append(SlopePart(row, self.doorsnede))
                #grass and stone
            self.check_geometry()
        else:
            pass #only grass
        #TODO: should it crash if the stone slope part is below the end of the grass slope? This would mean that the input is inconsistent

    def check_geometry(self):
        def find_grass_slope_zo(slope_parts):
            for slope_part in slope_parts:
                if float(slope_part.toplaagtype) == 20.0: #TODO include other grass types?
                    return slope_part.Zo
                else:
                    pass
                    #not found return top
            return slope_part.Zb
        #the grass slope should not be below the stone slope
        slope_grass_limit = find_grass_slope_zo(self.slope_parts)
        if slope_grass_limit > self.begin_grasbekleding:
            #steentoets is beschikbaar, dan geldt de overgangshoogte op basis van steentoets
            self.begin_grasbekleding = slope_grass_limit
            print(f'WARNING: Het opgegeven eind_grasbekleding ligt lager dan de overgang op basis van steentoets voor dwarsprofiel {self.dwarsprofiel}. Overgangshoogte uit Steentoets wordt gebruikt.')
        elif slope_grass_limit < self.begin_grasbekleding:
            self.begin_grasbekleding = slope_grass_limit
            print(f'WARNING: Het opgegeven eind_grasbekleding ligt hoger dan de overgang op basis van steentoets voor dwarsprofiel {self.dwarsprofiel}. Overgangshoogte uit Steentoets wordt gebruikt.')