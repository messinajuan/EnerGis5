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
from qgis.core import QgsSnappingConfig, QgsWkbTypes, QgsTolerance
from qgis.gui import QgsMapCanvasSnappingUtils, QgsSnapIndicator, QgsRubberBand
#from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QColor
from qgis.gui import QgsMapTool
from qgis.core import QgsPoint, QgsVectorLayer, QgsFeature, QgsMapLayerType
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrArea(QgsMapTool):
    def __init__(self, iface, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.iface = iface
        self.mapCanvas = mapCanvas
        self.conn = conn        
        self.tecla=''
        self.puntos = []
        self.areas_temp = QgsVectorLayer()
        self.nodos_temp = QgsVectorLayer()

        self.rb = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PointGeometry)
        self.rb.setStrokeColor(QColor('Purple'))
        self.rb.setWidth(2.0)

        self.habilitar_snap()

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
            self.areas_temp.renderer().symbol().setColor(QColor("blue"))

    def habilitar_snap(self):
        self.snapIndicator = QgsSnapIndicator(self.mapCanvas)
        self.snapper = QgsMapCanvasSnappingUtils(self.mapCanvas)
        config = QgsSnappingConfig()
        config.setEnabled(True)
        config.setType(QgsSnappingConfig.VertexAndSegment)
        config.setUnits(QgsTolerance.Pixels)
        config.setTolerance(12)
        config.setMode(2)
        self.snapper.setConfig(config)

    def keyPressEvent(self, event):
        if str(event.key()) == '16777249':
            self.tecla = 'Ctrl'
            #QMessageBox.information(None, "Mensaje", str(event.key()))
            pass
        if str(event.key()) == '16777216':
            self.tecla = 'Esc'
            #QMessageBox.information(None, "Mensaje", str(event.key()))

            self.puntos = []
            #borra todos los objetos de la capa
            if not self.areas_temp.isEditable():
                self.areas_temp.startEditing()
            listOfIds = [feat.id() for feat in self.areas_temp.getFeatures()]
            self.areas_temp.deleteFeatures(listOfIds)
            self.areas_temp.commitChanges()
            #----------------------------------
            pass
            
    def keyReleaseEvent(self, event):
        #QMessageBox.information(None, "Mensaje", tecla)
        self.tecla = ''
        pass
        
    def canvasPressEvent(self, event):
        self.puntos.append(QgsPoint(self.point.x(),self.point.y()))
        if len(self.puntos)>0:
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
        self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)

        snapMatch = self.snapper.snapToMap(event.pos())
        self.snapIndicator.setMatch(snapMatch)
        if str(self.snapIndicator.match().point())!='<QgsPointXY: POINT EMPTY>':
            #QMessageBox.information(None, "Mensaje", str(self.snapIndicator.match().point()))
            self.point = self.snapIndicator.match().point()

        if len(self.puntos)>0:
            self.puntos.append(QgsPoint(self.point.x(),self.point.y()))
            pts = QgsGeometry.fromPolyline(self.puntos)
            str_pts = pts.asWkt()
            str_pts = str_pts.replace("LineString ","Polygon (") + ")"
            ftrArea = QgsFeature()
            ftrArea.setGeometry(QgsGeometry.fromWkt(str_pts))
            self.limpiar_areas_temp()
            areas_temp_data = self.areas_temp.dataProvider()
            areas_temp_data.addFeatures([ftrArea])
            self.areas_temp.triggerRepaint()
            self.puntos.pop()
        pass

    def limpiar_areas_temp(self):
        listOfIds = [feat.id() for feat in self.areas_temp.getFeatures()]
        if not self.areas_temp.isEditable():
            self.areas_temp.startEditing()
        self.areas_temp.deleteFeatures(listOfIds)
        self.areas_temp.commitChanges()
        pass

    def canvasDoubleClickEvent(self, event):
        #x = event.pos().x()
        #y = event.pos().y()
        #point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                lyr.removeSelection()

        #puntos.append(QgsPoint(point.x(),point.y()))
        self.puntos.append(self.puntos[0])

        pts = QgsGeometry.fromPolyline(self.puntos)
        str_pts = pts.asWkt()
        str_pts = str_pts.replace("LineString ","Polygon (") + ")"
        self.ftrArea = QgsFeature()
        self.ftrArea.setGeometry(QgsGeometry.fromWkt(str_pts))
        areas_temp_data = self.areas_temp.dataProvider()
        areas_temp_data.addFeatures([self.ftrArea])
        self.areas_temp.triggerRepaint()
        #borra todos los objetos de la capa
        if not self.areas_temp.isEditable():
            self.areas_temp.startEditing()
        listOfIds = [feat.id() for feat in self.areas_temp.getFeatures()]
        self.areas_temp.deleteFeatures(listOfIds)
        self.areas_temp.commitChanges()
        #----------------------------------
        #QMessageBox.information(None, 'EnerGis 5', 'Tengo la Region ' + str(ftrArea.geometry().asWkt()))
        #QMessageBox.information(None, 'EnerGis 5', 'Tengo la Region ' + str(self.puntos))
        self.puntos=[]
        self.crearArea()
        self.habilitar_snap()
        pass

    def crearArea(self):
        from .frm_areas import frmAreas
        self.dialogo = frmAreas(self.mapCanvas, self.conn, self.ftrArea, 0)
        self.dialogo.show()
        pass
