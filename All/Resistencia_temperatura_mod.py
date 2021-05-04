# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 17:55:23 2019

@author: Agustin Lopez Pedroso
"""

import Controlador_campo as cc
import Keithley_6221 as kd
import Controlador_temp as te
import matplotlib.pyplot as plt
import pyqtgraph as pg
import numpy as np
import time 


res = kd.K6221()
#campo = cc.FieldControl()
temp = te.Ls331()

params= {'current_mA' : 0.1,
         'samples' : 10,
         'temperatura_final' : 15,
         'rate' : 2,
         'heater' : 0,
         'tiempo_med' : 20,
         'save' : False,
         'name' : ''
        }

def r_t(parameters):
    temperatura_a=[]
    temperatura_b=[]
    resistencia=[]
    tiempo=[]
    res.reset()
    
    time_med_aux_ini = time.time()
    time_med_aux =  time_med_aux_ini
    while (time_med_aux-time_med_aux_ini) < 2.0:
        time_med_aux = time.time()
        
    current = parameters['current_mA'/1000]
    res.delta_mode(current)
    
    time_med_aux_ini = time.time()
    time_med_aux =  time_med_aux_ini
    while (time_med_aux-time_med_aux_ini) < 2.0:
        time_med_aux = time.time()
        
    temp.change_temp(parameters['temperatura_final'],
                     parameters['rate'],parameters['heater'])

    time_med_aux_ini = time.time()
    time_med_aux =  time_med_aux_ini
    while (time_med_aux-time_med_aux_ini) < 2.0:
        time_med_aux = time.time()
        
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
            res_aux = res.mean_meas(parameters['samples'])
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
                      
    except KeyboardInterrupt:
        pass
    
    res.stop_meas()
    
    if parameters['save']:
        f.close()
    
    return tiempo,temperatura_a,temperatura_b, resistencia


    