# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 14:18:40 2020

@author: Agustin Lopez Pedroso
agustin.lopezpedroso@gmail.com
"""

from PyQt5 import QtWidgets, Qt, QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np
import time 
#import Controlador_campo as cc
import Keithley_6221 as kd
import Controlador_temp as te

import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
 
from Resistencia_vs_Temperatura_GUI import Ui_MainWindow
 
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
        self.results_inst = [0.0,0.0,0.0,0.0]
        self.running = True
        self.res = kd.K6221()
        self.temp = te.Ls331()
        if parameters['field_on']:
            self.campo = cc.FieldControl()

        # Add the callback to our kwargs
    
    def measure(self):
        resistance = self.res.mean_meas(self.parameters['samples'])
        temperature_a = self.temp.get_temp()[0]
        temperature_b = self.temp.get_temp()[1]
        return temperature_a, temperature_b, resistance
    
    def stop(self):
        self.running = False         
    
    @pyqtSlot()
    def run(self):
        '''
        results_inst[0] = Temperature_a
        results_inst[1] = Temperature_b
        results_inst[2] = Resistance
        results_inst[3] = Time
        '''
        
        self.res.reset()
        time.sleep(2)
        self.res.delta_mode(self.parameters['current_mA']/1000.0)
        time.sleep(1)
        self.temp.change_temp(self.parameters['temperature'],self.parameters['rate'],
                              self.parameters['heater'])
        time.sleep(5)
        
        ti = time.time()
        
        try:
            while True and self.running:
                time_aux = time.time() - ti             
                self.results_inst[:3] = self.measure()
                self.results_inst[3] = time_aux
                result = self.results_inst
                self.signals.result.emit(result)
                time.sleep(self.parameters['sleep_time'])
       
#                self.res.stop_meas()
#                
#                
#            if not self.running:
#                self.res.stop_meas()
#                self.campo.set_voltage_steps(0.0)
#                time.sleep(5)
#                print('pare la medicion')
            
            if not self.running:
                self.res.stop_meas()
                self.temp.set_range()
                print('pare la medicion')
                pass    
            
        except not self.running:
            self.res.stop_meas()
            self.temp.set_range()
            print('pare la medicion')
            pass

        finally:
            self.signals.finished.emit()  # Done


class mywindow(QtWidgets.QMainWindow):
 
    def __init__(self):
 
        super(mywindow, self).__init__()
 
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.ui.checkBox.stateChanged.connect(self.field_check)
        self.field_on = False

        self.ui.checkBox_2.stateChanged.connect(self.save_check)
        self.save = False
        
        self.curve = self.ui.graphWidget.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
        self.ui.graphWidget.setLabel('left', "Resistencia", units='Ohm')
        self.ui.graphWidget.setLabel('bottom', "Temperature_A", units='K')
        
        self.curve2 = self.ui.graphWidget_2.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
        self.ui.graphWidget_2.setLabel('left', "Temperature_A", units='K')
        self.ui.graphWidget_2.setLabel('bottom', "Time", units='seg')
                
        self.curve3 = self.ui.graphWidget_3.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
        self.ui.graphWidget_3.setLabel('left', "Temperature_B", units='K')
        self.ui.graphWidget_3.setLabel('bottom', "Time", units='seg')        
        
        self.ui.pushButton.pressed.connect(self.start)
        self.running_state = False
        self.ui.pushButton_2.pressed.connect(self.stop)
        
        self.ui.pushButton_3.clicked.connect(self.open_dialog_box)
        self.path = ''
        
        self.show()
        self.threadpool = QThreadPool()
        self._translate = QtCore.QCoreApplication.translate
        self.heater = 0
        
        
    def open_dialog_box(self):
        file = ''
        file = QFileDialog.getExistingDirectory()
        self.path = file
    
    def field_check(self,status):
        
        if status == QtCore.Qt.Checked:
            self.field_on = True
        else: 
            self.field_on = False
            
    def save_check(self,status):
        
        if status == QtCore.Qt.Checked:
            self.save = True
        else: 
            self.save = False
            
    def update(self,data):
        self.temperature_a.append(data[0])
        self.temperature_b.append(data[1])
        self.resistance.append(data[2])
        self.time.append(data[3])
        
        self.ui.lineEdit_11.setText(self._translate("MainWindow", "{}".format(str(self.resistance[-1]))))
        self.ui.lineEdit_12.setText(self._translate("MainWindow", "{}".format(str(self.temperature_a[-1]))))
        self.ui.lineEdit_13.setText(self._translate("MainWindow", "{}".format(str(self.temperature_b[-1]))))
        

        self.curve.setData(self.temperature_a,self.resistance)
        self.curve2.setData(self.time,self.temperature_a)
        self.curve3.setData(self.time,self.temperature_b)
        if self.param['save']:
            self.f.write('{},{},{},{}\n'.format(self.time[-1],self.temperature_a[-1],
                                                self.temperature_b[-1],self.resistance[-1]))


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
        if self.param['save']:
            self.f.close()
        self.ui.lineEdit_14.setText(self._translate("MainWindow", "User stop"))
        
        self.running_state = False
        
    def end(self):
        if self.param['save']:
            self.f.close()
        self.ui.lineEdit_14.setText(self._translate("MainWindow", "Finished"))
        print('Medicion finalizada')
        self.running_state = False
            
        
    def start(self):
        
        if not self.running_state:
    #        self.curve.setData([1,2,3],[4,3,2])
            self.running_state = True
            
            self.temperature_a = []
            self.temperature_b = []
            self.resistance = []
            self.time = []
            
            self.heater_state()
            
            self.param = {'current_mA': float(self.ui.lineEdit.text()),
                          'samples': int(self.ui.lineEdit_2.text()),
                          'field_on' : self.field_on,
                          'field' : float(self.ui.lineEdit_6.text()),
                          'temperature' : float(self.ui.lineEdit_7.text()),
                          'rate': float(self.ui.lineEdit_8.text()),
                          'heater' : self.heater,
                          'sleep_time' : float(self.ui.lineEdit_9.text()),
                          'save' : self.save,
                          'name' : str(self.ui.lineEdit_10.text())
                         }        
            
    
            tiempo_aux_ini = time.time()
            tiempo_aux = tiempo_aux_ini
            while (tiempo_aux - tiempo_aux_ini) < 2:
                tiempo_aux = time.time()
            
            if self.param['save']:
                self.f = open(self.path + '/{}'.format(self.param['name']),'w')
                self.f.write('Time(s),Temperature_a(K),Temperature_b(K),Resistance(Ohm)\n')
                
                    
            self.worker = Worker(self.param)
            self.worker.signals.result.connect(self.update)
            self.worker.signals.finished.connect(self.end)
            self.threadpool.start(self.worker) 
            self.ui.lineEdit_14.setText(self._translate("MainWindow", "Running"))

            
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
    