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
    result = pyqtSignal(object)
    
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
        self.campo = cc.FieldControl()

        # 
    
    def measure(self):
        '''
        Mido la resistencia varias veces y promedio el resultado.
        '''
        resistance = self.res.mean_meas(self.parameters['samples'])
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
        results_inst[2] = Campo
        
        Antes de medir hace un reset del equipo (ver controlador Keithley_6221)
        y arma el modo delta
        '''
        
        self.res.reset()
        time.sleep(2)
        self.res.delta_mode(self.parameters['current_mA']/1000.0)
        time.sleep(1)
        
        
        try:
            # Confirma si es necesario realizar el ciclo para pre-magnetizar la muestra
            if self.parameters['pre_magnetization']:
                self.campo.set_voltage_steps(self.parameters['cmin'] )
                time.sleep(2)
                self.campo.set_voltage_steps(0.0)
            
            # Ciclo de medicion para la curva M(H)
            # Primero sube al campo maximos, luego al campo minimo y termina en cero
            # En cada paso corrobora que el usuario no haya detenido la medición
            while self.results_inst[0] < self.parameters['cmax'] and self.running:
                self.campo.set_voltage_steps(self.results_inst[0])
                time.sleep(2)
                self.results_inst[1] = self.measure()
                if self.parameters['calibration']:
                    self.results_inst[2] = self.parameters['slope']*self.results_inst[0]+ self.parameters['intercept']
                result = self.results_inst
                self.signals.result.emit(result)
                time.sleep(0.1)
                self.results_inst[0] += self.parameters['step']
            
            if self.running:
                self.results_inst[0] = self.parameters['cmax']
                self.campo.set_voltage_steps(self.results_inst[0])
                time.sleep(2)
                self.results_inst[1] = self.measure()
                if self.parameters['calibration']:
                    self.results_inst[2] = self.parameters['slope']*self.results_inst[0]+ self.parameters['intercept']
                result = self.results_inst
                self.signals.result.emit(result)
                time.sleep(0.1)

            while self.results_inst[0] > self.parameters['cmin'] and self.running:
                self.campo.set_voltage_steps(self.results_inst[0])
                time.sleep(2)
                self.results_inst[1] = self.measure()
                if self.parameters['calibration']:
                    self.results_inst[2] = self.parameters['slope']*self.results_inst[0]+ self.parameters['intercept']
                result = self.results_inst
                self.signals.result.emit(result)
                time.sleep(0.1)
                self.results_inst[0] += -1.0*self.parameters['step']

            if self.running:
                self.results_inst[0] = self.parameters['cmin']
                self.campo.set_voltage_steps(self.results_inst[0])
                time.sleep(2)
                self.results_inst[1] = self.measure()
                if self.parameters['calibration']:
                    self.results_inst[2] = self.parameters['slope']*self.results_inst[0]+ self.parameters['intercept']
                result = self.results_inst
                self.signals.result.emit(result)
                time.sleep(0.1)

            while self.results_inst[0] < 0.0 and self.running:
                self.campo.set_voltage_steps(self.results_inst[0])
                time.sleep(2)
                self.results_inst[1] = self.measure()
                if self.parameters['calibration']:
                    self.results_inst[2] = self.parameters['slope']*self.results_inst[0]+ self.parameters['intercept']
                result = self.results_inst
                self.signals.result.emit(result)
                time.sleep(0.1)
                self.results_inst[0] += self.parameters['step']
                time.sleep(2)
                     
            if self.running:
                self.results_inst[0] = 0.0
                self.campo.set_voltage_steps(self.results_inst[0])
                time.sleep(2)                
                self.results_inst[1] = self.measure()
                if self.parameters['calibration']:
                    self.results_inst[2] = self.parameters['slope']*self.results_inst[0]+ self.parameters['intercept']
                result = self.results_inst
                self.signals.result.emit(result)
                time.sleep(0.1)
           #Finalizo la medicion si es que no fue detenida previamente     
                self.res.stop_meas()
                
            # Si el usuario detiene la medicion cambia el flag.
            # Paro la medicion del modo delta y lleo el campo a cero
            if not self.running:
                self.res.stop_meas()
                self.campo.set_voltage_steps(0.0)
                time.sleep(5)
                print('pare la medicion')
            
        except not self.running:
            print('pare la medicion')
            
            
            
        finally:
            '''
            Emito la señal de detencion del thread
            '''
            self.signals.finished.emit()  # Done


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
        self.ui.checkBox_3.stateChanged.connect(self.pre_mag)
        self.pre_magnetization = False       
        # Configuro los parametros del grafico
        self.curve = self.ui.graphWidget.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
        self.ui.graphWidget.setLabel('left', "Resistencia", units='Ohm')
        self.ui.graphWidget.setLabel('bottom', "Voltaje", units='V')     
        # Inicia la medicion al apretar el boton start
        self.ui.pushButton.pressed.connect(self.start)
        # Estado de la medicion, por default es False
        self.running_state = False
        # Pausa la medicion al apretar el boton stop
        self.ui.pushButton_2.pressed.connect(self.stop)
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
            
    def pre_mag(self,status):
        '''
        Cambia el valor del flag pre_magnetization al marcar la casilla correspondiente
        '''
        if status == QtCore.Qt.Checked:
            self.pre_magnetization = True
        else:
            self.pre_magnetization = False
        
            
    def update(self,data):
        '''
        Funcion para actualizar con los ultimos valores obtenidos de las mediciones
        '''
        # Actualizo las listas con los resultados obtenidos
        self.resistance.append(data[1])
        self.voltage.append(data[0])
        self.field.append(data[2])
        # Escribo los ultimos resultados en las casillas correspondientes en el GUI
        self.ui.lineEdit_10.setText(self._translate("MainWindow", "{}".format(str(self.resistance[-1]))))
        self.ui.lineEdit_11.setText(self._translate("MainWindow", "{}".format(str(self.voltage[-1]))))
        self.ui.lineEdit_12.setText(self._translate("MainWindow", "{}".format(str(self.field[-1]))))
        # Si tengo la calibracion, grafico y guardo la resistencia y el valor del campo
        if self.param['calibration']:
            self.curve.setData(self.field,self.resistance)
            if self.param['save'] and self.running_state:
                self.f.write('{},{}\n'.format(data[2],data[1]))
        # Si no tengo la calibracion, grafico y guardo la resistencia y el valor del voltaje de referencia
        else:
            self.curve.setData(self.voltage,self.resistance)
            if self.param['save'] and self.running_state:
                self.f.write('{},{}\n'.format(data[0],data[1]))            

        
    def stop(self):
        '''
        Funcion para detener la medicion. Envia señal al WorkingThread para detener a la fuente
        de corriente y enviar el campo a cero. Cambia el flag running_state a False.
        '''
        self.worker.stop()
        print('Pare el thread')
        if self.param['save']:
            self.f.close()
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "User stop"))
        self.running_state = False
        
    def end(self):
        '''
        Al concluir la medicion se ejecuta esta función automáticamente. Cierra el archivo de guardado
        y cambia el flag running_state a False
        '''
        if self.param['save']:
            self.f.close()
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Finished"))
        self.running_state = False
        print('Medicion finalizada')
        
        
    def start(self):
        '''
        Funcion principal, lee la entrada dada mediante el GUI para configurar los parámetros
        de la medicion
        '''
        # Evito iniciar dos veces consecutivas la corrida
        if not self.running_state:
            # Cambio el flag running_state a True y hago reset de las listas que almacenan los resultados
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
                          'calibration': self.calibration,
                          'slope' : float(self.ui.lineEdit_6.text()),
                          'intercept' : float(self.ui.lineEdit_7.text()),
                          'save' : self.save,
                          'name' : str(self.ui.lineEdit_8.text()),
                          'pre_magnetization' : self.pre_magnetization
                         }        
            
            time.sleep(2)
            # Creo el archivo para guardar la medicion. 
            if self.param['save']:
                self.f = open(self.path + '/{}'.format(self.param['name']),'w')
                
                if self.param['calibration']:
                    self.f.write('Campo(G),Resistencia(Ohm)\n')
                else:
                    self.f.write('Voltaje(V),Resistencia(Ohm)\n')
            # Llamo al Thread Worker        
            self.worker = Worker(self.param)
            # Conecto la señales del Thread con las funciones correspondientes
            self.worker.signals.result.connect(self.update)
            self.worker.signals.finished.connect(self.end)
            # Inicio el Thread
            self.threadpool.start(self.worker) 
            self.ui.lineEdit_9.setText(self._translate("MainWindow", "Running"))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    application = mywindow()
    application.show()
    sys.exit(app.exec_())
    