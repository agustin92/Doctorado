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
        print(self.nv.query('*IDN?')) #Devuelve el fabricante, número de modelo,
        #número de serie, y niveles de revisión de firmware de la unidad.
    
    def reset(self):
        self.nv.write('*RST') #Vuelve a las condiciones predeterminadas *RST
    
    def mode(self,mode='volt'): 
        self.nv.write('SENS:FUNC \'VOLT\'')
        self.nv.write('SENS:VOLT:RANG 0.01')  # Para cambiar el rango de voltaje a mano, 100,10,1,0.1,0.01 V 
        # self.nv.write('SENS:VOLT:RANG:AUTO ON')
        self.nv.write('SENS:VOLT:NPLC 5')# Para cambiar el rate a mano, (0.1 fast, 1 medium, 5 slow) 
        
    def calibrate(self):
        #measuring the internal temperature
        self.nv.write('SENS:TEMP:TRAN INT')
        self.nv.write('SENS:FUNC \'TEMP\'')
        self.nv.write('INIT:CONT ON')
        T_int = self.nv.query_ascii_values('SENS:DATA:FRESh?')[0]
        T_cal = self.nv.query_ascii_values('CAL:UNPR:ACAL:TEMP?')[0]
        if np.absolute(T_int - T_cal) > 1:
            self.nv.write(':CAL:UNPR:ACAL:INIT')
            self.nv.write(':CAL:UNPR:ACAL:STEP2')
            self.nv.write(':CAL:UNPR:ACAL:DONE')
       
    def measure(self):
        return self.nv.query_ascii_values('SENS:DATA:FRESh?')[0] #Return a new (fresh) reading.
    
    def mean_meas(self,samples):
        raux=[]
        for i in range(samples):
            raux.append(self.measure())
            time.sleep(0.15)
        return np.mean(np.array(raux)),np.std(np.array(raux))
    

    def output(self,on = False):
        if on:
            self.nv.write('INIT:CONT ON')
        else:
            self.nv.write('INIT:CONT OFF')    
