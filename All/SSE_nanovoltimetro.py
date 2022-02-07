# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 15:01:02 2020

@author: Agustin Lopez Pedroso
agustin.lopezpedroso@gmail.com

Upated Wed Jan 19 12:58:33 2022 to SSE

@author: Lara Solis
laramsolis@gmail.com

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
import Keithley_2182_SSE as nv
import Keithley_2010 as mt
import Controlador_temp as te

#import pyqtgraph as pg
#from pyqtgraph import PlotWidget, plot
 
from SSE_GUI import Ui_MainWindow
 
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
    result2 = pyqtSignal(object)
    
    zero_field = pyqtSignal()
    gradient_reached = pyqtSignal()
    
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
        self.results_inst = [0.0,0.0,0.0,0.0,0.0,0.0]
        self.results_grad = [0.0,0.0,0.0]
        self.running = True
#        self.set_gradient = False #solucionar
        self.res = kd.K6221()
        self.nano = nv.K2182()
        self.mult = mt.K2010()
        self.field = cc.FieldControl()
        self.temp = te.Ls331()

        # 
    
    def measure(self):
        '''
        Mido la señal varias veces y promedio el resultado.
        Devuelve el valor medio (signal[0]) y la desviacion estandar (signal[1])
        '''
        signal = self.nano.mean_meas(self.parameters['samples'])  #solucionar, poner std
        return signal
    
    def grad_measure(self):
        '''
        Mido el gradiente de temperatura.
        '''
        gradT = self.mult.measure()
        return gradT
    
    def stop(self):
        '''
        Cambia el flag de self.running para parar la medicion y el thread.
        '''
        self.running = False   

    
    @pyqtSlot()
    def run(self):
        '''
        results_inst[0] = Voltage
        results_inst[1] = Señal
        results_inst[2] = Gradiente
        results_inst[3] = Temperatura
        results_inst[4] = Corriente
        results_inst[5] = Desviacion estandar
        
        
        Para el gradiente:
        results_grad[0] = Gradiente
        results_grad[1] = Corriente
        results_grad[2] = Tiempo?
        
        Antes de medir hace un reset del equipo (ver controlador Keithley_6221)
        
        '''
        self.res.reset_soft()
        self.nano.reset()
        self.mult.reset()
        time.sleep(2)
        self.nano.calibrate()
        time.sleep(2)
        self.nano.mode()
        self.mult.mode()
        time.sleep(2)
        self.res.output(on=True)
        self.nano.output(on=True)
#        self.mult.output(on=True)
        
        cmax = self.parameters['cmax']
        cmin = self.parameters['cmin']
        step = self.parameters['step']
        target_gradT=self.parameters['deltaT']
        Imin = self.parameters['Imin']
        stab_time = self.parameters['stab_time']
        Imax = 31.623   #definido por la potencia máx de R = 2K (2W)
        Vcompl = 65     #definido por la potencia máx de R = 2K (2W) +2V para evitar compliance overshoot
        Istep = self.parameters['Istep']

        ti = time.time()
        
        self.running = True
        self.set_gradient = True  #para setear o no el grad
#==============================================================================
# Set Gradient

        Iaux = Imin
        if not self.set_gradient:
            self.res.current_mode(Iaux/1000 , Vcompl)
        gradT = self.grad_measure()
        
        achieved = target_gradT - 0.1 < gradT < target_gradT + 0.1
        
        if gradT < target_gradT - 0.1:
            while Iaux < Imax and not achieved and self.running and self.set_gradient:
                self.res.current_mode(Iaux/1000 , Vcompl)
                time.sleep(5)
                gradT = self.grad_measure()
                self.results_grad[0] = gradT
                self.results_grad[1] = Iaux
                self.results_grad[2] = time.time() - ti
                 
                self.signals.result2.emit(self.results_grad)
                 
                over_grad = gradT > target_gradT + 0.1
                achieved = target_gradT - 0.1 <= gradT <= target_gradT + 0.1
                if not achieved and not over_grad:
                    Iaux += Istep
                elif over_grad:
                    Istep = np.sqrt(Iaux**2 + Istep*Iaux + Istep**2/2) - Iaux #baja la mitad de potencia
                    Iaux -= Istep
                     
        elif gradT > target_gradT + 0.1:
            while Iaux >= 0 and not achieved and self.running and self.set_gradient:
                self.res.current_mode(Iaux/1000 , Vcompl)
                time.sleep(5)
                gradT = self.grad_measure()
                self.results_grad[0] = gradT
                self.results_grad[1] = Iaux
                self.results_grad[2] = time.time() - ti
                 
                self.signals.result2.emit(self.results_grad)
                 
                under_grad = gradT < target_gradT - 0.1
                achieved = target_gradT - 0.1 <= gradT <= target_gradT + 0.1
                if not achieved and not under_grad:
                    Iaux -= Istep
                elif under_grad:
                    Istep = np.sqrt(Iaux**2 + Istep*Iaux + Istep**2/2) - Iaux #sube la mitad de potencia
                    Iaux += Istep
