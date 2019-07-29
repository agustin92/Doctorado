# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 17:55:23 2019

@author: Agustin Lopez Pedroso
"""

import Controlador_campo as cc
import Keithley_6221 as kd
import Controlador_temp as te
import matplotlib.pyplot as plt
import numpy as np
import time 


res = kd.K6221()
#campo = cc.FieldControl()
temp = te.Ls331()


def r_t(current,samples,temperatura_final,rate,heater,tiempo_med=10,save=False,name=''):
    temperatura_a=[]
    temperatura_b=[]
    resistencia=[]
    tiempo=[]
    res.reset()
    time.sleep(2)
    res.delta_mode(current)
    time.sleep(2)
    temp.change_temp(temperatura_final,rate,heater)
    time.sleep(2)
    ti = time.time()
    line1=[]
    line2=[]
    line3=[]
    ax1 = []
    ax2 = []
    ax3 = []
    try:
        while True:
            temperatura_a.append(temp.get_temp()[0])
            time.sleep(0.2)
            temperatura_b.append(temp.get_temp()[1])
            time.sleep(0.2)
            tiempo.append(time.time()-ti)
            resistencia.append(res.mean_meas(samples))
            line1, line2, line3, ax1, ax2, ax3 = live_plotter_xy(temperatura_b,resistencia,tiempo,temperatura_a,tiempo,temperatura_b,line1,line2,line3,ax1,ax2,ax3)

            time.sleep(tiempo_med)
                      
    except KeyboardInterrupt:
        pass
    
    res.stop_meas()
    if save:
        f = open("{}".format(name),"w")
        f.write("Tiempo(s),Temperatura A(K), Temperatura B(K), Resistencia(Ohm)\n")
        renglon = len(resistencia)
        for i in range(renglon):
            f.write("{},{},{},{}\n".format(tiempo[i],temperatura_a[i],temperatura_b[i],resistencia[i]))
        f.close()
    return tiempo,temperatura_a,temperatura_b, resistencia


def live_plotter_xy(x_vec,y1_data,x_vec2,y2_data,x_vec3,y3_data,line1,line2,line3,ax1,ax2,ax3,identifier='',pause_time=0.01):
    if line1==[]:
        plt.ion()
        fig = plt.figure(figsize=(15,5))
        ax1 = fig.add_subplot(131)
        line1, = ax1.plot(x_vec,y1_data,'r-o',alpha=0.8)
#        ax1.plt.ylabel('Resistencia (OHM)')
#        ax1.plt.xlabel('Temeperatura_B (K)')
        ax1.set(xlabel='Temeperatura_B (K)', ylabel='Resistencia (OHM)')
#        ax1.plt.ticklabel_format(useOffset=False)
#        ax1.plt.title('Title: {}'.format(identifier))
        ax2 = fig.add_subplot(132)
        line2, = ax2.plot(x_vec2,y2_data,'r-o',alpha=0.8)
#        ax2.plt.ylabel('Temperatura_A (K)')
#        ax2.plt.xlabel('Tiempo (s)')
        ax2.set(xlabel='Tiempo (s)', ylabel='Temeperatura_A (K)')
#        ax2.plt.ticklabel_format(useOffset=False)
        ax3 = fig.add_subplot(133)
        line3, = ax3.plot(x_vec3,y3_data,'r-o',alpha=0.8)
#        ax3.plt.ylabel('Temperatura_B (K)')
#        ax3.plt.xlabel('Tiempo (s)')
        ax3.set(xlabel='Tiempo (s)', ylabel='Temeperatura_B (K)')
#        ax3.plt.ticklabel_format(useOffset=False)
        plt.title('Title: {}'.format(identifier))
        plt.show()
        
    line1.set_data(x_vec,y1_data)
    ax1.set_xlim(np.min(x_vec)-0.0001,np.max(x_vec)+0.0001)
    ax1.set_ylim(np.min(y1_data)-0.0001,np.max(y1_data)+0.0001)
    line2.set_data(x_vec2,y2_data)
    ax2.set_xlim(np.min(x_vec2)-0.0001,np.max(x_vec2)+0.0001)
    ax2.set_ylim(np.min(y2_data)-0.0001,np.max(y2_data)+0.0001)    
    line3.set_data(x_vec3,y3_data)
    ax3.set_xlim(np.min(x_vec3)-0.0001,np.max(x_vec3)+0.0001)
    ax3.set_ylim(np.min(y3_data)-0.0001,np.max(y3_data)+0.0001) 
#    if np.min(y1_data)<=line1.axes.get_ylim()[0] or np.max(y1_data)>=line1.axes.get_ylim()[1]:
#        plt.ylim([np.min(y1_data)-np.std(y1_data),np.max(y1_data)+np.std(y1_data)])

    plt.pause(pause_time)
    
    return line1, line2, line3, ax1, ax2, ax3
    