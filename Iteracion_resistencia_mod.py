# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 17:27:40 2019

@author: Agustin Lopez Pedroso
 Programa para realizar iteraciones de mediciones de resistencia a campo y 
temperatura fija
"""

import Keithley_6221 as kd
#import Controlador_campo as cc
import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
import time 


res = kd.K6221()
#campo = cc.FieldControl()



params= {'current_mA': 0.1,
         'samples' : 10,
         'number' : 100,
         'time_sleep' : 0.5,
         'save' : False,
         'name' : ''
        }

def resistencia_i(parameters):
    resistencia=[]
    iteracion = []
    res.reset()
    time.sleep(2)
    current = parameters['current_mA']/1000
    res.delta_mode(current)
    win = pg.GraphicsWindow(title="Meidicion R")
    win.resize(700,500)
    win.setWindowTitle('Medicion R vs N de iteracion')
    p1 = win.addPlot(title="R vs N de iteracion")
    p1.setLabel('left', "Resistencia", units='Ohm')
    p1.setLabel('bottom', "N de iteracion")
    p1.setDownsampling(mode='peak')
    p1.setClipToView(True)
    curve1 = p1.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
    
    for i in range(parameters['number']):
        resistencia.append(res.mean_meas(parameters['samples']))
        iteracion.append(i)
        curve1.setData(iteracion,resistencia)
        tiempo_aux_ini = time.time()
        tiempo_aux = tiempo_aux_ini
        while (tiempo_aux - tiempo_aux_ini) < parameters['time_sleep']:
            tiempo_aux = time.time()
    res.stop_meas()
    if parameters['save']:
        f = open("{}".format(parameters['name']),"w")
        f.write("Numero de iteracion,Resistencia(Ohm)\n")
        renglon = len(resistencia)
        for i in range(renglon):
            f.write("{},{}\n".format(iteracion[i],resistencia[i]))
        f.close()
    return iteracion, resistencia

