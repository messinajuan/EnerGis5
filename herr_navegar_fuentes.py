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

from .mod_navegacion import navegar_a_las_fuentes
from PyQt5.QtWidgets import QMessageBox
from qgis.gui import QgsMapTool
from qgis.core import  QgsMapLayerType
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrNavegarFuentes(QgsMapTool):

    def __init__(self, iface, mapCanvas, conn, nodo):
        QgsMapTool.__init__(self, mapCanvas)
        self.iface = iface
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.nodo = nodo

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
        #convierto el cursor en array
        self.mlineas = tuple(cursor)
        cursor.close()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
        #convierto el cursor en array
        self.mnodos = tuple(cursor)
        cursor.close()
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                lyr.removeSelection()
        #--------------------------------------------
        navegar_a_las_fuentes(self, self.mnodos, self.mlineas, self.nodo)
        #--------------------------------------------
        self.seleccion_n = []
        for n in range(1, len(self.mnodos)):
            if self.mnodos[n][45] == 1:
                self.seleccion_n.append(self.mnodos[n][1])
        self.seleccion_l = []
        for n in range (1, len(self.mlineas)):
            if self.mlineas[n][12] == 1:
                self.seleccion_l.append(self.mlineas[n][1])
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText('Análisis de la Red')
        msg.setInformativeText('Búsqueda de Fuentes')
        msg.setWindowTitle('EnerGis 5')
        msg.setDetailedText(str(len(self.seleccion_l)) + ' lineas marcadas')
        retval = msg.exec_()
        if len(self.seleccion_l)==0:
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
