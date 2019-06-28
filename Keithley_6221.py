# -*- coding: utf-8 -*-
"""
Created on Wed May 15 16:07:07 2019

@author: Agustin Lopez Pedroso
"""

import visa
import numpy as np
import time
import statistics as st

rm = visa.ResourceManager()

#K6221 = rm.open_resource('GPIB0::12::INSTR')
#print(K6221.query('*IDN?'))
#K6221.write('*RST')

class K6221():
    def __init__(self):
        self.cs = rm.open_resource('GPIB0::10::INSTR')
    
    def idn(self):
        print(self.cs.query('*IDN?'))
        
    def delta_mode(self,current,delay =0.1, count = 'inf'):
        self.cs.write('SOUR:DELT:HIGH {}'.format(str(current)))
        self.cs.write('SOUR:DELT:DELAY {}'.format(str(delay)))
        self.cs.write('SOUR:DELT:COUN {}'.format(str(count)))
        self.cs.write('SOUR:DELT:CAB on')
        self.cs.write('SOUR:DELT:ARM')
        self.cs.write('INIT:IMM')
    
    def reset(self):
        self.cs.write('*RST')
        self.cs.write('UNIT OHMS')
    
    def stop_meas(self):
        self.cs.write('SOUR:SWE:ABOR')
    
    def measure(self):
        return self.cs.query_ascii_values('SENS:DATA:LATEST?')[0]
    
    def mean_meas(self,samples):
        raux=[]
        for i in range(samples):
            raux.append(self.measure())
            time.sleep(0.2)
        return st.mean(raux)
            