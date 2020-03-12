# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 16:49:28 2020

@author: Usuario
"""

from PyQt5 import QtWidgets, Qt, QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np
import time 
import Controlador_temp as te

import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
 
from Temperature_Control_GUI import Ui_MainWindow
 
import sys
 
'''
 Pendientes Medir la temperatura cada algunos segundos y reportar cuando estoy
a una distancia de 0.5K para indicar que ya llegue a la temperatura deseada

'''

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
        self.temp = te.Ls331()
        self.running = False
        self.results_inst = [0.0,0.0,0,0.0]

        # Add the callback to our kwargs
    
    def measure(self):
        temperature_a = self.temp.get_temp()[0]
        temperature_b = self.temp.get_temp()[1]
        heater_output = self.temp.get_heater()
        return temperature_a, temperature_b, heater_output
    
    def stop(self):
        self.running = False
        self.temp.set_range() 
        self.temp.set_ramp(0)
    
    @pyqtSlot()
    def run(self):
        '''

        '''
        
        self.temp.change_temp(self.parameters['temperature'],self.parameters['rate'],
                              self.parameters['heater'])
        time.sleep(5)
        self.running =True
        ti = time.time()
        
        while self.running:
            self.results_inst[:3] = self.measure()
            time_aux = time.time() - ti
            self.results_inst[3] = time_aux
            self.signals.result.emit(self.results_inst)
            time.sleep(10)
            
        self.signals.finished.emit()  # Done
        self.running = False

class mywindow(QtWidgets.QMainWindow):
 
    def __init__(self):
 
        super(mywindow, self).__init__()
 
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
           
        
        self.ui.pushButton.pressed.connect(self.start)
        self.running_state = False
        self.ui.pushButton_2.pressed.connect(self.stop)
        
        
        self.show()
        self.threadpool = QThreadPool()
        self._translate = QtCore.QCoreApplication.translate
        self.heater = 0
        
        self.curve = self.ui.graphWidget.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
        self.ui.graphWidget.setLabel('left', "Temperatura_A", units='K')
        self.ui.graphWidget.setLabel('bottom', "Time", units='seg')        
        
        self.curve2 = self.ui.graphWidget_2.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
        self.ui.graphWidget_2.setLabel('left', "Temperature_B", units='K')
        self.ui.graphWidget_2.setLabel('bottom', "Time", units='seg')        

        self.ui.progressBar.setRange(0, 100)
        self.ui.progressBar.setValue(0)
        
    def heater_state(self):
        if self.ui.comboBox.currentText() == 'Off':
            self.heater = 0
        elif self.ui.comboBox.currentText() == 'Low':
            self.heater = 1
        elif self.ui.comboBox.currentText() == 'Med':
            self.heater = 2
        elif self.ui.comboBox.currentText() == 'High':
            self.heater = 3
            
        
    def stop(self):
        self.worker.stop()
        print('Pare el thread')
        self.ui.lineEdit_3.setText(self._translate("MainWindow", "User stop"))
        
        self.running_state = False
        
    def end(self):
        self.ui.lineEdit_3.setText(self._translate("MainWindow", "Done. Temperature {}".format(self.param['temperature'])))
        self.running_state = False
            
    def update(self,data):
        self.temperature_a.append(data[0])
        self.temperature_b.append(data[1])
        self.heater_output = data[2]        
        self.time.append(data[3])

        
        
        self.ui.lineEdit_4.setText(self._translate("MainWindow", "{}".format(str(self.temperature_a[-1]))))
        self.ui.lineEdit_5.setText(self._translate("MainWindow", "{}".format(str(self.temperature_b[-1]))))
        
        self.ui.progressBar.setValue(self.heater_output)
        self.curve.setData(self.time,self.temperature_a)
        self.curve2.setData(self.time,self.temperature_b)    
    
    def start(self):
        
        self.temperature_a = []
        self.temperature_b = []
        self.time = []
        self.heater_output = 0
        
        if not self.running_state:
    #        self.curve.setData([1,2,3],[4,3,2])
            self.running_state = True
            
            
            self.heater_state()
            
            self.param = {'temperature' : float(self.ui.lineEdit.text()),
                          'rate': float(self.ui.lineEdit_2.text()),
                          'heater' : self.heater,
                         }        
            
    
            tiempo_aux_ini = time.time()
            tiempo_aux = tiempo_aux_ini
            while (tiempo_aux - tiempo_aux_ini) < 2:
                tiempo_aux = time.time()
                
                    
            self.worker = Worker(self.param)
            self.worker.signals.result.connect(self.update)
            self.worker.signals.finished.connect(self.end)
            self.threadpool.start(self.worker) 
            self.ui.lineEdit_3.setText(self._translate("MainWindow", "Running"))

            

 
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