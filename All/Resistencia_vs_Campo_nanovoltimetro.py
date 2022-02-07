# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 15:01:02 2020

@author: Agustin Lopez Pedroso
agustin.lopezpedroso@gmail.com

Para funcionar deben estar conectados y encendidos el amplificador de corriente, 
fuente de corriente y nanovoltimetro
"""

from PyQt5 import QtWidgets, Qt, QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np
import time 
import Controlador_campo as cc
import Keithley_6221 as kd
import Keithley_2182 as nv

import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
 
from Resistencia_vs_Campo_GUI import Ui_MainWindow
 
import sys
 
###
#Pendientes
###

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        No data    
  
    result
        `object` data returned from processing, anything

    '''
    finished = pyqtSignal()
    max_field = pyqtSignal()
    result = pyqtSignal(object)
    zero_field = pyqtSignal()
    
class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
    '''

    def __init__(self, parameters):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        # Toma los parámetros definidos previamente en la interfaz gráfica
        # Inicia la comunicacion con los instrumentos
        self.parameters = parameters
        self.signals = WorkerSignals()
        self.results_inst = [0.0,0.0,0.0]
        self.running = True
        self.res = kd.K6221()
        self.nano = nv.K2182()
        self.field = cc.FieldControl()

        # 
    
    def measure(self):
        '''
        Mido la resistencia varias veces y promedio el resultado.
        '''
        resistance = self.nano.mean_meas(self.parameters['samples'])/float(self.parameters['current_mA']/1000)
        return resistance
    
    def stop(self):
        '''
        Cambia el flag de self.running para parar la medicion y el thread.
        '''
        self.running = False         
    
    @pyqtSlot()
    def run(self):
        '''
        results_inst[0] = Voltage
        results_inst[1] = Resistencia
        
        Antes de medir hace un reset del equipo (ver controlador Keithley_6221)
        
        '''
        
        self.res.reset_soft()
        self.nano.reset()
        time.sleep(2)
        self.res.current_mode(self.parameters['current_mA']/1000)
        self.nano.mode()
        time.sleep(2)
        self.res.output(on=True)
        self.nano.output(on=True)
        
        
        cmax = self.parameters['cmax']
        cmin = self.parameters['cmin']
        step = self.parameters['step']
        
        self.running = True
        
        caux = 0
        
        while caux < cmax and self.running:
            self.field.set_voltage(caux)
            self.results_inst[0] = caux
            self.results_inst[1] = self.measure()
            self.signals.result.emit(self.results_inst)
            caux += step
            self.field.set_voltage_steps(caux)
            time.sleep(0.5)
        
        if self.running:
            caux = cmax
            self.field.set_voltage(caux)
            self.results_inst[0] = caux
            self.results_inst[1] = self.measure()
            self.signals.result.emit(self.results_inst)
            self.field.set_voltage_steps(caux)
            self.signals.max_field.emit()
            time.sleep(0.5)
        
        
        while caux > cmin and self.running:
            self.field.set_voltage(caux)
            self.results_inst[0] = caux
            self.results_inst[1] = self.measure()
            self.signals.result.emit(self.results_inst)
            caux += -step
            self.field.set_voltage_steps(caux)
            time.sleep(0.5)        
            
        if self.running:
            caux = cmin
            self.field.set_voltage(caux)
            self.results_inst[0] = caux
            self.results_inst[1] = self.measure()
            self.signals.result.emit(self.results_inst)
            self.field.set_voltage_steps(caux)
            self.signals.max_field.emit()
            time.sleep(0.5)
            
        while caux < cmax and self.running:
            self.field.set_voltage(caux)
            self.results_inst[0] = caux
            self.results_inst[1] = self.measure()
            self.signals.result.emit(self.results_inst)
            caux += step
            self.field.set_voltage_steps(caux)
            time.sleep(0.5)
         
        if self.running:  
            self.signals.finished.emit()
            self.res.output()
            self.nano.output()
            self.field.set_voltage_steps(0)
            self.signals.zero_field.emit()
              # Done
            
        if not self.running:
            self.res.output()
            self.nano.output()
            self.field.set_voltage_steps(0)        
            self.signals.zero_field.emit()


class mywindow(QtWidgets.QMainWindow):
 
    def __init__(self):
 
        super(mywindow, self).__init__()
        '''
        Setup inicial para configurar los aspectos relevantes de la GUI
        '''
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)       
        # Corroboro el estado de la calibracion 
        self.ui.checkBox.stateChanged.connect(self.calibration_check)
        self.calibration = False
        # Corroboro si es necesario guardar la medicion
        self.ui.checkBox_2.stateChanged.connect(self.save_check)
        self.save = False       
        # Corroboro si es necesario hacer un ciclo de pre-magnetizacion
        self.ui.checkBox_3.stateChanged.connect(self.from_zero)
        self.from_zero_field = False       
        # Configuro los parametros del grafico
        self.curve = self.ui.graphWidget.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
        self.ui.graphWidget.setLabel('left', "Resistencia", units='Ohm')
        self.ui.graphWidget.setLabel('bottom', "Voltaje", units='V')     
        # Inicia la medicion al apretar el boton start
        self.ui.pushButton.pressed.connect(self.start)
        # Estado de la medicion, por default es False
        self.running_state = False
        # Pausa la medicion al apretar el boton stop
        self.ui.pushButton_2.pressed.connect(self.user_stop)
        self.ui.pushButton_2.setEnabled(False)
        # Abre la ventana para seleccionar el path del archivo a guardar
        self.ui.pushButton_3.clicked.connect(self.open_dialog_box)
        self.path = ''
        
        self.show()
        # Ininicia el threadpool para poder realizar las tareas en difrentes threads
        self.threadpool = QThreadPool()
        self._translate = QtCore.QCoreApplication.translate
        
    def open_dialog_box(self):
        '''
        Guarda el path a la carpeta donde se guardará la medicion
        '''
        file = ''
        file = QFileDialog.getExistingDirectory()
        self.path = file
    
    def calibration_check(self,status):
        '''
        Corrobora el marcador de calibracion
        '''
        if status == QtCore.Qt.Checked:
            self.calibration = True
            self.ui.graphWidget.setLabel('bottom', "Campo", units='Gauss')
        else: 
            self.calibration = False
            self.ui.graphWidget.setLabel('bottom', "Voltaje", units='V')
            
    def save_check(self,status):
        '''
        Cambia el valor del flag save al marcar la casilla correspondiente
        '''
        if status == QtCore.Qt.Checked:
            self.save = True
        else: 
            self.save = False
            
    def from_zero(self,status):
        '''
        Cambia el valor del flag pre_magnetization al marcar la casilla correspondiente
        '''
        if status == QtCore.Qt.Checked:
            self.from_zero_field = True
        else:
            self.from_zero_field = False
       
    def max_f(self):
        '''
        Change the flag to start the measurement when the field is max (if from_zero is False)
        '''
        self.measure = True 
           
    def update(self,data):
        '''
        Funcion para actualizar con los ultimos valores obtenidos de las mediciones
        '''
        # Actualizo las listas con los resultados obtenidos
        if self.from_zero:
            self.resistance.append(data[1])
            self.voltage.append(data[0])
            # Escribo los ultimos resultados en las casillas correspondientes en el GUI
            self.ui.lineEdit_10.setText(self._translate("MainWindow", "{}".format(str(self.resistance[-1]))))
            self.ui.lineEdit_11.setText(self._translate("MainWindow", "{}".format(str(self.voltage[-1]))))
            # Si tengo la calibracion, grafico y guardo la resistencia y el valor del campo
            if self.calibration:
                slope = float(self.ui.lineEdit_6.text())
                intercept = float(self.ui.lineEdit_7.text())
                self.curve.setData(slope*self.voltage + intercept,self.resistance)
                if self.save and self.running_state:
                    self.f = open(self.path + '/{}'.format(self.param['name']),'a+')
                    self.f.write('{},{}\n'.format(slope*data[0] + intercept,data[1]))
                    self.f.close()
            # Si no tengo la calibracion, grafico y guardo la resistencia y el valor del voltaje de referencia
            else:
                self.curve.setData(self.voltage,self.resistance)
                if self.save and self.running_state:
                    self.f = open(self.path + '/{}'.format(self.param['name']),'a+')
                    self.f.write('{},{}\n'.format(data[0],data[1]))    
                    self.f.close()

        elif self.measure:
            self.resistance.append(data[1])
            self.voltage.append(data[0])
            # Escribo los ultimos resultados en las casillas correspondientes en el GUI
            self.ui.lineEdit_10.setText(self._translate("MainWindow", "{}".format(str(self.resistance[-1]))))
            self.ui.lineEdit_11.setText(self._translate("MainWindow", "{}".format(str(self.voltage[-1]))))
            # Si tengo la calibracion, grafico y guardo la resistencia y el valor del campo
            if self.calibration:
                slope = float(self.ui.lineEdit_6.text())
                intercept = float(self.ui.lineEdit_7.text())
                self.ui.lineEdit_11.setText(self._translate("MainWindow", "{}".format(str(slope*data[0] + intercept))))
                self.curve.setData(slope*self.voltage + intercept,self.resistance)
                if self.save and self.running_state:
                    self.f = open(self.path + '/{}'.format(self.param['name']),'a+')
                    self.f.write('{},{}\n'.format(slope*data[0] + intercept,data[1]))
                    self.f.close()
            # Si no tengo la calibracion, grafico y guardo la resistencia y el valor del voltaje de referencia
            else:
                self.curve.setData(self.voltage,self.resistance)
                if self.save and self.running_state:
                    self.f = open(self.path + '/{}'.format(self.param['name']),'a+')
                    self.f.write('{},{}\n'.format(data[0],data[1]))   
                    self.f.close()
        
    def user_stop(self):
        '''
        Funcion para detener la medicion. Envia señal al WorkingThread para detener a la fuente
        de corriente y enviar el campo a cero. Cambia el flag running_state a False.
        '''
        self.worker.stop()
        print('Pare el thread')
        self.running_state = False
        # if self.save:
        #     self.f.close()
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "User stop / Decreasing field"))

        
    def end(self):
        '''
        Al concluir la medicion se ejecuta esta función automáticamente. Cierra el archivo de guardado
        y cambia el flag running_state a False
        '''
        self.running_state = False
        # if self.save:
        #     self.f.close()
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Finished / Decreasing field"))

    def field_ready(self):
        '''
        Change the status windows when the field decreased to 0
        '''
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Field = 0 / Ready"))   
        self.ui.pushButton.setEnabled(True)
        self.ui.pushButton_2.setEnabled(False)       
        
    def start(self):
        '''
        Funcion principal, lee la entrada dada mediante el GUI para configurar los parámetros
        de la medicion
        '''

        # Cambio el flag running_state a True y hago reset de las listas que almacenan los resultados
        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton_2.setEnabled(True)
        self.running_state = True
        self.voltage = []
        self.resistance = []
        self.field = []
        # Diccionario que contiene los parámetros relevantes para la medicion
        # current_mA = Corriente de medición para el modo delta
        # samples = Numero de mediciones de resistencia para promediar
        # cmax y cmin = Valor de voltaje de referencia max y min (respectivamente)
        # step = Paso de voltaje de referencia
        # calibration = Flag para determinar si hay valores de calibracion
        # slope y intercept = Parámetros para pasar de voltaje a campo
        # save = Flag para determinar si es necesario guardar la medicion
        # name = Nombre del archivo (hay que incluir la extension a mano)
        # pre_magnetization = Flag para determinar si hay que realizar ciclo de pre-magnetizacion
        self.param = {'current_mA': float(self.ui.lineEdit.text()),
                      'samples': int(self.ui.lineEdit_2.text()),
                      'cmax' : float(self.ui.lineEdit_3.text()),
                      'cmin' : float(self.ui.lineEdit_4.text()),
                      'step' : float(self.ui.lineEdit_5.text()),
                      'save' : self.save,
                      'name' : str(self.ui.lineEdit_8.text())
                     }        
        
        time.sleep(2)
        # Creo el archivo para guardar la medicion. 
        if self.save:
            self.f = open(self.path + '/{}'.format(self.param['name']),'w')
            
            if self.calibration:
                self.f.write('Campo(G),Resistencia(Ohm)\n')
            else:
                self.f.write('Voltaje(V),Resistencia(Ohm)\n')
            self.f.close()
        # Llamo al Thread Worker        
        self.worker = Worker(self.param)
        # Conecto la señales del Thread con las funciones correspondientes
        self.worker.signals.result.connect(self.update)
        self.worker.signals.finished.connect(self.end)
        self.worker.signals.max_field.connect(self.max_f)
        self.worker.signals.zero_field.connect(self.field_ready)
        # Inicio el Thread
        self.threadpool.start(self.worker) 
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Running"))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    application = mywindow()
    application.show()
    sys.exit(app.exec_())
    