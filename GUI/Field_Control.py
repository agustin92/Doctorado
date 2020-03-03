# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 15:53:44 2020

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


 
from Field_Control_GUI import Ui_MainWindow
 
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
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
    '''

    def __init__(self, field_control, voltage):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.field = field_control
        self.voltage = voltage
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
    
    
    def stop(self):
        self.field.set_voltage_steps(0)
        time.sleep(5)     
    
    @pyqtSlot()
    def run(self):
        '''
        '''
        try:
            self.field.set_voltage_steps(self.voltage)
            time.sleep(5)
            
        finally:
            self.signals.finished.emit()  # Done


class mywindow(QtWidgets.QMainWindow):
 
    def __init__(self):
 
        super(mywindow, self).__init__()
 
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._translate = QtCore.QCoreApplication.translate
        
        self.ui.checkBox.stateChanged.connect(self.calibration_check)
        self.calibration = False
        
        self.field_controler = cc.FieldControl()
  
        
        self.ui.pushButton.pressed.connect(self.start)
#        self.running = False
        self.ui.pushButton_2.pressed.connect(self.stop)
    
        self.voltage = 0.0


        
        self.show()
        self.threadpool = QThreadPool()

        
        
    
    def calibration_check(self,status):
        
        if status == QtCore.Qt.Checked:
            self.calibration = True
            self.ui.label_3.setText(self._translate("MainWindow", "Field (Gauss)"))
        else: 
            self.calibration = False
            self.ui.label_3.setText(self._translate("MainWindow", "Voltage (Field)"))

        
    def stop(self):
        self.worker.stop()
        self.ui.lineEdit_4.setText(self._translate("MainWindow", "Field 0.0"))

    def end(self):
        self.ui.lineEdit_4.setText(self._translate("MainWindow", "Done. Field = {}".format(str(self.voltage))))
        
        
    def start(self):
        
        
        self.ui.lineEdit_4.setText(self._translate("MainWindow", "Wait"))
        if self.calibration:
            field = float(self.ui.lineEdit_3.text())
            slope = float(self.ui.lineEdit.text())
            intercept = float(self.ui.lineEdit_2.text())
            self.voltage =  (field-intercept)/slope
        
        else:
            self.voltage = float(self.ui.lineEdit_3.text())
                   
                
        self.worker = Worker(self.field_controler, self.voltage)
        
#        self.worker.signals.result.connect(self.update)
        self.worker.signals.finished.connect(self.end)
        self.threadpool.start(self.worker) 


            
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