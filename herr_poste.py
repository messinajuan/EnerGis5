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
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QColor
from qgis.gui import QgsMapTool
from qgis.core import QgsRectangle, QgsFeatureRequest, QgsVectorLayer, QgsFeature
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrPoste(QgsMapTool):

    def __init__(self, iface, mapCanvas, conn, tension):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas    
        self.conn = conn
        self.tension = tension
        self.zona = 0
        self.nodos_temp = QgsVectorLayer()
        #QMessageBox.information(None, 'herrNodo', str(tension))

        self.rb = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PointGeometry)
        self.rb.setStrokeColor(QColor('Purple'))
        self.rb.setWidth(2.0)

        #arranco con un snap y despues paso a otro
        self.snapIndicator = QgsSnapIndicator(self.mapCanvas)
        self.snapper = QgsMapCanvasSnappingUtils(self.mapCanvas)
        config = QgsSnappingConfig()
        config.setEnabled(True)
        config.setType(QgsSnappingConfig.VertexAndSegment)
        config.setUnits(QgsTolerance.Pixels)
        config.setTolerance(12)
        config.setMode(2)
        self.snapper.setConfig(config)

        pass

    def keyPressEvent(self, event):
        #QMessageBox.information(None, "Mensaje", str(event.key()))
        if str(event.key()) == '16777249':
            self.tecla = 'Ctrl'
            #QMessageBox.information(None, "Mensaje", str(event.key()))
            pass
            
    def keyReleaseEvent(self, event):
        #QMessageBox.information(None, "Mensaje", tecla)
        self.tecla = ''
        
    def canvasPressEvent(self, event):
        point = self.point
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]

        for lyr in layers:
            if lyr.name() == 'Areas':
                width = 1 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    self.zona = ftr.id()

        for lyr in layers:
            #primero nos fijamos si hay una linea abajo, a ver si insertamos
            self.elmt_asociado=''
            if lyr.name()[:5] == 'Nodos':
                width = 2 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)                
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    self.crearPoste(point, '1', ftr.id())
                    return

            if lyr.name()[:6] == 'Postes':
                width = 2 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    QMessageBox.information(None, 'EnerGis 5', 'Ya hay un poste en esa posición')
                    return

            if lyr.name()[:6] == 'Lineas':
                width = 4 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    self.crearPoste(point, '2', ftr.id())
                    return

        self.crearPoste(point, '0', 0)
        pass

    def canvasMoveEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)

        snapMatch = self.snapper.snapToMap(event.pos())
        self.snapIndicator.setMatch(snapMatch)
        if str(self.snapIndicator.match().point())!='<QgsPointXY: POINT EMPTY>':
            #QMessageBox.information(None, "Mensaje", str(self.snapIndicator.match().point()))
            self.point = self.snapIndicator.match().point()

    def crearPoste(self, point, elemento_asociado, geoname_asociado):
        #QMessageBox.information(None, "Mensaje", str(elemento_asociado))
        b_existe = False
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyrCRS = lyr.crs().authid()
            if lyr.name() == 'Nodos_Temp':
                b_existe = True
                self.nodos_temp = lyr

        if b_existe == False:
            self.nodos_temp = QgsVectorLayer("Point?crs=" + lyrCRS, "Nodos_Temp", "memory")
            QgsProject.instance().addMapLayer(self.nodos_temp)
            self.nodos_temp.renderer().symbol().setSize(1)
            self.nodos_temp.renderer().symbol().setColor(QColor("black"))

        nodos_temp_data = self.nodos_temp.dataProvider()
        pt = QgsGeometry.fromPointXY(point)
        ftr = QgsFeature()
        ftr.setGeometry(pt)
        nodos_temp_data.addFeatures([ftr])
        self.nodos_temp.triggerRepaint()

        from .frm_postes import frmPostes
        self.dialogo = frmPostes(self.mapCanvas, self.conn, self.tension, 0, elemento_asociado, geoname_asociado, self.zona)
        self.dialogo.show()

