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

from PyQt5 import QtCore
#from PyQt5.QtWidgets import QMessageBox
from qgis.gui import QgsMapTool
from qgis.core import QgsVectorLayer
from qgis.core import QgsPoint
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrRotar(QgsMapTool):

    def __init__(self, iface, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.iface = iface
        self.mapCanvas = mapCanvas    
        self.conn = conn
        self.p1 = QgsPoint()
        self.ftrs_nodos = []
        self.ftrs_lineas = []
        self.ftrs_postes = []
        self.ftrs_areas = []
        self.ftrs_parcelas = []
        self.angulo = 0
        self.nodos_temp = QgsVectorLayer()

        n = mapCanvas.layerCount()
        layers = [mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Temp':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_nodos.append(ftr.id())
            if lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Temp':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_lineas.append(ftr.id())
            if lyr.name()[:6] == 'Postes':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_postes.append(ftr.id())
            if lyr.name() == 'Areas':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_areas.append(ftr.id())
            if lyr.name() == 'Parcelas':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_parcelas.append(ftr.id())
        pass
                   
    def canvasPressEvent(self, event):
        #Get the click
        x = event.pos().x()
        y = event.pos().y()
        point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        
        self.pc = QgsPoint(point.x(), point.y())

        if len(self.ftrs_nodos) > 0 or len(self.ftrs_lineas) or len(self.ftrs_postes) or len(self.ftrs_areas) or len(self.ftrs_parcelas) > 0:
            from .frm_rotar import frmRotar
            self.dialogo = frmRotar(self.mapCanvas, self.conn, self.ftrs_nodos, self.ftrs_lineas, self.ftrs_postes, self.ftrs_areas, self.ftrs_parcelas, self.pc)
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & QtCore.Qt.CustomizeWindowHint)
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint)
            self.dialogo.show()
        pass
