
from preprocessing.step2_mechanism_data.hydraring_computation import HydraRingComputation

class WaterlevelComputationInput(HydraRingComputation):

    def __init__(self,HRING_path = r"C:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236\MechanismComputation.exe"):
        self.ComputationID = 0
        self.MechanismID = 1
        # Prototype initialization 3.x:
        super().__init__(HRING_path=HRING_path)
    def fill_data(self,data):
        self.name = data.dijkvak
        self.h_min = data.ondergrens
        self.h_max = data.bovengrens
        self.HRLocation = data.HRLocation

    def make_SQL_file(self):
        pass

    def make_ini_file(self):
        pass
