# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 11:02:48 2019

@author: Agustin Lopez Pedroso

Programa para medir R(H)
"""

import Controlador_campo as cc
import Keithley_6221 as kd
#import statistics as st
import matplotlib.pyplot as plt
import numpy as np
import time 


# use ggplot style for more sophisticated visuals
plt.style.use('ggplot')



res = kd.K6221()
campo = cc.FieldControl()

#current = 0   #Definir la corriente en A
#campo_max = 2 #Definir campo maximo
#campo_min = -2 #Definir campo minimo

def change_field_r(vinicial,vfinal,samples,step):
    vaux = vinicial
    resistencia_interna = []
    if vinicial < vfinal:
        while vaux < vfinal:
            campo.set_voltage(vaux)
            time.sleep(2)
            resistencia_interna.append(res.mean_meas(samples))
            vaux = vaux + step
            
            print(res.mean_meas(samples))
        campo.set_voltage(vfinal)
        time.sleep(2)
        resistencia_interna.append(res.mean_meas(samples))
    
    else:
        while vaux > vfinal:
            campo.set_voltage(vaux)
            time.sleep(2)
            resistencia_interna.append(res.mean_meas(samples))
            vaux = vaux - step
            print(res.mean_meas(samples))
        campo.set_voltage(vfinal)
        time.sleep(2)
        resistencia_interna.append(res.mean_meas(samples))
    return resistencia_interna    

def change_field_r_plt(vinicial,vfinal,samples,step,line1,resistencia_prev,
                       campo_prev,voltaje_prev,calibration, Slope=0,Intercept=0,):
    vaux = vinicial
    if vinicial < vfinal:
        while vaux <= vfinal:
            campo.set_voltage_steps(vaux)
            time.sleep(2)
            resistencia_prev.append(res.mean_meas(samples))
            voltaje_prev.append(vaux)
            if calibration:
                campo_prev.append(vaux*Slope+Intercept)
                line1 = live_plotter_xy(campo_prev,resistencia_prev,line1,calibration)
            else:
                line1 = live_plotter_xy(voltaje_prev,resistencia_prev,line1,calibration)
            vaux = vaux + step
#            print(res.mean_meas(samples))
        campo.set_voltage(vfinal)
        time.sleep(2)
        resistencia_prev.append(res.mean_meas(samples))
        voltaje_prev.append(vfinal)
        if calibration:
            campo_prev.append(vfinal*Slope+Intercept)
            line1 = live_plotter_xy(campo_prev,resistencia_prev,line1,calibration)
        else:
            line1 = live_plotter_xy(voltaje_prev,resistencia_prev,line1,calibration)
    
    else:
        while vaux >= vfinal:
            campo.set_voltage_steps(vaux)
            time.sleep(2)
            resistencia_prev.append(res.mean_meas(samples))
            voltaje_prev.append(vaux)
            if calibration:
                campo_prev.append(vaux*Slope+Intercept)
                line1 = live_plotter_xy(campo_prev,resistencia_prev,line1,calibration)
            else:
                line1 = live_plotter_xy(voltaje_prev,resistencia_prev,line1,calibration)
            vaux = vaux - step
#            print(res.mean_meas(samples))
        campo.set_voltage(vfinal)
        time.sleep(2)
        resistencia_prev.append(res.mean_meas(samples))
        voltaje_prev.append(vfinal)
        if calibration:
            campo_prev.append(vfinal*Slope+Intercept)
            line1 = live_plotter_xy(campo_prev,resistencia_prev,line1,calibration)
        else:
            line1 = live_plotter_xy(voltaje_prev,resistencia_prev,line1,calibration)

    return resistencia_prev, voltaje_prev, line1, campo_prev


def r_h(current,samples,cmax,cmin,step,calibration= False,slope = 0,intercept=0,save = False,name = ''):
#    campo.set_voltage_steps(-1)
#    campo.set_voltage_steps(0)
    resistencia = []
    voltaje=[]
    line1_aux=[]
    field=[]
    res.reset()
    time.sleep(2)
    res.delta_mode(current)
    try:
        aux =change_field_r_plt(0,cmax,samples,step,line1_aux,resistencia,field,voltaje,calibration,slope,intercept)
    #    resistencia.extend(aux[0])
    #    voltaje.extend(aux[1])
    #    line1_aux =aux[2]
    #    if calibration:
    #        field.extend(aux[3])
        aux =change_field_r_plt(cmax,cmin,samples,step,aux[2],aux[0],aux[3],aux[1],calibration,slope,intercept)
    #    resistencia.extend(aux[0])
    #    voltaje.extend(aux[1])
    #    line1_aux = aux[2]
    #    if calibration:
    #        field.extend(aux[3])
        aux =change_field_r_plt(cmin,0,samples,step,aux[2],aux[0],aux[3],aux[1],calibration,slope,intercept)
        resistencia=aux[0]
        voltaje = aux[1]
        if calibration:
            field = aux[3]
        
    except KeyboardInterrupt:
        pass
    res.stop_meas()
    if save:
        f = open("{}".format(name),"w")
        if calibration:
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
    
        
        
def live_plotter_xy(x_vec,y1_data,line1,calibration,identifier='',pause_time=0.01):
    if line1==[]:
        plt.ion()
        fig = plt.figure(figsize=(8,4))
        ax = fig.add_subplot(111)
        line1, = ax.plot(x_vec,y1_data,'r-o',alpha=0.8)
        if calibration:
            plt.ylabel('Resistencia (OHM)')
            plt.xlabel('Campo(G)')
        else:
            plt.ylabel('Resistencia (OHM)')
            plt.xlabel('Voltaje(V)')
        plt.title('Title: {}'.format(identifier))
        plt.ticklabel_format(useOffset=False)
        plt.show()
        
    line1.set_data(x_vec,y1_data)
    plt.xlim(np.min(x_vec)-0.001,np.max(x_vec)+0.001)
    plt.ylim(np.min(y1_data)-0.001,np.max(y1_data)+0.001)
#    if np.min(y1_data)<=line1.axes.get_ylim()[0] or np.max(y1_data)>=line1.axes.get_ylim()[1]:
#        plt.ylim([np.min(y1_data)-np.std(y1_data),np.max(y1_data)+np.std(y1_data)])

    plt.pause(pause_time)
    
    return line1
    
