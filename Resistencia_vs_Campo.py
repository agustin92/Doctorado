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
        self.parameters = parameters
        self.signals = WorkerSignals()
        self.results_inst = [0.0,0.0,0.0]
        self.running = True
        self.res = kd.K6221()
        self.campo = cc.FieldControl()

        # Add the callback to our kwargs
    
    def measure(self):
        resistance = self.res.mean_meas(self.parameters['samples'])
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
        
        self.res.reset()
        time.sleep(2)
        self.res.delta_mode(self.parameters['current_mA']/1000.0)
        time.sleep(1)
        
        
        try:
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
                
                self.res.stop_meas()
                
                
            if not self.running:
                self.res.stop_meas()
                self.campo.set_voltage_steps(0.0)
                time.sleep(5)
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
        
        self.ui.pushButton_3.clicked.connect(self.open_dialog_box)
        self.path = ''
        

        self.show()
        self.threadpool = QThreadPool()
        self._translate = QtCore.QCoreApplication.translate
        
        
    def open_dialog_box(self):
        file = ''
        file = QFileDialog.getExistingDirectory()
        self.path = file
    
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
        
        self.ui.lineEdit_10.setText(self._translate("MainWindow", "{}".format(str(self.resistance[-1]))))
        self.ui.lineEdit_11.setText(self._translate("MainWindow", "{}".format(str(self.voltage[-1]))))
        self.ui.lineEdit_12.setText(self._translate("MainWindow", "{}".format(str(self.field[-1]))))
        
        if self.param['calibration']:
            self.curve.setData(self.field,self.resistance)
            if self.param['save']:
                self.f.write('{},{}\n'.format(data[2],data[1]))
        else:
            self.curve.setData(self.voltage,self.resistance)
            if self.param['save']:
                self.f.write('{},{}\n'.format(data[0],data[1]))            

        
    def stop(self):
        self.worker.stop()
        print('Pare el thread')
        if self.param['save']:
            self.f.close()
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "User stop"))
        
    def end(self):
        if self.param['save']:
            self.f.close()
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Finished"))
        print('Medicion finalizada')
        
        
    def start(self):
        
#        self.curve.setData([1,2,3],[4,3,2])
        self.voltage = []
        self.resistance = []
        self.field = []
        
        
        self.param = {'current_mA': float(self.ui.lineEdit.text()),
                      'samples': int(self.ui.lineEdit_2.text()),
                      'cmax' : float(self.ui.lineEdit_3.text()),
                      'cmin' : float(self.ui.lineEdit_4.text()),
                      'step' : float(self.ui.lineEdit_5.text()),
                      'calibration': self.calibration,
                      'slope' : float(self.ui.lineEdit_6.text()),
                      'intercept' : float(self.ui.lineEdit_7.text()),
                      'save' : self.save,
                      'name' : str(self.ui.lineEdit_8.text())
                     }        
        

        tiempo_aux_ini = time.time()
        tiempo_aux = tiempo_aux_ini
        while (tiempo_aux - tiempo_aux_ini) < 2:
            tiempo_aux = time.time()
        
        if self.param['save']:
            self.f = open(self.path + '/{}'.format(self.param['name']),'w')
            
            if self.param['calibration']:
                self.f.write('Campo(G),Resistencia(Ohm)\n')
            else:
                self.f.write('Voltaje(V),Resistencia(Ohm)\n')
                
                
        self.worker = Worker(self.param)
        self.worker.signals.result.connect(self.update)
        self.worker.signals.finished.connect(self.end)
        self.threadpool.start(self.worker) 
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Running"))

            
#        self.ui.pushButton.clicked.connect(self.btnClicked) # connecting the clicked signal with btnClicked slot
# 
#    def btnClicked(self):
# 
#        self.ui.label.setText("Button Clicked")
 
 
#app = QtWidgets.QApplication([])
# 
#application = mywindow()
# 
#application.show()
#app.exec_()
#sys.exit(app.exec())
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    application = mywindow()
    application.show()
    sys.exit(app.exec_())
    