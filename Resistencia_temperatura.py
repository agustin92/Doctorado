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


def r_t(current,samples,temperatura_final,rate,heater,save=False,name=''):
    temperatura_a=[]
    temperatura_b=[]
    resistencia=[]
    tiempo=[]
    res.reset()
    res.delta_mode(current)
    temp.change_temp(temperatura_final,rate,heater)
    ti = time.time()
    try:
        while True:
            temperatura_a.append(temp.get_temp()[0])
            time.sleep(0.2)
            temperatura_b.append(temp.get_temp()[1])
            time.sleep(0.2)
            tiempo.append(time.time()-ti)
            resistencia.append(res.mean_meas(samples))
            time.sleep(10)

            
    except KeyboardInterrupt:
        pass
def live_plotter_xy(x_vec,y1_data,line1,identifier='',pause_time=0.01):
    if line1==[]:
        plt.ion()
        fig = plt.figure(figsize=(8,4))
        ax = fig.add_subplot(111)
        line1, = ax.plot(x_vec,y1_data,'r-o',alpha=0.8)
        plt.ylabel('Resistencia (OHM)')
        plt.xlabel('Numero de iteracion')
        plt.title('Title: {}'.format(identifier))
        plt.show()
        
    line1.set_data(x_vec,y1_data)
    plt.xlim(np.min(x_vec)-0.0001,np.max(x_vec)+0.0001)
    plt.ylim(np.min(y1_data)-0.0001,np.max(y1_data)+0.0001)
#    if np.min(y1_data)<=line1.axes.get_ylim()[0] or np.max(y1_data)>=line1.axes.get_ylim()[1]:
#        plt.ylim([np.min(y1_data)-np.std(y1_data),np.max(y1_data)+np.std(y1_data)])

    plt.pause(pause_time)
    
    return line1
    