import os
from scipy import interpolate
import numpy as np
import json
from scipy.special import ndtri

class HydraNLReadWaterLevel:
    def __init__(self, work_dir: str, loc: str, correct_uncer: bool, decim_type: str):

        self.work_dir = work_dir
        self.loc = loc
        self.correct_uncer = correct_uncer
        self.decim_type = decim_type

    def export_json(self, file_name: str):

        file_path = os.path.join(self.work_dir,self.loc,'Berekeningen','waterstand','hfreq.txt')
        value, prob, beta, return_period = read_txt(file_path)

        if self.correct_uncer:
            value = value+get_decim(prob, value, self.decim_type)

        write_json_to_file(self, 'waterlevel', file_name, value, prob, beta, return_period)


class HydraNLReadOverflow:
    def __init__(self, work_dir: str, loc: str, correct_uncer: bool, decim_type: str, prfl: str, h_d: float, q_crit: int):

        self.work_dir = work_dir
        self.loc = loc
        self.correct_uncer = correct_uncer
        self.decim_type = decim_type
        self.prfl = prfl.split('.')[0]
        self.h_d = h_d
        self.q_crit = int(q_crit)
        
    def export_json(self, file_name: str):

        file_path = os.path.join(self.work_dir,self.loc,'Berekeningen',f'hbn_{self.prfl}_{self.q_crit}','ffq.txt')
        value, prob, beta, return_period = read_txt(file_path)

        if self.correct_uncer:
            value = value+get_decim(prob, value, self.decim_type)

        value_grid = np.arange(self.h_d-1.0, self.h_d+2.0, 0.25)
        f = interpolate.interp1d(value, np.log(prob), fill_value=('extrapolate'))
        prob_grid = [np.exp(float(f(val))) for val in value_grid]
        beta_grid = [-ndtri(val) for val in prob_grid]
        f = interpolate.interp1d(value, np.log(return_period), fill_value=('extrapolate'))
        return_period_grid = [np.exp(float(f(val))) for val in value_grid]

        write_json_to_file(self, 'overflow', file_name, value_grid, prob_grid, beta_grid, return_period_grid)


def read_txt(file_path: str):

    f = open(file_path,'r')
    value = []; freq = []
    for line in f.readlines()[1:]:
        value.append(float(line.split()[0]))
        freq.append(float(line.split()[1]))
       
    prob = [1-np.exp(-val) for val in freq] # translate frequency to probability
    beta = [-ndtri(val) for val in prob] # translate probability to beta
    return_period = [1/val for val in freq] # translate frequency to return period

    f.close()

    return value, prob, beta, return_period
    
def write_json_to_file(self, calc_type: str, file_name: str, value: list[float], prob: list[float], beta: list[float], return_period: list[float]):

    if calc_type=='waterlevel':
        data = {'location': self.loc,
                'waterlevel':{'value': list(value), 
                            'probability': list(prob),
                            'beta': list(beta),
                            'return_period': list(return_period)}}

    elif calc_type=='overflow':
        data = {'location': self.loc,
                'prfl': self.prfl,
                'q_crit': self.q_crit,
                'dike_height': self.h_d,
                'overflow':{'value': list(value), 
                            'probability': list(prob),
                            'beta': list(beta),
                            'return_period': list(return_period)}}
    else:
        raise ValueError('calc_type must be either waterlevel or overflow')

    jstr = json.dumps(data, indent = 4)
    with open(file_name, 'w') as outfile:
        outfile.write(jstr)

def get_decim(prob: list[float], value: list[float], decim_type: str):
    
    if decim_type=='decim_simple':

        T1 = 1000.0
        T2 = 10000.0

        f = interpolate.interp1d(np.log(prob), value, fill_value=('extrapolate'))
        value_T1 = f(np.log(1/T1))
        value_T2 = f(np.log(1/T2))
        corr = value_T2 - value_T1

    elif decim_type=='decim_10':
        
        f = interpolate.interp1d(np.log(prob), value, fill_value=('extrapolate'))
        prob_10 = [val/10.0 for val in prob]
        value_10 = f(np.log(np.array(prob_10)))
        corr = value_10 - value
    
    else:
        raise ValueError('decim_type must be either decim_simple or decim_10')

    return corr