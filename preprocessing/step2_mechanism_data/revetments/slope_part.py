from preprocessing.step2_mechanism_data.revetments.project_utils.functions_integrate import issteen

class SlopePart:
    def __init__(self, steentoets_series):
        #put values in series as attributes
        self.__dict__ = steentoets_series.to_dict()
        #check if it is a stone slope part
        self.stone = self.check_steen()
    
    def check_steen(self):
        if issteen(self.toplaagtype):
            return True
        else:
            return False