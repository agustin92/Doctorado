# -*- coding: utf-8 -*-
"""
Created on Wed May 15 16:07:07 2019

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

class K6221():
    def __init__(self):
        self.cs = rm.open_resource('GPIB0::10::INSTR')
    
    def idn(self):
        print(self.cs.query('*IDN?'))
        
    def delta_mode(self,current,delay =0.1, count = 'inf'):
        if not self.ask_delta_mode():
            self.cs.write('SOUR:DELT:HIGH {}'.format(str(current)))
            self.cs.write('SOUR:DELT:DELAY {}'.format(str(delay)))
            self.cs.write('SOUR:DELT:COUN {}'.format(str(count)))
            self.cs.write('SOUR:DELT:CAB on')

            self.cs.write('SOUR:DELT:ARM')
            tiempo_aux_ini = time.time()
            tiempo_aux = tiempo_aux_ini
            while (tiempo_aux - tiempo_aux_ini) < 5:
                tiempo_aux = time.time()
            while not self.ask_delta_mode():
                self.cs.write('SOUR:DELT:ARM')
                tiempo_aux_ini = time.time()
                tiempo_aux = tiempo_aux_ini
                while (tiempo_aux - tiempo_aux_ini) < 1:
                    tiempo_aux = time.time()
            self.cs.write('INIT:IMM')
    
    def change_current(self,current):
        self.cs.write('SOUR:DELT:HIGH {}'.format(str(current)))
    
    def ask_delta_mode(self):
        return int(self.cs.query('SOUR:DELT:ARM?'))
    
    def reset(self,rang = 0.1,unit='OHMS'):
        self.cs.write('*RST')
        self.cs.write('UNIT {}'.format(unit))
        self.cs.write("SYST:COMM:SER:SEND \'VOLT:RANG:AUTO ON\' ")
#        self.cs.write("SYST:COMM:SER:SEND \'VOLT:RANG {}\' ".format(str(rang)))
        self.cs.write("SYST:COMM:SER:SEND \'VOLT:NPLC 5\' ")
        self.cs.write('CURRent:RANGe:AUTO ON')
        self.cs.write('CURRent:COMP 100')


    
    def stop_meas(self):
        self.cs.write('SOUR:SWE:ABOR')
    
    def measure(self):
        return self.cs.query_ascii_values('SENS:DATA:FRESh?')[0]
    
    def mean_meas(self,samples):
        raux=[]
        for i in range(samples):
            raux.append(self.measure())
            tiempo_aux_ini = time.time()
            tiempo_aux = tiempo_aux_ini
            while (tiempo_aux - tiempo_aux_ini) < 0.2:
                tiempo_aux = time.time()
        return np.mean(np.array(raux))
            