# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 17:27:40 2019

@author: Agustin Lopez Pedroso
"""

import Keithley_6221 as kd
import Controlador_campo as cc
#import statistics as st
import matplotlib.pyplot as plt
import numpy as np
import time 


# use ggplot style for more sophisticated visuals
plt.style.use('ggplot')



res = kd.K6221()
campo = cc.FieldControl()




def resistencia_i(current_mA,samples,number,time_sleep=0.5,save= False,name=''):
    resistencia=[]
    iteracion = []
    line1= []
    res.reset()
    time.sleep(2)
    current = current_mA/1000
    res.delta_mode(current)
    for i in range(number):
        resistencia.append(res.mean_meas(samples))
        iteracion.append(i)
        line1 = live_plotter_xy(iteracion,resistencia,line1)
#        print(contador)
        time.sleep(time_sleep)
    res.stop_meas()
    if save:
        f = open("{}".format(name),"w")
        f.write("Numero de iteracion,Resistencia(Ohm)\n")
        renglon = len(resistencia)
        for i in range(renglon):
            f.write("{},{}\n".format(iteracion[i],resistencia[i]))
        f.close()
    return iteracion, resistencia

def live_plotter_xy(x_vec,y1_data,line1,identifier='',pause_time=0.01):
#    lim = 2
#    x_vec = x_vec[lim:]
#    y1_data = y1_data[lim:]
    if line1==[]:
        plt.ion()
        fig = plt.figure(figsize=(8,4))
        ax = fig.add_subplot(111)
        line1, = ax.plot(x_vec,y1_data,'r-o',alpha=0.8)
        plt.ylabel('Resistencia (OHM)')
        plt.xlabel('Numero de iteracion')
        plt.title('Title: {}'.format(identifier))
        plt.ticklabel_format(useOffset=False)
        plt.show()
        
    line1.set_data(x_vec,y1_data)
    plt.xlim(np.min(x_vec)-0.0001,np.max(x_vec)+0.0001)
    plt.ylim(np.min(y1_data)-0.0001,np.max(y1_data)+0.0001)
#    if np.min(y1_data)<=line1.axes.get_ylim()[0] or np.max(y1_data)>=line1.axes.get_ylim()[1]:
#        plt.ylim([np.min(y1_data)-np.std(y1_data),np.max(y1_data)+np.std(y1_data)])

    plt.pause(pause_time)
    
    return line1