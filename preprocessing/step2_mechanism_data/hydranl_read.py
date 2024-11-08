import pandas as pd
import os
from scipy import interpolate
import numpy as np
import json
from scipy.special import ndtri

class HydraNLReadWaterLevel:
    def __init__(self, work_dir, loc, correct_uncer):

        self.work_dir = work_dir
        self.loc = loc
        self.correct_uncer = correct_uncer

    def __read_txt(self):

        freq = 'waterstand/hfreq.txt'
        file_name = os.path.join(self.work_dir,self.loc,'Berekeningen',freq)
        
        f = open(file_name,'r')
        value = []; prob = []
        for line in f.readlines()[1:]:
            value.append(float(line.split()[0]))
            prob.append(float(line.split()[1]))
        
        beta = [-ndtri(val) for val in prob]
        return_period = [1/val for val in prob]

        f.close()

        return value, prob, beta, return_period
    
    def __write_json_to_file(self, file_name, value, prob, beta, return_period):

        data = {'location': self.loc,
                'waterlevel':{'value': list(value), 
                              'probability': list(prob),
                              'beta': list(beta),
                              'return_period': list(return_period)}}

        jstr = json.dumps(data, indent = 4)
        with open(file_name, 'w') as outfile:
            outfile.write(jstr)

    def export_json(self, file_name):

        value, prob, beta, return_period = self.__read_txt()

        if self.correct_uncer:
            value = value+get_decim(prob, value)

        self.__write_json_to_file(file_name, value, prob, beta, return_period)


class HydraNLReadOverflow:
    def __init__(self, work_dir, loc, correct_uncer, prfl, h_d, q_crit):

        self.work_dir = work_dir
        self.loc = loc
        self.prfl = prfl.split('.')[0]
        self.q_crit = int(q_crit)
        self.correct_uncer = correct_uncer
        self.h_d = h_d
        
    def __read_txt(self):

        freq = f'hbn_{self.prfl}_{self.q_crit}/ffq.txt'
        file_name = os.path.join(self.work_dir,self.loc,'Berekeningen',freq)
        
        f = open(file_name,'r')
        value = []; prob = []
        for line in f.readlines()[1:]:
            value.append(float(line.split()[0]))
            prob.append(float(line.split()[1]))
        
        beta = [-ndtri(val) for val in prob]
        return_period = [1/val for val in prob]

        f.close()

        return value, prob, beta, return_period
    
    def __write_json_to_file(self, file_name, value, prob, beta, return_period):

        data = {'location': self.loc,
                'prfl': self.prfl,
                'q_crit': self.q_crit,
                'dikeheight': self.h_d,
                'overflow':{'value': list(value), 
                            'probability': list(prob),
                            'beta': list(beta),
                            'return_period': list(return_period)}}

        jstr = json.dumps(data, indent = 4)
        with open(file_name, 'w') as outfile:
            outfile.write(jstr)

    def export_json(self, file_name):

        value, prob, beta, return_period = self.__read_txt()

        if self.correct_uncer:
            value = value+get_decim(prob, value)

        value_grid = np.arange(self.h_d-1.0, self.h_d+2.0, 0.25)
        f = interpolate.interp1d(value, np.log(prob), fill_value=('extrapolate'))
        prob_grid = [np.exp(float(f(val))) for val in value_grid]
        beta_grid = [-ndtri(val) for val in prob_grid]
        return_period_grid = [1/val for val in prob_grid]

        self.__write_json_to_file(file_name, value_grid, prob_grid, beta_grid, return_period_grid)

def get_decim(prob, value):
    
    T1 = 1000.0
    T2 = 10000.0

    f = interpolate.interp1d(np.log(prob), value, fill_value=('extrapolate'))
    value_T1 = f(np.log(1/T1))
    value_T2 = f(np.log(1/T2))
        
    return value_T2 - value_T1            