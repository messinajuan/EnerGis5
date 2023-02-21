# encoding: utf-8
#-----------------------------------------------------------
# Copyright (C) 2018 Juan Messina
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

from .mod_navegacion import navegar_a_las_fuentes, navegar_compilar_red
from PyQt5.QtWidgets import QMessageBox
from qgis.gui import QgsMapTool
from qgis.core import QgsMapLayerType
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrNavegarExtremos(QgsMapTool):

    def __init__(self, iface, mapCanvas, conn, nodo):
        QgsMapTool.__init__(self, mapCanvas)
        self.iface = iface
        self.mapCanvas = mapCanvas    
        self.conn = conn
        self.nodo = nodo

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
        #convierto el cursor en array
        self.mnodos = tuple(cursor)
        cursor.close()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
        #convierto el cursor en array
        self.mlineas = tuple(cursor)
        cursor.close()
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                lyr.removeSelection()
        for n in range (0, len(self.mnodos)):
            if self.mnodos[n][1]==self.nodo:
                nodo_desde = self.mnodos[n][0]
                n = len(self.mnodos)
        #QMessageBox.information(None, 'Fuente', 'Nodo desde : ' + str(nodo_desde))
        #--------------------------------------------
        navegar_a_las_fuentes(self, self.mnodos, self.mlineas, self.nodo)
        #--------------------------------------------
        #el resultado es lo que tengo que anular
        lineas_anuladas=[]
        #anulo los caminos a las fuentes
        for n in range (0, len(self.mlineas)):
            if self.mlineas[n][2]==nodo_desde or self.mlineas[n][3]==nodo_desde:
                if self.mlineas[n][12]==1:
                    #QMessageBox.information(None, 'Fuente', 'Al nodo llega de la fuente la linea geoname: ' + str(self.mlineas[n][0]))
                    lineas_anuladas.append(self.mlineas[n][0])
                    self.mlineas[n][1]=0
        #QMessageBox.information(None, 'Fuente', str(self.mnodos[nodo_desde][0]) + ' | ' + str(self.mnodos[nodo_desde][1]) + ' | ' + str(self.mnodos[nodo_desde][2]) + ' | ' + str(self.mnodos[nodo_desde][3]) + ' | ' + str(self.mnodos[nodo_desde][4]) + ' | ' + str(self.mnodos[nodo_desde][5]) + ' | ' + str(self.mnodos[nodo_desde][6]) + ' | ' + str(self.mnodos[nodo_desde][7]))
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
        #convierto el cursor en array
        self.mnodos = tuple(cursor)
        cursor.close()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
        #convierto el cursor en array
        self.mlineas = tuple(cursor)
        cursor.close()
        #QMessageBox.information(None, 'Fuente', str(self.mnodos[nodo_desde][0]) + ' | ' + str(self.mnodos[nodo_desde][1]) + ' | ' + str(self.mnodos[nodo_desde][2]) + ' | ' + str(self.mnodos[nodo_desde][3]) + ' | ' + str(self.mnodos[nodo_desde][4]) + ' | ' + str(self.mnodos[nodo_desde][5]) + ' | ' + str(self.mnodos[nodo_desde][6]) + ' | ' + str(self.mnodos[nodo_desde][7]))
        for n in range (0, len(lineas_anuladas)):
            #QMessageBox.information(None, 'Fuente', 'linea anulada')
            #busco en que casillero tengo la linea y anulo esos proximos nodos en el nodo que estoy navegando
            for i in range (5, 37):
                if self.mnodos[nodo_desde][i]==lineas_anuladas[n]:
                    #QMessageBox.information(None, 'Fuente', 'A linea id : ' + str(self.mnodos[nodo_desde][i]))
                    self.mnodos[nodo_desde][4]=self.mnodos[nodo_desde][4]-1
                    #QMessageBox.information(None, 'Fuente', '-> la borro')
                    for j in range (i, 36):
                        self.mnodos[nodo_desde][j]=self.mnodos[nodo_desde][j+1]
                    i=37
        for n in range(0, len(self.mnodos)):
            self.mnodos[n][3] = 0
        for n in range (0, len(self.mlineas)):
            self.mlineas[n][4] = 0
        self.monodos = [0] * len(self.mnodos) #valores cero de longitud igual a mnodos
        #QMessageBox.information(None, 'Fuente', str(self.mnodos[nodo_desde][0]) + ' | ' + str(self.mnodos[nodo_desde][1]) + ' | ' + str(self.mnodos[nodo_desde][2]) + ' | ' + str(self.mnodos[nodo_desde][3]) + ' | ' + str(self.mnodos[nodo_desde][4]) + ' | ' + str(self.mnodos[nodo_desde][5]) + ' | ' + str(self.mnodos[nodo_desde][6]) + ' | ' + str(self.mnodos[nodo_desde][7]))
        navegar_compilar_red(self, self.mnodos, self.mlineas, self.monodos, nodo_desde)
        #QMessageBox.information(None, 'EnerGis 5', 'Navegado')
        self.seleccion_n = []
        for m in range(1, len(self.mnodos)):
            if self.mnodos[m][3] != 0:
                self.seleccion_n.append(self.mnodos[m][1])
        nodos_navegados=len(self.seleccion_n)
        self.seleccion_l = []
        for n in range (1, len(self.mlineas)):
            if self.mlineas[n][4] != 0:
                self.seleccion_l.append(self.mlineas[n][1])
        lineas_navegadas=len(self.seleccion_l)
        if lineas_navegadas==0:
            return
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText('Análisis de la Red')
        msg.setInformativeText('Navegar a los Extremos')
        msg.setWindowTitle('EnerGis 5')
        msg.setDetailedText(str(nodos_navegados) + ' nodos, ' + str(lineas_navegadas) + ', lineas')
        retval = msg.exec_()
        if nodos_navegados==0 and lineas_navegadas==0:
            return
        retval = self.h_elementos_seleccionados()
        pass

    def h_elementos_seleccionados(self):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Temp':
                lyr.select(self.seleccion_n)
            if lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Temp':
                lyr.select(self.seleccion_l)
        #from .frm_seleccion import frmSeleccion
        #self.dialogo = frmSeleccion(self.mapCanvas)
        #self.dialogo.show()
        pass