#        time.sleep(300)
        t0=time.time()
        while time.time()-t0 < stab_time and self.running:
            time.sleep(5)
            gradT = self.grad_measure()
            self.results_grad[0] = gradT
            self.results_grad[1] = Iaux
            self.results_grad[2] = time.time() - ti
            self.signals.result2.emit(self.results_grad)

#==============================================================================
        caux = 0      
        while caux < cmax and self.running:
            self.field.set_voltage(caux)
            self.results_inst[0] = caux
            voltage = self.measure()
            self.results_inst[1] = voltage[0]*1E6
            self.results_inst[2] = self.grad_measure()
            self.results_inst[3] =  self.temp.get_temp()[1]
            self.results_inst[4] = Iaux
            self.results_inst[5] = voltage[1]*1E6
            self.signals.result.emit(self.results_inst)
            caux += step
            self.field.set_voltage_steps(caux)
            time.sleep(0.5)
        
        if self.running:
            caux = cmax
            self.field.set_voltage(caux)
            self.results_inst[0] = caux
            voltage = self.measure()
            self.results_inst[1] = voltage[0]*1E6
            self.results_inst[2] = self.grad_measure()
            self.results_inst[3] =  self.temp.get_temp()[1]
            self.results_inst[4] = Iaux
            self.results_inst[5] = voltage[1]*1E6
            self.signals.result.emit(self.results_inst)
            self.field.set_voltage_steps(caux)
            self.signals.max_field.emit()
            time.sleep(0.5)
        
        
        while caux > cmin and self.running:
            self.field.set_voltage(caux)
            self.results_inst[0] = caux
            voltage = self.measure()
            self.results_inst[1] = voltage[0]*1E6
            self.results_inst[2] = self.grad_measure()
            self.results_inst[3] =  self.temp.get_temp()[1]
            self.results_inst[4] = Iaux
            self.results_inst[5] = voltage[1]*1E6
            self.signals.result.emit(self.results_inst)
            caux += -step
            self.field.set_voltage_steps(caux)
            time.sleep(0.5)        
            
        if self.running:
            caux = cmin
            self.field.set_voltage(caux)
            self.results_inst[0] = caux
            voltage = self.measure()
            self.results_inst[1] = voltage[0]*1E6
            self.results_inst[2] = self.grad_measure()
            self.results_inst[3] =  self.temp.get_temp()[1]
            self.results_inst[4] = Iaux
            self.results_inst[5] = voltage[1]*1E6
            self.signals.result.emit(self.results_inst)
            self.field.set_voltage_steps(caux)
            self.signals.max_field.emit()
            time.sleep(0.5)
            
        while caux < cmax and self.running:
            self.field.set_voltage(caux)
            self.results_inst[0] = caux
            voltage = self.measure()
            self.results_inst[1] = voltage[0]*1E6
            self.results_inst[2] = self.grad_measure()
            self.results_inst[3] =  self.temp.get_temp()[1]
            self.results_inst[4] = Iaux
            self.results_inst[5] = voltage[1]*1E6
            self.signals.result.emit(self.results_inst)
            caux += step
            self.field.set_voltage_steps(caux)
            time.sleep(0.5)
            
