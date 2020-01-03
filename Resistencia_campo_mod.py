# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 11:02:48 2019

@author: Agustin Lopez Pedroso

Programa para medir R(H) Usando el modo delta de la fuente de corriente
"""

import Controlador_campo as cc
import Keithley_6221 as kd
import pyqtgraph as pg
import matplotlib.pyplot as plt
import numpy as np
import time 


res = kd.K6221()
campo = cc.FieldControl()

#current = 0   #Definir la corriente en A
#campo_max = 2 #Definir campo maximo
#campo_min = -2 #Definir campo minimo


def change_field_r_plt(vinicial,vfinal,samples,step,curve,
                       resistencia_prev,campo_prev,voltaje_prev,
                       calibration, Slope=0,Intercept=0,):
    vaux = vinicial
    if vinicial < vfinal:
        while vaux <= vfinal:
            campo.set_voltage_steps(vaux)
            tiempo_aux_ini = time.time()
            tiempo_aux = tiempo_aux_ini
            while (tiempo_aux - tiempo_aux_ini) < 2:
                tiempo_aux = time.time()              
            resistencia_prev.append(res.mean_meas(samples))
            voltaje_prev.append(vaux)
            if calibration:
                campo_prev.append(vaux*Slope+Intercept)
                curve.setData(campo_prev,resistencia_prev)
            else:
                curve.setData(voltaje_prev,resistencia_prev)
            vaux += step
        campo.set_voltage(vfinal)
        tiempo_aux_ini = time.time()
        tiempo_aux = tiempo_aux_ini
        while (tiempo_aux - tiempo_aux_ini) < 2:
            tiempo_aux = time.time()
        resistencia_prev.append(res.mean_meas(samples))
        voltaje_prev.append(vfinal)
        if calibration:
            campo_prev.append(vfinal*Slope+Intercept)
            curve.setData(campo_prev,resistencia_prev)
        else:
            curve.setData(voltaje_prev,resistencia_prev)
    
    else:
        while vaux >= vfinal:
            campo.set_voltage_steps(vaux)
            tiempo_aux_ini = time.time()
            tiempo_aux = tiempo_aux_ini
            while (tiempo_aux - tiempo_aux_ini) < 2:
                tiempo_aux = time.time()
            resistencia_prev.append(res.mean_meas(samples))
            voltaje_prev.append(vaux)
            if calibration:
                campo_prev.append(vaux*Slope+Intercept)
                curve.setData(campo_prev,resistencia_prev)
            else:
                curve.setData(voltaje_prev,resistencia_prev)
            vaux -= step
        campo.set_voltage(vfinal)
        tiempo_aux_ini = time.time()
        tiempo_aux = tiempo_aux_ini
        while (tiempo_aux - tiempo_aux_ini) < 2:
            tiempo_aux = time.time()
        resistencia_prev.append(res.mean_meas(samples))
        voltaje_prev.append(vfinal)
        if calibration:
            campo_prev.append(vfinal*Slope+Intercept)
            curve.setData(campo_prev,resistencia_prev)
        else:
            curve.setData(voltaje_prev,resistencia_prev)

    return resistencia_prev, voltaje_prev, campo_prev

# Descripción de los parámetros
# current = corriente de medición en mA
# samples = Numero de mediciones para promediar
# cmax = Voltaje máximo (Campo máximo)
# cmin = Voltaje mínimo (Campo minimo)
# step = numero de pasos desde 0 hasta el valor máximo o mínimo
# calibration = True si hay curva de calibración para reportar el valor del campo
# slope = Pendiente del ajuste del campo
# intercept = Ordenada al origen del ajuste
# save = True para guardar los resultados
# name = Path del archivo para guardar los resultados    

param = {'current_mA': 0.0001,
         'samples': 10,
         'cmax' : 4.0,
         'cmin' : -4.0,
         'step' : 0.5,
         'calibration': False,
         'slope' : 0,
         'intercept' : 0,
         'save' : False,
         'name' : ''
        }

def r_h(parameters):
    # Este programa toma los valores de un diccionario, realiza desde 0 hasta cmax
    # desde ahí va a cmax hasta cmin y termina en 0.
    resistencia = []
    voltaje=[]
    field=[]
    res.reset()
    tiempo_aux_ini = time.time()
    tiempo_aux = tiempo_aux_ini
    while (tiempo_aux - tiempo_aux_ini) < 2:
        tiempo_aux = time.time()
    res.delta_mode(parameters['current']/1000)
    win = pg.GraphicsWindow(title="Meidicion R(H)")
    win.resize(700,500)
    win.setWindowTitle('Medicion R(H)')
    
    if parameters['calibration']:
        p1 = win.addPlot(title="Resistencia vs Campo")
        p1.setLabel('left', "Resistencia", units='Ohm')
        p1.setLabel('bottom', "Campo", units='Oe')
    else:
        p1 = win.addPlot(title="Campo vs Resistencia")
        p1.setLabel('left', "Voltaje", units='V')
        p1.setLabel('bottom', "Campo", units='Oe')

    p1.setDownsampling(mode='peak')
    p1.setClipToView(True)
    curve1 = p1.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
    try:
        aux =change_field_r_plt(0.0,parameters['cmax'],parameters['samples'],
                                parameters['step'],curve1,resistencia,field,
                                voltaje,parameters['calibration'],
                                parameters['slope'], parameters['intercept'])
        aux =change_field_r_plt(parameters['cmax'],parameters['cmin'],
                                parameters['samples'],parameters['step'],
                                curve1, aux[0], aux[2], aux[1],
                                parameters['calibration'],parameters['slope'],
                                parameters['intercept'])
        aux =change_field_r_plt(parameters['cmin'],0.0,parameters['samples'],
                                parameters['step'],curve1,aux[0],aux[2],aux[1],
                                parameters['calibration'],parameters['slope'],
                                parameters['intercept'])
        resistencia=aux[0]
        voltaje = aux[1]
        if parameters['calibration']:
            field = aux[2]
        
    except KeyboardInterrupt:
        pass
    res.stop_meas()
    
    if parameters['save']:
        f = open("{}".format(parameters['name']),"w")
        if parameters['calibration']:
            f.write("Campo(G),Resistencia(Ohm)\n")
            renglon = len(resistencia)
            for i in range(renglon):
                f.write("{},{}\n".format(field[i],resistencia[i]))
        else:
            f.write("Voltaje(V),Resistencia(Ohm)\n")
            renglon = len(resistencia)
            for i in range(renglon):
                f.write("{},{}\n".format(voltaje[i],resistencia[i]))
        f.close()
    return resistencia, voltaje, field
    
        
        
    
