# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 11:49:04 2019

@author: Admin
"""

import Controlador_campo as cc
import Controlador_multimetro as kd
import Controlador_temp as te
import matplotlib.pyplot as plt
import numpy as np
import time 


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
    line1=[]
    line2=[]
    line3=[]
    ax1 = []
    ax2 = []
    ax3 = []
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
            line1, line2, line3, ax1, ax2, ax3 = live_plotter_xy(temperatura_b,resistencia,tiempo,temperatura_a,tiempo,temperatura_b,line1,line2,line3,ax1,ax2,ax3)

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
    