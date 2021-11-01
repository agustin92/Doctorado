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
    
    def current_mode(self,current,comp = 105):
        self.cs.write('CURR:RANG {}'.format(str(current)))
        self.cs.write('CURR {}'.format(str(current)))
        self.cs.write('CURRent:COMP {}'.format(str(comp)))
        
    def output(self,on = False):
        if on:
            self.cs.write('OUTP ON')
        else:
            self.cs.write('CLE')
    
    def change_current(self,current):
        self.cs.write('SOUR:DELT:HIGH {}'.format(str(current)))
    
    def ask_delta_mode(self):
        return int(self.cs.query('SOUR:DELT:ARM?'))
    
    def reset(self,rang = 0.1,unit='OHMS'):
        self.cs.write('*RST')
        self.cs.write('UNIT {}'.format(unit))
        # self.cs.write("SYST:COMM:SER:SEND \'VOLT:RANG:AUTO ON\' ") # Rango de voltaje automático, comentar para desactivar
        self.cs.write("SYST:COMM:SER:SEND \'VOLT:RANG 0.01\' ")  # Para cambiar el rango de voltaje a mano, 100,10,1,0.1,0.01 V      
#        self.cs.write("SYST:COMM:SER:SEND \'VOLT:RANG {}\' ".format(str(rang)))
        self.cs.write("SYST:COMM:SER:SEND \'VOLT:NPLC 5\' ")
        self.cs.write('CURRent:RANGe:AUTO ON')
        self.cs.write('CURRent:COMP 105')

    def reset_soft(self):
        self.cs.write('*RST')
    
    def stop_meas(self):
        self.cs.write('SOUR:SWE:ABOR')
    
    def measure(self):
        return self.cs.query_ascii_values('SENS:DATA:FRESh?')[0]
    
    def mean_meas(self,samples):
        raux=[]
        for i in range(samples):
            raux.append(self.measure())
            time.sleep(0.2)
        return np.mean(np.array(raux))
            