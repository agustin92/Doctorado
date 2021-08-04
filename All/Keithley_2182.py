# -*- coding: utf-8 -*-
"""
Created on Tue Jul 27 13:11:59 2021

@author: Agustin Lopez Pedroso
agustin.lopezpedroso@gmail.com
"""

import visa
import numpy as np
import time
#import statistics as st

rm = visa.ResourceManager()

#K6221 = rm.open_resource('GPIB0::12::INSTR')
#print(K6221.query('*IDN?'))
#K6221.write('*RST')

class K2182():
    def __init__(self):
        self.nv = rm.open_resource('GPIB0::7::INSTR')
    
    def idn(self):
        print(self.nv.query('*IDN?'))
    
    def reset(self):
        self.nv.write('*RST')
    
    def mode(self,mode='volt'):
        # self.nv.write('SENS:FUNC VOLT')
        self.nv.write('SENS:VOLT:RANG 100')
        # self.nv.write('SENS:VOLT:RANG:AUTO ON')
        self.nv.write('SENS:VOLT:NPLC 5')
        
    def measure(self):
        return self.nv.query_ascii_values('SENS:DATA:FRESh?')[0]
    
    def mean_meas(self,samples):
        raux=[]
        for i in range(samples):
            raux.append(self.measure())
            time.sleep(0.1)
        return np.mean(np.array(raux))
    

    def output(self,on = False):
        if on:
            self.nv.write('INIT:CONT ON')
        else:
            self.nv.write('INIT:CONT OFF')

    

    
