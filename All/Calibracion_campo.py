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
import LS_DSP455 as dsp
from sklearn.linear_model import LinearRegression

import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
 
from Calibracion_campo_GUI import Ui_MainWindow
 
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
        self.results_inst = [0.0,0.0]
        self.running = True
        self.fs = dsp.DSP_455()
        self.volt = cc.FieldControl()

        # 
    
    def measure(self):
        '''
        Mido la resistencia varias veces y promedio el resultado.
        '''
        field = self.fs.mean_field(self.parameters['samples'])
        return field
    
    def stop(self):
        '''
        Cambia el flag de self.running para parar la medicion y el thread.
        '''
        self.running = False         
    
    @pyqtSlot()
    def run(self):
        '''
        results_inst[0] = Voltage
        results_inst[1] = Field
        '''
        vaux = 0
        self.running = True
        while self.running and vaux>self.parameters['vmin'] :
            self.volt.set_voltage(vaux)
            vaux += -0.025
            time.sleep(0.5)
       
        if self.running:
            vaux = self.parameters['vmin']
            self.volt.set_voltage(vaux)
            
        
        while self.running and vaux < self.parameters['vmax']:
            self.volt.set_voltage_steps(vaux)
            time.sleep(5)
            self.signals.result.emit([self.measure(),vaux])
            vaux += self.parameters['step']
        
        if self.running:
            self.volt.set_voltage_steps(self.parameters['vmax'])
            time.sleep(5)
            self.signals.result.emit([self.measure(),vaux])
            self.running= False
            
        if not self.running:
            self.volt.set_voltage_steps(0)
            self.signals.finished.emit()

class mywindow(QtWidgets.QMainWindow):
 
    def __init__(self):
 
        super(mywindow, self).__init__()
        '''
        Setup inicial para configurar los aspectos relevantes de la GUI
        '''
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)    
        self.ui.pushButton_4.setEnabled(False)
        # Corroboro si es necesario guardar la medicion
        self.ui.checkBox_2.stateChanged.connect(self.save_check)
        self.save = False          
        # Configuro los parametros del grafico
        self.curve = self.ui.graphWidget.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
        self.ui.graphWidget.setLabel('left', "Field", units='G')
        self.ui.graphWidget.setLabel('bottom', "Voltaje", units='V')     
        # Inicia la medicion al apretar el boton start
        self.ui.pushButton_5.pressed.connect(self.start)
        # Estado de la medicion, por default es False
        self.running_state = False
        # Pausa la medicion al apretar el boton stop
        self.ui.pushButton_4.pressed.connect(self.stop)
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

            
    def save_check(self,status):
        '''
        Cambia el valor del flag save al marcar la casilla correspondiente
        '''
        if status == QtCore.Qt.Checked:
            self.save = True
        else: 
            self.save = False
                                
    def update(self,data):
        '''
        Funcion para actualizar con los ultimos valores obtenidos de las mediciones
        '''
        # Actualizo las listas con los resultados obtenidos
        self.voltage.append(data[1])
        self.field.append(data[0])
        # Escribo los ultimos resultados en las casillas correspondientes en el GUI
        self.ui.lineEdit_11.setText(self._translate("MainWindow", "{}".format(str(self.voltage[-1]))))
        self.ui.lineEdit_12.setText(self._translate("MainWindow", "{}".format(str(self.field[-1]))))
        # Si tengo la calibracion, grafico y guardo la resistencia y el valor del campo
        self.curve.setData(self.voltage,self.field)
        if self.param['save'] and self.running_state:
            self.f.write('{},{}\n'.format(self.voltage[-1],self.field[-1]))
        # Si no tengo la calibracion, grafico y guardo la resistencia y el valor del voltaje de referencia        

        
    def stop(self):
        '''
        Funcion para detener la medicion. Envia señal al WorkingThread para detener a la fuente
        de corriente y enviar el campo a cero. Cambia el flag running_state a False.
        '''
        self.worker.stop()
        self.ui.lineEdit_10.setText(self._translate("MainWindow", "User stop / Decreasing Field"))
        self.running_state = False
        
    def end(self):
        '''
        Al concluir la medicion se ejecuta esta función automáticamente. Cierra el archivo de guardado
        y cambia el flag running_state a False
        '''
        
        if self.param['save']:
            self.f.close()
        self.ui.lineEdit_10.setText(self._translate("MainWindow", "Finished"))
        
        if self.running_state:
            self.calibrate()
            
        self.running_state = False
        self.ui.pushButton_4.setEnabled(False)
        self.ui.pushButton_5.setEnabled(True)   
        
        
    def calibrate(self):
        X = np.array(self.voltage).reshape((-1,1))
        y = np.array(self.field).reshape((-1,1))
        lr = LinearRegression()
        lr.fit(X,y)
        a = lr.coef_
        b = lr.intercept_
        self.ui.lineEdit_8.setText(self._translate("MainWindow", str(a[0])))
        self.ui.lineEdit_9.setText(self._translate("MainWindow", str(b)))
        if self.param['save']:
            self.f = open(self.path + '/Results_{}'.format(self.param['name']),'w')
            self.f.write('Slope(G/V),Intercept(G)\n')
            self.f.write('{},{}\n'.format(a,b))
            self.f.close()
            
            
    def start(self):
        '''
        Funcion principal, lee la entrada dada mediante el GUI para configurar los parámetros
        de la medicion
        '''
        # Evito iniciar dos veces consecutivas la corrida
        
        # Cambio el flag running_state a True y hago reset de las listas que almacenan los resultados
        self.running_state = True
        self.ui.pushButton_4.setEnabled(True)
        self.ui.pushButton_5.setEnabled(False)
        self.voltage = []
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
        self.param = {'samples': int(self.ui.lineEdit_4.text()),
                      'vmax' : float(self.ui.lineEdit_1.text()),
                      'vmin' : float(self.ui.lineEdit_2.text()),
                      'step' : float(self.ui.lineEdit_5.text()),
                      'save' : self.save,
                      'name' : str(self.ui.lineEdit_7.text()),
                     }        
        
        # Creo el archivo para guardar la medicion. 
        if self.param['save']:
            self.f = open(self.path + '/{}'.format(self.param['name']),'w')
            self.f.write('Voltage(V),Field(G)\n')

        # Llamo al Thread Worker        
        self.worker = Worker(self.param)
        # Conecto la señales del Thread con las funciones correspondientes
        self.worker.signals.result.connect(self.update)
        self.worker.signals.finished.connect(self.end)
        # Inicio el Thread
        self.threadpool.start(self.worker) 
        self.ui.lineEdit_10.setText(self._translate("MainWindow", "Running"))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    application = mywindow()
    application.show()
    sys.exit(app.exec_())
    