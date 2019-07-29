# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 11:49:04 2019

@author: Agustin Lopez Pedroso
"""

#import Controlador_campo as cc
import Controlador_multimetro as kd
import Controlador_temp as te
#import matplotlib.pyplot as plt
import numpy as np
import time 
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg


mul = kd.K2010()
#campo = cc.FieldControl()
temp = te.Ls331()


def r_t(modo,samples,temperatura_final,rate,heater,tiempo_med=10,save=False,name=''):
    temperatura_a=[]
    temperatura_b=[]
    resistencia=[]
    tiempo=[]
    mul.reset()
    if modo == '4wire':
        mul.mode_4wire()
    else:
        mul.mode_2wire()
    mul.continuous_mode(on=True)
    time.sleep(2)
    time.sleep(2)
    temp.change_temp(temperatura_final,rate,heater)
    time.sleep(2)
    ti = time.time()
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

    if save:
        f = open("{}".format(name),"a+")
        f.write("Tiempo(s),Temperatura A(K), Temperatura B(K), Resistencia(Ohm)\n")    
        f.close()
    try:
        while True:
            temp_aux_a = temp.get_temp()[0]
            temperatura_a.append(temp_aux_a)
            time.sleep(0.2)
            temp_aux_b = temp.get_temp()[1]
            temperatura_b.append(temp_aux_b)
            time.sleep(0.2)
            time_aux = time.time()-ti
            tiempo.append(time_aux)
            res_aux = mul.mean_meas(samples)
            resistencia.append(res_aux)
            if save:
                f = open("{}".format(name),"a+")
                f.write("{},{},{},{}\n".format(time_aux,temp_aux_a,temp_aux_b,res_aux))
                f.close()
            
            p1.plot(temperatura_b,resistencia,pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
            time.sleep(0.1)
            pg.QtGui.QApplication.processEvents()
            p2.plot(tiempo,temperatura_a,pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
            time.sleep(0.1)
            pg.QtGui.QApplication.processEvents()
            p3.plot(tiempo,temperatura_b,pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
            time.sleep(0.1)
            pg.QtGui.QApplication.processEvents()
            time.sleep(tiempo_med)
                      
    except KeyboardInterrupt:
        pass
    
    mul.continuous_mode()
#    if save:
#        f = open("{}".format(name),"a+")
#        f.write("Tiempo(s),Temperatura A(K), Temperatura B(K), Resistencia(Ohm)\n")
#        renglon = len(resistencia)
#        for i in range(renglon):
#            f.write("{},{},{},{}\n".format(tiempo[i],temperatura_a[i],temperatura_b[i],resistencia[i]))
#        f.close()
    return tiempo,temperatura_a,temperatura_b, resistencia



    