# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 15:01:02 2020

@author: Agustin Lopez Pedroso
agustin.lopezpedroso@gmail.com
"""

from PyQt5 import QtWidgets, Qt, QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np
import time 

import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
 
from Resistencia_vs_Campo_GUI import Ui_MainWindow
 
import sys
 
###
#Pendientes: Poner result emit donde corresponda, revisar si debo pasar los resultados en cada emit
# revisar toda la estructura del codigo para adaptarlo a la nueva clase
# Poner que el stop detenga la medicion y lleve el campo a cero, no es necesario que deje de correr
#la parte gráfica, poner que guarde ahí si es que no lo hace antes. Con un flag en el while es suficiente
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
        self.parameters = parameters
        self.signals = WorkerSignals()
        self.results_inst = [0.0,0.0,0.0]
        self.running = True

        # Add the callback to our kwargs
    
    def measure(self, voltage):
        resistance = np.random.randn()
        return resistance
    
    def stop(self):
        self.running = False         
    
    @pyqtSlot()
    def run(self):
        '''
        results_inst[0] = Voltage
        results_inst[1] = Resistencia
        results_inst[2] = Campo
        '''
        
        try:
            while self.results_inst[0] < self.parameters['cmax'] and self.running:
                print('mido')
                self.results_inst[1] = self.measure(self.results_inst[0])
                if self.parameters['calibration']:
                    self.results_inst[2] = self.parameters['slope']*self.results_inst[0]+ self.parameters['intercept']
                result = self.results_inst
                self.signals.result.emit(result)
                time.sleep(0.1)
                self.results_inst[0] += self.parameters['step']
                time.sleep(2)
            
            if self.running:
                self.results_inst[0] = self.parameters['cmax']
                self.results_inst[1] = self.measure(self.results_inst[0])
                if self.parameters['calibration']:
                    self.results_inst[2] = self.parameters['slope']*self.results_inst[0]+ self.parameters['intercept']
                result = self.results_inst
                self.signals.result.emit(result)
                time.sleep(0.1)

            while self.results_inst[0] > self.parameters['cmin'] and self.running:
                print('mido')
                self.results_inst[1] = self.measure(self.results_inst[0])
                if self.parameters['calibration']:
                    self.results_inst[2] = self.parameters['slope']*self.results_inst[0]+ self.parameters['intercept']
                result = self.results_inst
                self.signals.result.emit(result)
                time.sleep(0.1)
                self.results_inst[0] += -1.0*self.parameters['step']
                time.sleep(2)                        

            if self.running:
                self.results_inst[0] = self.parameters['cmin']
                self.results_inst[1] = self.measure(self.results_inst[0])
                if self.parameters['calibration']:
                    self.results_inst[2] = self.parameters['slope']*self.results_inst[0]+ self.parameters['intercept']
                result = self.results_inst
                self.signals.result.emit(result)
                time.sleep(0.1)

            while self.results_inst[0] < 0.0 and self.running:
                print('mido')
                self.results_inst[1] = self.measure(self.results_inst[0])
                if self.parameters['calibration']:
                    self.results_inst[2] = self.parameters['slope']*self.results_inst[0]+ self.parameters['intercept']
                result = self.results_inst
                self.signals.result.emit(result)
                time.sleep(0.1)
                self.results_inst[0] += self.parameters['step']
                time.sleep(2)
                     
            if self.running:
                self.results_inst[0] = 0.0
                self.results_inst[1] = self.measure(self.results_inst[0])
                if self.parameters['calibration']:
                    self.results_inst[2] = self.parameters['slope']*self.results_inst[0]+ self.parameters['intercept']
                result = self.results_inst
                self.signals.result.emit(result)
                time.sleep(0.1)
                
            if not self.running:
                print('pare la medicion')
            
        except not self.running:
            print('pare la medicion')

        finally:
            self.signals.finished.emit()  # Done


class mywindow(QtWidgets.QMainWindow):
 
    def __init__(self):
 
        super(mywindow, self).__init__()
 
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.ui.checkBox.stateChanged.connect(self.calibration_check)
        self.calibration = False

        self.ui.checkBox_2.stateChanged.connect(self.save_check)
        self.save = False
        
        self.curve = self.ui.graphWidget.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
        self.ui.graphWidget.setLabel('left', "Resistencia", units='Ohm')
        self.ui.graphWidget.setLabel('bottom', "Voltaje", units='V')
        
        
        self.ui.pushButton.pressed.connect(self.start)
#        self.running = False
        self.ui.pushButton_2.pressed.connect(self.stop)
        
        self.voltage = []
        self.resistance = []
        self.field = []
        
        self.show()
        self.threadpool = QThreadPool()
        
    def calibration_check(self,status):
        
        if status == QtCore.Qt.Checked:
            self.calibration = True
            self.ui.graphWidget.setLabel('bottom', "Campo", units='Gauss')
        else: 
            self.calibration = False
            self.ui.graphWidget.setLabel('bottom', "Voltaje", units='V')
            
    def save_check(self,status):
        
        if status == QtCore.Qt.Checked:
            self.save = True
        else: 
            self.save = False
            
    def update(self,data):
        self.resistance.append(data[1])
        self.voltage.append(data[0])
        self.field.append(data[2])
        
        if self.param['calibration']:
            self.curve.setData(self.field,self.resistance)
        else:
            self.curve.setData(self.voltage,self.resistance)

        
    def stop(self):
        self.worker.stop()
        print('Pare el thread')
        
        
    def start(self):
        
#        self.curve.setData([1,2,3],[4,3,2])
        
        self.param = {'current_mA': float(self.ui.lineEdit.text()),
                      'samples': int(self.ui.lineEdit_2.text()),
                      'cmax' : float(self.ui.lineEdit_3.text()),
                      'cmin' : float(self.ui.lineEdit_4.text()),
                      'step' : float(self.ui.lineEdit_5.text()),
                      'calibration': self.calibration,
                      'slope' : float(self.ui.lineEdit_6.text()),
                      'intercept' : float(self.ui.lineEdit_7.text()),
                      'save' : self.save,
                      'name' : self.ui.lineEdit_7.text()
                     }        
        

        tiempo_aux_ini = time.time()
        tiempo_aux = tiempo_aux_ini
        while (tiempo_aux - tiempo_aux_ini) < 2:
            tiempo_aux = time.time()

        
        self.worker = Worker(self.param)
        self.worker.signals.result.connect(self.update)
        self.threadpool.start(self.worker) 

            
#        self.ui.pushButton.clicked.connect(self.btnClicked) # connecting the clicked signal with btnClicked slot
# 
#    def btnClicked(self):
# 
#        self.ui.label.setText("Button Clicked")
 
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    application = mywindow()
    application.show()
    sys.exit(app.exec_()) 
    
#app = QtWidgets.QApplication([])
# 
#application = mywindow()
# 
#application.show()
#app.exec_()
#sys.exit(app.exec())