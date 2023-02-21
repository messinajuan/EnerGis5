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

from qgis.core import QgsProject, QgsGeometry, QgsMapLayerType
#from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QColor
from qgis.gui import QgsMapTool
from qgis.core import QgsVectorLayer, QgsFeature, QgsPoint
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrSeleccionAleatoria(QgsMapTool):

    def __init__(self, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas    
        self.conn = conn
        self.areas_temp = QgsVectorLayer()
        self.puntos = []

        n = self.mapCanvas.layerCount()
        b_existe = False
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyrCRS = lyr.crs().authid()
            if lyr.name() == 'Areas_Temp':
                b_existe = True
                self.areas_temp = lyr

        if b_existe == False:
            self.areas_temp = QgsVectorLayer("Polygon?crs=" + lyrCRS, "Areas_Temp", "memory")
            QgsProject.instance().addMapLayer(self.areas_temp)
            self.areas_temp.renderer().symbol().setOpacity(0.15)
            self.areas_temp.renderer().symbol().setColor(QColor("red"))
        pass
        
    def keyPressEvent(self, event):

        if str(event.key()) == '16777249':
            #tecla = 'Ctrl'
            #QMessageBox.information(None, "Mensaje", str(event.key()))
            pass
        if str(event.key()) == '16777216':
            #tecla = 'Esc'
            #QMessageBox.information(None, "Mensaje", str(event.key()))
            self.puntos = []
            self.limpiar_areas_temp()
            pass

    def limpiar_areas_temp(self):
        if not self.areas_temp.isEditable():
            self.areas_temp.startEditing()
        listOfIds = [feat.id() for feat in self.areas_temp.getFeatures()]
        self.areas_temp.deleteFeatures(listOfIds)
        self.areas_temp.commitChanges()
        pass
        
    def canvasPressEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        self.puntos.append(QgsPoint(point.x(),point.y()))
        pts = QgsGeometry.fromPolyline(self.puntos)
        str_pts = pts.asWkt()
        str_pts = str_pts.replace("LineString ","Polygon (") + ")"
        ftrArea = QgsFeature()
        ftrArea.setGeometry(QgsGeometry.fromWkt(str_pts))
        areas_temp_data = self.areas_temp.dataProvider()
        areas_temp_data.addFeatures([ftrArea])
        self.areas_temp.triggerRepaint()
        return

    def canvasMoveEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        if len(self.puntos)==0:
            return    
        self.limpiar_areas_temp()
        self.puntos.append(QgsPoint(point.x(),point.y()))
        pts = QgsGeometry.fromPolyline(self.puntos)
        str_pts = pts.asWkt()
        str_pts = str_pts.replace("LineString ","Polygon (") + ")"
        ftrArea = QgsFeature()
        ftrArea.setGeometry(QgsGeometry.fromWkt(str_pts))
        areas_temp_data = self.areas_temp.dataProvider()
        areas_temp_data.addFeatures([ftrArea])
        self.areas_temp.triggerRepaint()
        self.puntos.pop()
        pass
        
    def canvasReleaseEvent(self, event):
        #x = event.pos().x()
        #y = event.pos().y()
        #point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        pass

    def canvasDoubleClickEvent(self, event):
        #x = event.pos().x()
        #y = event.pos().y()
        #point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        self.seleccion_n = []
        self.seleccion_l = []
        self.seleccion_p = []
        self.seleccion_a = []
        self.seleccion_c = []
        self.seleccion_e = []

        #puntos.append(QgsPoint(point.x(),point.y()))
        self.puntos.append(self.puntos[0])
        pts = QgsGeometry.fromPolyline(self.puntos)
        str_pts = pts.asWkt()
        str_pts = str_pts.replace("LineString ","Polygon (") + ")"
        #QMessageBox.information(None, 'EnerGis 5', 'Agrego la Region ' + str_pts)
        ftrArea = QgsFeature()
        ftrArea.setGeometry(QgsGeometry.fromWkt(str_pts))
        areas_temp_data = self.areas_temp.dataProvider()
        areas_temp_data.addFeatures([ftrArea])
        self.areas_temp.triggerRepaint()

        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                lyr.removeSelection()

                if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                    for ftr in lyr.getFeatures():
                        if ftrArea.geometry().intersects(ftr.geometry()):
                            self.seleccion_n.append(ftr.id())

                if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
                    for ftr in lyr.getFeatures():
                        if ftrArea.geometry().intersects(ftr.geometry()):
                            self.seleccion_l.append(ftr.id())

                if lyr.name()[:6] == 'Postes':
                    for ftr in lyr.getFeatures():
                        if ftrArea.geometry().intersects(ftr.geometry()):
                            self.seleccion_p.append(ftr.id())

                if lyr.name() == 'Areas':
                    for ftr in lyr.getFeatures():
                        if ftrArea.geometry().intersects(ftr.geometry()):
                            self.seleccion_a.append(ftr.id())

                if lyr.name() == 'Parcelas':
                    for ftr in lyr.getFeatures():
                        if ftrArea.geometry().intersects(ftr.geometry()):
                            self.seleccion_c.append(ftr.id())

                if lyr.name() == 'Ejes':
                    for ftr in lyr.getFeatures():
                        if ftrArea.geometry().intersects(ftr.geometry()):
                            self.seleccion_e.append(ftr.id())

        self.limpiar_areas_temp()
        #del puntos[:]
        self.puntos=[]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(self.seleccion_n)
            if lyr.name()[:6] == 'Lineas':
                lyr.select(self.seleccion_l)
            if lyr.name()[:6] == 'Postes':
                lyr.select(self.seleccion_p)
            if lyr.name() == 'Areas':
                lyr.select(self.seleccion_a)
            if lyr.name() == 'Parcelas':
                lyr.select(self.seleccion_c)
            if lyr.name() == 'Ejes':
                lyr.select(self.seleccion_e)
        return