#solucionar la funcion del Stop_gradient
        if self.running:  
            self.signals.finished.emit()
            self.res.output()
            self.nano.output()
            self.mult.output()
            self.field.set_voltage_steps(0)
            self.signals.zero_field.emit()
              # Done
            
        if not self.running:
            self.res.output()
            self.nano.output()
            self.mult.output()
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
        # Corroboro si es necesario setear con el gradiente
        self.ui.checkBox_4.stateChanged.connect(self.set_gradient_check)
        self.set_gradient = False 
        # Corroboro si es necesario hacer un ciclo de pre-magnetizacion
        self.ui.checkBox_3.stateChanged.connect(self.from_zero)
        self.from_zero_field = False 
        # Corroboro si es necesario llevar el gradiente a cero al final
        self.ui.checkBox_5.stateChanged.connect(self.stop_gradient_check)
        self.stop_gradient = False
        # Configuro los parametros del grafico de señal
        self.curve = self.ui.graphWidget.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
        self.ui.graphWidget.setLabel('left', "Voltaje", units='muV')
        self.ui.graphWidget.setLabel('bottom', "Voltaje", units='V')
        # Configuro los parametros del grafico de gradiente
        self.curve2 = self.ui.graphWidget_2.plot(pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
        self.ui.graphWidget_2.setLabel('left', "Delta T", units='K')
        self.ui.graphWidget_2.setLabel('bottom', "Tiempo", units='seg')
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
        
    def set_gradient_check(self,status):
        '''
        Cambia el valor del flag set_gradient al marcar la casilla correspondiente
        '''
        if status == QtCore.Qt.Checked:
            self.set_gradient = True
        else:
            self.set_gradient = False

    def stop_gradient_check(self,status):
        '''
        Cambia el valor del flag stop_gradient al marcar la casilla correspondiente
        '''
        if status == QtCore.Qt.Checked:
            self.stop_gradient = True
        else:
            self.stop_gradient = False
       
    def update_grad(self,data):
        '''
        Funcion para actualizar con los ultimos valores obtenidos del gradiente mientras estabiliza
        '''
        # Actualizo las listas con los resultados obtenidos mientras se estabiliza el gradiente
        self.initial_gradient.append(data[0])
        self.initial_heater_curr.append(data[1])     
        self.tiempo.append(data[2])     
   
        # Escribo los ultimos resultados en las casillas correspondientes en el GUI
        self.ui.lineEdit_13.setText(self._translate("MainWindow", "{:.2f}".format(self.initial_gradient[-1])))
        self.ui.lineEdit_15.setText(self._translate("MainWindow", "{:.2f}".format(self.initial_heater_curr[-1])))

        #Grafico
        self.curve2.setData(self.tiempo,self.initial_gradient)
          
           
    def update(self,data):
        '''
        Funcion para actualizar con los ultimos valores obtenidos de las mediciones
        '''
        # Actualizo las listas con los resultados obtenidos
        if self.from_zero:
                      
            self.voltage.append(data[0])        
            self.resistance.append(data[1])
            self.gradient.append(data[2])        
            self.temperature.append(data[3])
            self.heater_curr.append(data[4])
            self.resistance_std.append(data[5])
            
            # Escribo los ultimos resultados en las casillas correspondientes en el GUI
            self.ui.lineEdit_10.setText(self._translate("MainWindow", "{:.2f} {} {:.2f}".format(self.resistance[-1],u"\u00B1",self.resistance_std[-1])))
            self.ui.lineEdit_11.setText(self._translate("MainWindow", "{:.3f}".format(self.voltage[-1])))
            self.ui.lineEdit_13.setText(self._translate("MainWindow", "{:.2f}".format(self.gradient[-1])))
            self.ui.lineEdit_15.setText(self._translate("MainWindow", "{:.2f}".format(self.heater_curr[-1])))
            self.ui.lineEdit_18.setText(self._translate("MainWindow", "{:.2f}".format(self.temperature[-1])))

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
#                self.curve2.setData(self.tiempo,self.gradient) #solucionar agregar el gradiente en la curva 2
                if self.save and self.running_state:
                    self.f = open(self.path + '/{}'.format(self.param['name']),'a+')
                    self.f.write('{},{},{},{},{},{}\n'.format(data[0],data[1],data[2],data[3],data[4],data[5]))     
                    self.f.close()

        elif self.measure:
            
            self.voltage.append(data[0])        
            self.resistance.append(data[1])
            self.gradient.append(data[2])        
            self.temperature.append(data[3])
            self.heater_curr.append(data[4])
            self.resistance_std.append(data[5])
            
            # Escribo los ultimos resultados en las casillas correspondientes en el GUI
            self.ui.lineEdit_10.setText(self._translate("MainWindow", "{:.2f} {} {:.2f}".format(self.resistance[-1],u"\u00B1",self.resistance_std[-1])))
            self.ui.lineEdit_11.setText(self._translate("MainWindow", "{:.3f}".format(self.voltage[-1])))
            self.ui.lineEdit_13.setText(self._translate("MainWindow", "{:.2f}".format(self.gradient[-1])))
            self.ui.lineEdit_15.setText(self._translate("MainWindow", "{:.2f}".format(self.heater_curr[-1])))
            self.ui.lineEdit_18.setText(self._translate("MainWindow", "{:.2f}".format(self.temperature[-1])))
            
            # Si tengo la calibracion, grafico y guardo la resistencia y el valor del campo
            if self.calibration: #solucionar copiar lo mismo que sin calibracion
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
                self.curve.setData(self.voltage,self.resistance,self.gradient,self.temperature,self.heater_curr,self.resistance_std)
                if self.save and self.running_state:
                    self.f = open(self.path + '/{}'.format(self.param['name']),'a+')
                    self.f.write('{},{},{},{},{},{}\n'.format(data[0],data[1],data[2],data[3],data[4],data[5]))  
                    self.f.close()
        
    def user_stop(self):
        '''
        Funcion para detener la medicion. Envia señal al WorkingThread para detener a la fuente
        de corriente y enviar el campo a cero. Cambia el flag running_state a False.
        '''
        self.worker.stop()
        print('Pare el thread')
        self.running_state = False
#        if self.save:
#            self.f.close()
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "User stop / Decreasing field"))

        
    def end(self):
        '''
        Al concluir la medicion se ejecuta esta función automáticamente. Cierra el archivo de guardado
        y cambia el flag running_state a False
        '''
        self.running_state = False
