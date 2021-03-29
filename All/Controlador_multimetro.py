# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 09:20:52 2019

@author: Agustin Lopez Pedroso
"""

import visa
import numpy as np
import time
#import statistics as st

rm = visa.ResourceManager()

#K6221 = rm.open_resource('GPIB0::12::INSTR')
#print(K6221.query('*IDN?'))
#K6221.write('*RST')

class K2010():
    def __init__(self):
        self.mult = rm.open_resource('GPIB0::16::INSTR')
    
    def idn(self):
        print(self.mult.query('*IDN?'))
    
    def reset(self):
        self.mult.write('*RST')
        
    def mode_2wire(self,nplc='5'):
        self.mult.write('SENS:FUNC \'RES\'')
        self.mult.write('SENS:RES:RANG:AUTO ON')
        self.mult.write('SENS:RES:NPLC {}'.format(nplc))
#        self.mult.write('CONF:{}'.format(str(modo)))
    
    def mode_4wire(self,nplc='5'):
        self.mult.write('SENS:FUNC \'FRES\'')
        self.mult.write('SENS:FRES:RANG:AUTO ON')
        self.mult.write('SENS:FRES:NPLC {}'.format(nplc))
        
    def ask_modo(self):
        return self.mult.query('CONF?')
    
    def single_shot(self):
        return self.mult.query_ascii_values('READ?')
    
    def measure(self):
        return self.mult.query_ascii_values('SENS:DATA:FRESH?')[0]
    
    def continuous_mode(self,on=False):
        if on:
            self.mult.write('INIT:CONT ON')
        else:
            self.mult.write('INIT:CONT OFF')
            
    def mean_meas(self,samples):
        raux=[]
        for i in range(samples):
            raux.append(self.measure())
            time.sleep(0.2)
        return np.mean(np.array(raux))
            
        