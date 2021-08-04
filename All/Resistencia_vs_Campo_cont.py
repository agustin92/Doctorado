# -*- coding: utf-8 -*-
"""
Created on Wed Nov 18 18:19:26 2020

@author: Agustin Lopez Pedroso
agustin.lopezpedroso@gmail.com
"""
from PyQt5 import QtWidgets, Qt, QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np
import time 


import Controlador_campo as cc
import Keithley_6221 as mt

import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
 
from Resistencia_vs_Campo_cont_GUI import Ui_MainWindow
 
import sys


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        No data    
  
    result
        `object` data returned from processing, anything

    '''
    result1 = pyqtSignal(object)
    max_field = pyqtSignal()
    finished1 = pyqtSignal()
    zero_field = pyqtSignal()
    
class Worker(QRunnable):
    '''
    Field thread.
    Change the value of the magnetic field and emit a signal after reached the set value. 

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
    '''

    def __init__(self, params, field_control):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.field = field_control
        self.parameters = params
        self.signals = WorkerSignals()
        self.running = False
        # Add the callback to our kwargs

    
    def stop(self):
        '''
        Change the self.running flag to stop the measurment. This function is used when the user stop the measurment
        '''
        self.running = False
    
    @pyqtSlot()
    def run(self):
        '''
        Running thread. This function makes field loop and sends a signal after reaching the max field and after
        finishing the loop.
        '''
        cmax = self.parameters['cmax']
        cmin = self.parameters['cmin']
        rate = self.parameters['rate']/1000
        
        self.running = True
        
        caux = 0
        
        while caux < cmax and self.running:
            self.field.set_voltage(caux)
            self.signals.result1.emit(caux)
            caux += rate/2
            time.sleep(0.5)
        
        if self.running:
            caux = cmax
            self.field.set_voltage(caux)
            self.signals.result1.emit(caux)
            self.signals.max_field.emit()
        
        while caux > cmin and self.running:
            self.field.set_voltage(caux)
            self.signals.result1.emit(caux)
            caux += -rate/2
            time.sleep(0.5)         
            
        if self.running:
            caux = cmin
            self.field.set_voltage(caux)
            self.signals.result1.emit(caux)
            
        while caux < cmax and self.running:
            self.field.set_voltage(caux)
            self.signals.result1.emit(caux)
            caux += rate/2
            time.sleep(0.5) 
         
        if self.running:  
            self.signals.finished1.emit()
            self.field.set_voltage_steps(0)
            self.signals.zero_field.emit()
              # Done
            
        if not self.running:
            self.field.set_voltage_steps(0)
            self.signals.zero_field.emit()
            
class WorkerSignals2(QObject):
    '''
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        No data    
  
    result
        `object` data returned from processing, anything

    '''
    result2 = pyqtSignal(object)
    
class Worker2(QRunnable):
    '''
    Measure thread.
    Get the resistance and transmit the result to the main thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
    '''

    def __init__(self, parameters, mul):
        super(Worker2, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.parameters = parameters
        self.signals = WorkerSignals2()
        self.mul = mul
        self.mul.reset()
        self.mul.delta_mode(self.parameters['current_mA'])
        self.running_state = False
     
    
    @pyqtSlot()
    def run(self):
        '''
        Measure the resistance value until the field loop is finished or if the user stoped manualy the measurement
        '''
        self.running_state = True
        
        while self.running_state:
            self.signals.result2.emit(self.mul.mean_meas(self.parameters['samples']))
            time.sleep(self.parameters['sleep_time'])
            
        self.mul.stop_meas()
            
    def stop(self):
        '''
        Change the running_state flag to False to finish the measurment
        '''
        self.running_state = False

class mywindow(QtWidgets.QMainWindow):
 
    def __init__(self):
 
        super(mywindow, self).__init__()
 
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
           
        
        self.ui.pushButton.pressed.connect(self.start)        
        self.running_state = False        
        self.ui.pushButton_2.pressed.connect(self.user_stop) 
        self.ui.pushButton_2.setEnabled(False)
        # Corroboro el estado de la calibracion 
        self.ui.checkBox.stateChanged.connect(self.calibration_check)
        self.calibration = False
        # Corroboro si es necesario guardar la medicion
        self.ui.checkBox_2.stateChanged.connect(self.save_check)
        self.save = False
        # Corroboro si es necesario empezar la medición desde campo cero
        self.ui.checkBox_3.stateChanged.connect(self.from_zero_)
        self.from_zero = False  
        # Configuro los parametros del grafico
        self.curve = self.ui.graphWidget.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
        self.ui.graphWidget.setLabel('left', "Resistencia", units='Ohm')
        self.ui.graphWidget.setLabel('bottom', "Voltaje", units='V')   
        self.measure = False
        
        self.show()
        self.threadpool = QThreadPool ()
        self._translate = QtCore.QCoreApplication.translate
        # Cargo los equipos como objetos        
        self.field_controler = cc.FieldControl()    
        self.mul = mt.K6221()
        # Ventana para seleccionar la carpeta de guardado    
        self.ui.pushButton_3.clicked.connect(self.open_dialog_box)
        self.path = ''
        
        
    def calibration_check(self,status):
        '''
        Check the calibration check box
        '''
        if status == QtCore.Qt.Checked:
            self.calibration = True
            self.ui.graphWidget.setLabel('bottom', "Campo", units='Gauss')
        else: 
            self.calibration = False
            self.ui.graphWidget.setLabel('bottom', "Voltaje", units='V')

    def from_zero_(self,status):
        '''
        Check the from_zero check box. If it is true, the measurement will start from 0 field
        '''
        if status == QtCore.Qt.Checked:
            self.from_zero = True
        else:
            self.from_zero = False
                
             
    def end(self):
        '''
        End the sequence, restart the list that save the values and prepare the code for the next measurement
        '''
        if self.save:
            self.f.close()
        self.voltage = []
        self.resistance = []
        self.field = []
        self.worker2.stop()
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Finished / Descreasing Field"))
        # self.ui.pushButton.setEnabled(True)
        # self.ui.pushButton_2.setEnabled(False)
        self.running_state = False
        self.measure = False
     
    def user_stop(self):
        '''
        Stop the measrument if the stop buttom is pressed. Restart all the variables and turn down the instruments
        '''
        if self.save:
            self.f.close()
        self.voltage = []
        self.resistance = []
        self.field = []
        
        self.worker.stop()
        self.worker2.stop()
        # self.ui.pushButton.setEnabled(True)
        # self.ui.pushButton_2.setEnabled(False)
        self.running_state = False 
        self.measure = False
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "User stop / Decreasing field"))
        
    def field_ready(self):
        '''
        Change the status windows when the field decreased to 0
        '''
        self.ui.pushButton.setEnabled(True)
        self.ui.pushButton_2.setEnabled(False)        
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Field = 0 / Ready"))
        
    def max_f(self):
        '''
        Change the flag to start the measurement when the field is max (if from_zero is False)
        '''
        self.measure = True
    
    def update1(self,data):
        '''
        Get the voltage value from the working thread 1 and save it in an auxiliary variable 
        '''
        if self.param0['calibration']:
            self.field_aux = data*self.param0['slope']+self.param0['intercept']
        else:
            self.voltage_aux = data
        
    def update2(self,data):
        '''
        Get the results of the last resistance measurement, add the results to the list, and replot with the new results
        '''
        # The measurement start from zero if the check box is checked
        if self.from_zero:
            self.resistance.append(data)
            self.ui.lineEdit_10.setText(self._translate("MainWindow", "{}".format(str(self.resistance[-1]))))
            
            if self.param0['calibration'] and self.running_state:
                self.field.append(self.filed_aux)
                self.ui.lineEdit_12.setText(self._translate("MainWindow", "{}".format(str(self.field[-1]))))
                self.curve.setData(self.field,self.resistance)
            elif not self.param0['calibration'] and self.running_state:
                self.voltage.append(self.voltage_aux)
                self.ui.lineEdit_11.setText(self._translate("MainWindow", "{}".format(str(self.voltage[-1]))))
                self.curve.setData(self.voltage,self.resistance)
            
            if self.save:
                if self.param0['calibration'] and self.running_state:
                    self.f.write('{},{}\n'.format(self.field[-1],self.resistance[-1]))
                    
                elif not self.param0['calibration'] and self.running_state:
                    self.f.write('{},{}\n'.format(self.voltage[-1],self.resistance[-1]))
                    
        # Start the measurment after the field reached the max value
        elif self.measure:
            self.resistance.append(data)
            self.ui.lineEdit_10.setText(self._translate("MainWindow", "{}".format(str(self.resistance[-1]))))
            
            if self.param0['calibration'] and self.running_state:
                self.field.append(self.filed_aux)
                self.ui.lineEdit_12.setText(self._translate("MainWindow", "{}".format(str(self.field[-1]))))
                self.curve.setData(self.field,self.resistance)
            elif not self.param0['calibration'] and self.running_state:
                self.voltage.append(self.voltage_aux)
                self.ui.lineEdit_11.setText(self._translate("MainWindow", "{}".format(str(self.voltage[-1]))))
                self.curve.setData(self.voltage,self.resistance)
            
            if self.save:
                if self.param0['calibration'] and self.running_state:
                    self.f.write('{},{}\n'.format(self.field[-1],self.resistance[-1]))
                    
                elif not self.param0['calibration'] and self.running_state:
                    self.f.write('{},{}\n'.format(self.voltage[-1],self.resistance[-1]))        
                
    def save_check(self,status):
        '''
        Check if the save buttom is checked
        '''
        if status == QtCore.Qt.Checked:
            self.save = True
        else: 
            self.save = False    
 
    def open_dialog_box(self):
        '''
        Get the path to the directory where the results will be saved
        '''
        file = ''
        file = QFileDialog.getExistingDirectory()
        self.path = file
        
    
    def start(self):
        '''
        Start the measurement thread, disabled the measure buttom  
        '''
        
        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton_2.setEnabled(True)
        # Cambio el flag running_state a True y hago reset de las listas que almacenan los resultados
        self.running_state = True
        self.voltage_aux = 0
        self.field_aux = 0
        self.voltage = []
        self.resistance = []
        self.field = []
        # Diccionario que contiene los parámetros relevantes para la medicion
        # current_mA = Corriente de medición para el modo delta
        # samples = Numero de mediciones de resistencia para promediar
        # cmax y cmin = Valor de voltaje de referencia max y min (respectivamente)
        # rate = Rate de cambio del campo magnético en volts/seg
        # calibration = Flag para determinar si hay valores de calibracion
        # slope y intercept = Parámetros para pasar de voltaje a campo
        # save = Flag para determinar si es necesario guardar la medicion
        # name = Nombre del archivo (hay que incluir la extension a mano)
        # pre_magnetization = Flag para determinar si hay que realizar ciclo de pre-magnetizacion
        self.param0 = {'calibration': self.calibration,
                      'slope' : float(self.ui.lineEdit_6.text()),
                      'intercept' : float(self.ui.lineEdit_7.text()),
                      'from_zero' : self.from_zero,
                      'name' : str(self.ui.lineEdit_8.text())
                      }
        
        self.param1 = {'cmax' : float(self.ui.lineEdit_3.text()),
                      'cmin' : float(self.ui.lineEdit_4.text()),
                      'rate' : float(self.ui.lineEdit_5.text())
                     }             
        
        self.param2 = {'current_mA': float(self.ui.lineEdit.text())/1000,
                      'samples': int(self.ui.lineEdit_2.text()),    
                      'sleep_time' : float(self.ui.lineEdit_13.text())
                     }               
        
        # Creo el archivo para guardar la medicion. 
        if self.save:
            self.f = open(self.path + '/{}'.format(self.param0['name']),'w')
            
            if self.param0['calibration']:
                self.f.write('Campo(G),Resistencia(Ohm)\n')
            else:
                self.f.write('Voltaje(V),Resistencia(Ohm)\n')
            
        self.worker = Worker(self.param1,self.field_controler)
        self.worker.signals.result1.connect(self.update1)
        self.worker.signals.max_field.connect(self.max_f)
        self.worker.signals.finished1.connect(self.end)
        self.worker.signals.zero_field.connect(self.field_ready)
        self.threadpool.start(self.worker) 
        self.worker2 = Worker2(self.param2,self.mul)
        self.worker2.signals.result2.connect(self.update2)
        self.threadpool.start(self.worker2) 
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Running"))
            

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    application = mywindow()
    application.show()
    sys.exit(app.exec_())

