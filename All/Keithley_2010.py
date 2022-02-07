# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 15:48:57 2022

@author: Lara 
laramsolis@gmail.com
"""

import visa
#import numpy as np
#import time

rm = visa.ResourceManager()


class K2010():
    def __init__(self):
        self.nv = rm.open_resource('GPIB0::16::INSTR') #ojo que cambia. Revisar en VISA Interactive Control
    
    def idn(self):
        print(self.nv.query('*IDN?')) 
    
    def reset(self):
        self.nv.write('*RST') #Vuelve a las condiciones predeterminadas *RST
        self.nv.write('TRAC:CLE') #Borra el búfer de lecturas anteriores
        
#    def temp_mode(self,temp):

    
    def mode(self,mode='temp'): 
        self.nv.write('FUNC \'TEMP\'')
        self.nv.write('TEMP:TC:TYPE K')
        self.nv.write('TEMP:TC:RJUN:RSEL SIM') 
        self.nv.write(':TEMP:TC:RJUN:SIM 0')
        
        self.nv.write('SENS:FUNC \'TEMP\'')
        self.nv.write('SENS:TEMP:NPLC 1')# Para cambiar el rate a mano, (0.1 fast, 1 medium, 5 slow) 
        self.nv.write('TEMP:AVER:TCON REP;COUN 10;STAT ON')
        
    def measure(self):
        self.nv.write('FORM:ELEM READ')
        return self.nv.query_ascii_values('READ?')[0] #Return a new (fresh) reading.

    def output(self,on = False):
        if on:
            self.nv.write('INIT:CONT ON')
        else:
            self.nv.write('INIT:CONT OFF')
