# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 11:49:04 2019

@author: Agustin Lopez Pedroso
Programa para realizar R(T) con el multimetro Keithley
"""

#import Controlador_campo as cc
import Controlador_multimetro as kd
import Controlador_temp as te
#import matplotlib.pyplot as plt
import numpy as np
import time 
#from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg


mul = kd.K2010()
#campo = cc.FieldControl()
temp = te.Ls331()

# Parametros iniciales para la medición
# Descripcion
# Modo = 2wires o 4wires, por default toma 2wires
# samples = cantidad de mediciones para promediar
# temperatura_final = Temperatura final de la medicion
# rate = K/min tipicamente 2
# heater = 0 Apagado, 1 Low, 2 Med, 3 High
# tiempo_med = tiempo de espera entre mediciones (segundos)
# save = True para guardar los datos False no guarda ningun archivo
# name = path del directorio para guardar, usar // para la ruta del archivo

param = {'modo' : '4wire',
         'samples' : 10  ,
         'temperatura_final' : 20,
         'rate' : 2 ,
         'heater' : 3 , 
         'tiempo_med' : 10 ,
         'save' : False ,
         'name' : ''
        }

#def r_t(parameters,modo,samples,temperatura_final,rate,heater,tiempo_med=10,save=False,name=''):    
def r_t(parameters):
    
    #Inicializo las listas 
    temperatura_a=[]
    temperatura_b=[]
    resistencia=[]
    tiempo=[]
    # Reset del equipo
    mul.reset()
    # Configuro el modo de medicion
    if parameters['modo'] == '4wire':
        mul.mode_4wire()
    else:
        mul.mode_2wire()
    # Setup del multimetro
    mul.continuous_mode(on=True)
    time.sleep(2)
    # Setup del controlador de temperatura
    temp.change_temp(parameters['temperatura_final'],parameters['rate'],parameters['heater'])
    time.sleep(2)
    ti = time.time()
    
    # Parametros para graficar la salida
    win = pg.GraphicsWindow(title="Meidicion R(T)")
    win.resize(1300,500)
    win.setWindowTitle('Medicion R(T)')
    p1 = win.addPlot(title="Resistencia vs Temperatura")
    p1.setLabel('left', "Resistencia", units='Ohm')
    p1.setLabel('bottom', "Temperatura B", units='K')
    p2 = win.addPlot(title="Temperatura A vs Tiempo")
    p2.setLabel('left', "Temperatura A", units='K')
    p2.setLabel('bottom', "Tiempo", units='s')
    p3 = win.addPlot(title="Temperatura B vs Tiempo")
    p3.setLabel('left', "Temperatura B", units='K')
    p3.setLabel('bottom', "Tiempo", units='s')
    p1.setDownsampling(mode='peak')
    p2.setDownsampling(mode='peak')
    p3.setDownsampling(mode='peak')
    p1.setClipToView(True)
    p2.setClipToView(True)
    p3.setClipToView(True)
    curve1 = p1.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
    curve2 = p2.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
    curve3 = p3.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
    # Si quiero guardar, creo el archivo
    if parameters['save']:
        f = open("{}".format(parameters['name']),"a+")
        f.write("Tiempo(s),Temperatura A(K), Temperatura B(K), Resistencia(Ohm)\n")    
    #Loop de medicion, mide indefinidamente hasta cortar con CRL + C        
    try:
        while True:
            temp_aux_a = temp.get_temp()[0]
            temperatura_a.append(temp_aux_a)
#            time.sleep(0.2)
            temp_aux_b = temp.get_temp()[1]
            temperatura_b.append(temp_aux_b)
#            time.sleep(0.2)
            time_aux = time.time()-ti
            tiempo.append(time_aux)
            res_aux = mul.mean_meas(parameters['samples'])
            resistencia.append(res_aux)
            
            if parameters['save']:
                f.write("{},{},{},{}\n".format(time_aux,temp_aux_a,temp_aux_b,res_aux))
                
            curve1.setData(temperatura_b,resistencia)
            curve2.setData(tiempo,temperatura_a)
            curve3.setData(tiempo,temperatura_b)
            
            time_med_aux_ini = time.time()
            time_med_aux =  time_med_aux_ini
            
            while (time_med_aux-time_med_aux_ini) < parameters['tiempo_med']:
                time_med_aux = time.time()
#            time.sleep(parameters['tiempo_med'])
                      
    except KeyboardInterrupt:
        pass
    
    if parameters['save']:
        f.close()
        
    mul.continuous_mode()

    return tiempo,temperatura_a,temperatura_b, resistencia



    