#        if self.save:
#            self.f.close()
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Finished / Decreasing field"))

    def field_ready(self):
        '''
        Change the status windows when the field decreased to 0
        '''
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Field = 0 / Ready"))   
        self.ui.pushButton.setEnabled(True)
        self.ui.pushButton_2.setEnabled(False)       
        
    def gradient_ready(self):
        '''
        Change the status windows when the gradient is stabilizing
        '''
#        initial_time = time.time()
#        while (time.time() - initial_time < time_stab):
#            rest = time_stab - (time.time() - initial_time)
#            self.ui.lineEdit_9.setText(self._translate("MainWindow", "Stabilizing ","%.0f" %rest))
        self.ui.lineEdit_10.setText(self._translate("MainWindow", "Gradient Ready"))
        
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
        self.resistance_std = []
        self.field = []
        self.gradient = []
        self.temperature = []
        self.heater_curr = []
        self.initial_heater_curr = []
        self.initial_gradient = []
        self.tiempo = []
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
        self.param = {#'current_mA': float(self.ui.lineEdit.text()),
                      'deltaT' : float(self.ui.lineEdit_17.text()),
                      'Imin' : float(self.ui.lineEdit_19.text()),
                      'Istep' : float(self.ui.lineEdit_22.text()),
                      'stab_time' : float(self.ui.lineEdit_24.text()),
                      'samples': int(self.ui.lineEdit_7.text()),
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
                self.f.write('Campo(G),Señal(muV),Gradiente(K),Temperatura(K),Corriente(mA)\n')
            else:
                self.f.write('Voltaje(V),Señal(muV),Gradiente(K),Temperatura(K),Corriente(mA),Señal_std(muV)\n')
            self.f.close()
        # Llamo al Thread Worker        
        self.worker = Worker(self.param)
        # Conecto la señales del Thread con las funciones correspondientes
        self.worker.signals.result.connect(self.update)
        self.worker.signals.result2.connect(self.update_grad)
        self.worker.signals.finished.connect(self.end)
        self.worker.signals.max_field.connect(self.max_f)
        self.worker.signals.zero_field.connect(self.field_ready)
        self.worker.signals.gradient_reached.connect(self.gradient_ready)
        # Inicio el Thread
        self.threadpool.start(self.worker) 
        self.ui.lineEdit_9.setText(self._translate("MainWindow", "Running"))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    application = mywindow()
    application.show()
    sys.exit(app.exec_())
    