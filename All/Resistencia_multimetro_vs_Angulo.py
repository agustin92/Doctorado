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
import Controlador_multimetro as mt

import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
 
from Resistencia_multimetro_vs_Angulo_GUI import Ui_MainWindow
 
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
    finished = pyqtSignal()
    
class Worker(QRunnable):
    '''
    Field thread.
    Change the value of the magnetic field and emit a signal after reached the set value. 

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
    '''

    def __init__(self, field_contol, field_voltage):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.field = field_contol
        self.voltage = field_voltage
        self.signals = WorkerSignals()
        # Add the callback to our kwargs

    
    def stop(self):
        self.running = False
        self.temp.set_range() 
        self.temp.set_ramp(0)
    
    @pyqtSlot()
    def run(self):
        '''

        '''
        try:
            self.field.set_voltage_steps(self.voltage)
            time.sleep(5)
            
        finally:
            self.signals.finished.emit()  # Done

class WorkerSignals2(QObject):
    '''
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        No data    
  
    result
        `object` data returned from processing, anything

    '''
    finished2 = pyqtSignal()
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
        if self.parameters['status']:
            self.mul.reset()
            if self.parameters['mode'] == '2_Wires':
                self.mul.mode_2wire()
            else:
                self.mul.mode_4wire()    
        self.mul.continuous_mode(on=True)      
    
    @pyqtSlot()
    def run(self):
        '''

        '''
        self.signals.result2.emit(self.mul.mean_meas(self.parameters['samples']))
        self.mul.continuous_mode()
        self.signals.finished2.emit()  # Done



class mywindow(QtWidgets.QMainWindow):
 
    def __init__(self):
 
        super(mywindow, self).__init__()
 
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
           
        
        self.ui.pushButton.pressed.connect(self.set_field)
        
        self.ui.pushButton_5.pressed.connect(self.start)
        self.ui.pushButton_2.pressed.connect(self.set_angle)
        self.ui.pushButton_4.pressed.connect(self.end)
        
        self.angle = []
        self.resistance = []
        
        self.show()
        self.threadpool = QThreadPool ()
        self._translate = QtCore.QCoreApplication.translate
        
        self.curve = self.ui.graphWidget.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
        self.ui.graphWidget.setLabel('left', "Resistencia", units='Ohm')
        self.ui.graphWidget.setLabel('bottom', "Angulo", units='degree')        
                
        self.field_controler = cc.FieldControl()    
        self.mul = mt.K2010()
        self.first = True
        
        self.ui.checkBox_2.stateChanged.connect(self.save_check)
        self.save = False        
 
        self.ui.pushButton_3.clicked.connect(self.open_dialog_box)
        self.path = ''
        
    def set_field(self, field = None):
        '''
        Initialize the thread that controls the field
        '''
        if field == None:
            self.field_value = float(self.ui.lineEdit_3.text())
        else:
            self.field_value = field
        self.worker = Worker(self.field_controler, self.field_value)
        self.worker.signals.finished.connect(self.mod_status)
        self.threadpool.start(self.worker) 
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Changing Field"))
        
        
    def mod_status(self):
        '''
        Show the field value after the modification of the value
        '''
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Field {}V".format(self.field_value)))
        self.ui.lineEdit_10.setText(self._translate("MainWindow", "{}".format(self.field_value)))
        
    def set_angle(self):
        '''
        Add the new value of the angle and enable the measure buttom
        '''
        self.angle.append(float(self.ui.lineEdit_4.text()))
        self.ui.pushButton_5.setEnabled(True)
             
    def end(self):
        '''
        End the sequence, restart the list that save the values and prepare de code for the next measurement
        '''
        if self.save:
            self.f.close()
        self.resistance = []
        self.angle = []
        self.first = True
        self.set_field(field=0.0)
        
            
    def update(self,data):
        '''
        Get the results of the last measurement, add the results to the list, and replot with the new results
        '''
        
        self.resistance.append(data)
        
        self.ui.lineEdit_11.setText(self._translate("MainWindow", "{}".format(str(self.resistance[-1]))))
        self.ui.lineEdit_12.setText(self._translate("MainWindow", "{}".format(str(self.angle[-1]))))
        
        self.curve.setData(self.angle,self.resistance)
        
        if self.save:
            self.f.write('{},{},{}\n'.format(self.angle[-1],self.resistance[-1],self.ui.lineEdit_3.text()))
    
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
        
    
    def end_mes(self):
        '''
        '''
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Done"))
    
    def start(self):
        '''
        Start the measurement thread, disabled the measure buttom  
        '''
        
        self.ui.pushButton_5.setEnabled(False)
        self.param = {'mode' : self.ui.comboBox_2.currentText(),
                      'samples': int(self.ui.lineEdit_2.text()),
                      'res' : self.res
                     }                
        
        if self.first:
            self.param['status'] = True
            self.first = False
            
            if self.save:
                self.f = open(self.path + '/{}'.format(self.ui.lineEdit_8.text()),'w')
                self.f.write('Angle (deg),Resistance (Ohm), Voltage (V)\n')
        else:
            self.param['status'] = False
            
            
        self.worker2 = Worker2(self.param,self.mul)
        self.worker2.signals.result2.connect(self.update)
        self.worker2.signals.finished2.connect(self.end_mes)
        self.threadpool.start(self.worker2) 
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Running"))

            

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    application = mywindow()
    application.show()
    sys.exit(app.exec_())

