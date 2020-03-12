# -*- coding: utf-8 -*-
"""
Created on Mon May  6 15:20:11 2019

@author: Agustin Lopez Pedroso

Control del controlador de Temperatura
"""

import visa
import numpy as np
import time
import matplotlib.pyplot as plt

rm = visa.ResourceManager()

#LS331 = rm.open_resource('GPIB0::12::INSTR')
#print(LS331.query('*IDN?'))
#LS331.write('*RST')

class Ls331():
    def __init__(self):
        #Inicializo el instrumento
        self.contemp = rm.open_resource('GPIB0::12::INSTR')
#        self.contemp.write('*RST')
    
    def idn(self):
        #Identificación del instrumento
        print(self.contemp.query('*IDN?'))
        
        
    def get_setpoint(self):
        #Pregunta el setpoint del instrumento
        print(self.contemp.query('SETP?'))
        return self.contemp.query('SETP?')
    
    def setpoint(self,temp,loop = 1):
        # Fija el setpoint en K. Por default usa el loop=1 que permite usar la 
        #resistencia de alta potencia
        self.contemp.write('SETP {}, {}'.format(str(loop),str(temp)))
        print ('Successful change. New setpoint {}'.format(str(temp)))

    def set_ramp(self,rate,out=0,loop=1):
        # Fija el rate de la rampa en K/m y la habilita o deshabilita.
        # Por default esta deshabilitada.
        # out = 0 Off
        # out = 1 On
        self.contemp.write('RAMP {}, {}, {}'.format(str(loop),str(out),str(rate)))
        print ('Successful change. New rate {}'.format(str(rate)))
    
    def set_range(self,heater=0):
        # Fija la resistencia a utilizar.
        # heater = 0 Off
        # heater = 1 LOW
        # heater = 2 MED
        # heater = 3 HIGH
        self.contemp.write('RANGE {}'.format(str(heater)))
        heater_state = ''
        if heater == 0:
            heater_state = 'OFF'
        elif heater == 1:
            heater_state = 'LOW'
        elif heater == 2:
            heater_state = 'MED'
        elif heater == 3:
            heater_state = 'HIGH' 
        print ('Successful change. Heater state {}'.format(heater_state))
    
    def set_control_loop(self,loop=1,inp='a',unit=1,pwup=0, cpwr=1):
        # Fija con que temómetro se fija la temperatura.
        # Por default en este equipo se controla con el termómetro A.
        self.contemp.write('CSET {}, {}, {}, {}'.format(str(loop),inp,str(unit),str(pwup),str(cpwr)))

    def change_temp(self,temp,rate,heat):
        # Cambio el setpoint y el rate para iniciar una rampa de temperatura.
        self.set_ramp(1)
#        time.sleep(0.1)
        temp_ini = []
        temp_ini = self.get_temp()
#        time.sleep(0.1)
        self.setpoint(temp_ini[0])
        time.sleep(1.0)
        self.set_ramp(rate, out=1)
        time.sleep(1.0)
        self.setpoint(temp)
#        time.sleep(0.1)
        self.set_range(heat)
        
        
    def get_temp(self):
        # Mide la temperatura en ambos termómetros
        
        temp_a = self.contemp.query('KRDG? A')
        len_a = len(temp_a)
        start = 0
        end = len_a
        for i in range(len_a):
            if temp_a[i] == '+':
                start = i
        for i in range(len_a):
            if temp_a[i] == "\r" :
                end = i
        temp_a = float(temp_a[start+1:end])
                
            
#        time.sleep(0.5)
        temp_b = self.contemp.query('KRDG? B')
        len_b = len(temp_b)
        start = 0
        end = len_a
        for i in range(len_b):
            if temp_b[i] == '+':
                start = i
        for i in range(len_b):
            if temp_b[i] == "\r" :
                end = i
        temp_b = float(temp_b[start+1:end])
        return temp_a, temp_b
    
    def get_heater(self):
        return int(self.contemp.query('HTR?'))
#        print(self.contemp.query('HTR?'))
    
def graficar_temp(temp):
    a=[]
    b=[]
    c=[]
    plt.plot(b,a,'-r')
    plt.show()
    time.sleep(10)
    ti = time.time()
    try:
        while True:
            time.sleep(2)
            a.append(temp.get_temp()[0])
            time.sleep(0.2)
            c.append(temp.get_temp()[1])
            b.append(time.time()-ti)
            plt.plot(b,a,'-r')
            plt.plot(b,c,'-b')
            plt.pause(0.05)
            
            
    except KeyboardInterrupt:
        pass
    return a,b
        
    
         