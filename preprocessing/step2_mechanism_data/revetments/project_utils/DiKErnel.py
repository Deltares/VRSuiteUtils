# -*- coding: utf-8 -*-
"""
Created on Thu Mar 23 15:26:38 2023

@author: wojciech
"""

import json
import os
import numpy as np
from pathlib import Path
import subprocess

class DIKErnelCalculations(object):
    
    def __init__(self, tijdstippen, waterstand, Hs, Tp, betahoek, x, y, positie):

        self.tijdstippen = list(tijdstippen)
        self.waterstand = list(waterstand)
        self.Hs = list(Hs)
        self.Tp = list(Tp)
        self.betahoek = list(betahoek)
        self.x = list(x)
        self.y = list(y)
        self.positie = positie

    def gras_golfklap_input_JSON(self, typeZode, local_path):

        data = {"tijdstippen": self.tijdstippen, 
                "hydraulischeBelastingen": {"waterstanden": self.waterstand, "golfhoogtenHm0": self.Hs, "golfperiodenTm10": self.Tp, "golfhoeken": self.betahoek},
                "dijkprofiel": {"posities": self.x, "hoogten": self.y, "teenBuitenzijde": self.x[0], "kruinBuitenzijde": self.x[-1]}, 
                "locaties": [{"positie": self.positie, "rekenmethode": "grasGolfklap", "typeToplaag": typeZode}]}

        write_JSON_to_file(data, local_path.joinpath("input.json"))
            
    def gras_golfoploop_input_JSON(self, typeZode, local_path):
        
        # calculate tanalpha
        ind = np.argwhere((self.positie>=self.x[0:-1]) & (self.positie<=self.x[1:]))[0][0]
        tanalpha = (self.y[ind+1]-self.y[ind])/(self.x[ind+1]-self.x[ind])
        
        data = {"tijdstippen": self.tijdstippen, 
                "hydraulischeBelastingen": {"waterstanden": self.waterstand, "golfhoogtenHm0": self.Hs, "golfperiodenTm10": self.Tp, "golfhoeken": self.betahoek},
                "dijkprofiel": {"posities": self.x, "hoogten": self.y, "teenBuitenzijde": self.x[0], "kruinBuitenzijde": self.x[-1]}, 
                "locaties": [{"positie": self.positie, "rekenmethode": "grasGolfoploop", "typeToplaag": typeZode, "tanA": tanalpha}],
                "rekenmethoden": [{"rekenmethode": "grasGolfoploop", "rekenprotocol": {"typeRekenprotocol": "rayleighDiscreet"}}]} 
        
        write_JSON_to_file(data, local_path.joinpath("input.json"))

    def run_DIKErnel(self, binDIKErnel, output_path, local_path, region):

        dike_kernel_exe = binDIKErnel.joinpath('DiKErnel-cli.exe')
        input_json_path = local_path.joinpath("input.json")
        output_json_path = output_path.joinpath('output.json')
        # os.system(str(dike_kernel_exe) + ' --invoerbestand project_utils/input.json '+ '--uitvoerbestand output.json --uitvoerniveau schade')
        cmdstring = '"{}" --invoerbestand "{}" --uitvoerbestand "{}" --uitvoerniveau fysica'.format(dike_kernel_exe, input_json_path, output_json_path)
        #run cmdsring using subprocess
        subprocess.run(cmdstring, shell=True)

        # with open('output.json', 'r') as openfile:
        with open(output_json_path, 'r') as openfile:
            json_object = json.load(openfile)
            
        schadegetalPerTijdstap = json_object['uitvoerdata']['locaties'][0]['schade']['schadegetalPerTijdstap']
        toenameSchade = json_object['uitvoerdata']['locaties'][0]['fysica']['toenameSchade']
        
        os.remove(output_json_path)
        
        if region=='rivieren':
            schade = max(toenameSchade) # maximum damage
        else:
            schade = max(schadegetalPerTijdstap) # cumulative damage

        return schade
    
def write_JSON_to_file(data, file_name):
        
    jstr = json.dumps(data, indent = 4)
        
    with open(file_name, "w") as outfile:
        outfile.write(jstr)
        
def read_JSON(file_name):
    
    with open(file_name, 'r') as openfile:
        json_object = json.load(openfile)
        
    return json_object

def read_prfl(file_name):
    with open(file_name) as f:
        lines = f.readlines()
    
    x = []
    y = []
    i = 0

    for line in lines:
        if 'RICHTING' in line:
           richting = float(line.split()[-1])
        
        if 'KRUINHOOGTE' in line:
            kruinhoogte = float(line.split()[-1])
        
        if 'DIJK' in line:
            noPoints = int(line.split()[-1])
            
            for j in range(i+1, i+1+noPoints):
                
                x = np.append(x, float(lines[j].split()[0]))
                y = np.append(y, float(lines[j].split()[1]))
        i += 1

    return richting, kruinhoogte, x, y

def read_prfl_foreland(file_name):
    with open(file_name) as f:
        lines = f.readlines()

    x_voorland = []
    y_voorland = []
    k = 0
    foreland_present = False

    for line in lines:

        if 'VOORLAND' in line:
            foreland_present = True
            noPoints = int(line.split()[-1])

            for j in range(k + 1, k + 1 + noPoints):
                x_voorland = np.append(x_voorland, float(lines[j].split()[0]))
                y_voorland = np.append(y_voorland, float(lines[j].split()[1]))
        k += 1

    if foreland_present:
        return x_voorland, y_voorland
    else:
        pass
