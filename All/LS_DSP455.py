# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 00:08:24 2021

@author: Agustin Lopez Pedroso
agustin.lopezpedroso@gmail.com
"""

import visa
import numpy as np
import time

rm = visa.ResourceManager()

class DSP_455():
    
    def __init__(self):
        self.gm = rm.open_resource('GPIB0::13::INSTR')
    
    def idn(self):
        print(self.gm.query('*IDN?'))
    
    def get_field(self):
        # field = self.gm.query('RDGFIELD?')
        # len_a = len(field)
        # start = 0
        # end = len_a
        # for i in range(len_a):
        #     if field[i] == '+':
        #         start = i
        # for i in range(len_a):
        #     if field[i] == "\r" :
        #         end = i
        # field = float(field[start+1:end])        
        return float(self.gm.query('RDGFIELD?'))
    
    def mean_field(self,samples, sleep=0.5):
        field_aux = []
        for i in range(samples):
            field_aux.append(self.get_field())
            time.sleep(sleep)
        return np.array(field_aux).mean()