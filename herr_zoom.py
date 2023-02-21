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

from qgis.core import QgsProject, QgsGeometry
#from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QColor
from qgis.gui import QgsMapTool
from qgis.core import QgsRectangle, QgsVectorLayer, QgsFeature
from qgis.core import QgsPoint, QgsPointXY
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrZoom(QgsMapTool):

    def __init__(self, iface, mapCanvas, herramienta):
        QgsMapTool.__init__(self, mapCanvas)
        self.iface = iface
        self.mapCanvas = mapCanvas    
        self.herramienta = herramienta
        
        self.ancho = 0
        self.alto = 0
        self.pcentro = QgsPointXY()
        
        self.p1 = QgsPoint()
        self.p2 = QgsPoint()

        self.areas_temp = QgsVectorLayer()
       
        n = self.mapCanvas.layerCount()
        b_existe = False
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyrCRS = lyr.crs().authid()
                return
            if lyr.name() == 'Areas_Temp':
                b_existe = True
                self.areas_temp = lyr
                return

        if b_existe == False:
            self.areas_temp = QgsVectorLayer("Polygon?crs=" + lyrCRS, "Areas_Temp", "memory")
            QgsProject.instance().addMapLayer(self.areas_temp)
            self.areas_temp.renderer().symbol().setOpacity(0.15)
            self.areas_temp.renderer().symbol().setColor(QColor("red"))
        pass
        
    def canvasPressEvent(self, event):
        if event.button() == 1: #Boton izquierdo
            #Get the click
            x = event.pos().x()
            y = event.pos().y()
            self.p1 = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
            if self.herramienta == 'Pan':
                self.herramienta = 'Pon'
                return
            if self.herramienta == 'ZoomOut':
                self.mapCanvas.zoomOut()
                self.p1 = QgsPoint()
                self.p2 = QgsPoint()
                return

    def canvasMoveEvent(self, event):
        if self.herramienta == 'ZoomOut':
            return
        if str(self.p1)=='<QgsPoint: Point EMPTY>':
            return
        #Get the click
        x = event.pos().x()
        y = event.pos().y()
        self.p2 = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)

        if self.herramienta == 'Pon':
            e = self.iface.mapCanvas().extent()
            self.ancho = abs(e.xMaximum() - e.xMinimum())
            self.alto = abs(e.yMaximum() - e.yMinimum())
            xcentro = e.xMinimum() + (e.xMaximum() - e.xMinimum()) / 2
            ycentro = e.yMinimum() + (e.yMaximum() - e.yMinimum()) / 2            
            self.pcentro = QgsPointXY(xcentro, ycentro)

            #p3 es el nuevo centro del mapa, o sea el centro inicial + lo que se desplazó el mouse (p2 - p1)
            x3 = self.pcentro.x() - self.p2.x() + self.p1.x()
            y3 = self.pcentro.y() - self.p2.y() + self.p1.y()
            
            self.p3 = QgsPointXY(x3, y3)
            self.mapCanvas.setCenter(self.p3)
            self.mapCanvas.refresh()
            return

        rect = QgsRectangle(self.p1.x(), self.p1.y(), self.p2.x(), self.p2.y())

        self.limpiar_areas_temp()
        ftrArea = QgsFeature()
        ftrArea.setGeometry(QgsGeometry.fromRect(rect))
        areas_temp_data = self.areas_temp.dataProvider()
        areas_temp_data.addFeatures([ftrArea])
        self.areas_temp.triggerRepaint()

        pass

    def limpiar_areas_temp(self):
        listOfIds = [feat.id() for feat in self.areas_temp.getFeatures()]
        if not self.areas_temp.isEditable():
            self.areas_temp.startEditing()
        self.areas_temp.deleteFeatures(listOfIds)
        self.areas_temp.commitChanges()
        pass

    def canvasReleaseEvent(self, event):
        if self.herramienta == 'ZoomOut':
            return
        if self.herramienta == 'Pon':
            self.mapCanvas.refresh()
            self.p1 = QgsPoint()
            self.p2 = QgsPoint()
            self.herramienta = 'Pan'
            return
        if self.p2.x() == self.p1.x() or self.p2.y() == self.p1.y() or self.p2.x()==0:
            if self.herramienta == 'ZoomIn':
                self.mapCanvas.zoomIn()
                self.p1 = QgsPoint()
                self.p2 = QgsPoint()
                return

        #Get the click
        x = event.pos().x()
        y = event.pos().y()
        self.p2 = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)

        self.limpiar_areas_temp()

        rect = QgsRectangle(self.p1.x(), self.p1.y(), self.p2.x(), self.p2.y())
        ftrArea = QgsFeature()
        ftrArea.setGeometry(QgsGeometry.fromRect(rect))

        self.mapCanvas.setExtent(rect)
        self.mapCanvas.refresh()

        self.p1 = QgsPoint()
        self.p2 = QgsPoint()
        pass
