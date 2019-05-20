# -*- coding: utf-8 -*-
"""
Created on Fri May 17 10:25:39 2019

@author: Admin
"""
import PyDAQmx
from PyDAQmx import Task
import numpy as np
import time
#value = 0
#
#task = Task()
#task.CreateAOVoltageChan("Dev1/ao0","",-10.0,10.0,PyDAQmx.DAQmx_Val_Volts,None)
#task.StartTask()
#task.WriteAnalogScalarF64(1,10.0,value,None)
#task.StopTask()


class FieldControl():
    # Librerías necesarias: PyDAQmx, numpy y time
    def __init__(self):
        # Inicilizo la comunicación con la placa DAQ, específicamente con el canal
        #de output para controlar la corriente del electroimán
        self.task = Task()
        self.task.CreateAOVoltageChan("Dev1/ao0","",-10.0,10.0,PyDAQmx.DAQmx_Val_Volts,None)
    
    def set_voltage(self,voltage):
        # Inicio un task para establecer el valor de voltaje de salida en volts
        self.task.StartTask()
        self.task.WriteAnalogScalarF64(1,10.0,voltage,None)
        self.task.StopTask()
    
    def set_volatge_steps(self,vf,vi,step=0.1):
        # Cambia el voltaje en pasos pequeños, es necesario poner el valor de voltaje
        #deseado vf y el voltaje inicial vi(mejorar para que lo tome solo)
        vaux = vi
        if vf > vi:
            while vaux < vf:
                self.task.StartTask()
                self.task.WriteAnalogScalarF64(1,10.0,vaux,None)
                self.task.StopTask()
                vaux = vaux + step
                time.sleep(2)
        else:
            while vaux > vf:
                self.task.StartTask()
                self.task.WriteAnalogScalarF64(1,10.0,vaux,None)
                self.task.StopTask()
                vaux = vaux - step
                time.sleep(2)
        self.task.StartTask()
        self.task.WriteAnalogScalarF64(1,10.0,vf,None)
        self.task.StopTask()
        print('Succes')
        
        