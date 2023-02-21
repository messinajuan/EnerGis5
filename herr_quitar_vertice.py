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

from qgis.core import QgsSnappingConfig, QgsWkbTypes, QgsTolerance
from qgis.gui import QgsMapCanvasSnappingUtils, QgsSnapIndicator, QgsRubberBand
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QColor
from qgis.gui import QgsMapTool
from qgis.core import QgsRectangle, QgsFeatureRequest
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrQuitarVertice(QgsMapTool):
    def __init__(self, iface, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas    
        self.conn = conn
        self.rb = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PointGeometry)
        self.rb.setStrokeColor(QColor('Purple'))
        self.rb.setWidth(2.0)
        self.habilitar_snap()
        pass

    def habilitar_snap(self):
        self.snapIndicator = QgsSnapIndicator(self.mapCanvas)
        self.snapper = QgsMapCanvasSnappingUtils(self.mapCanvas)
        config = QgsSnappingConfig()
        config.setEnabled(True)
        config.setType(QgsSnappingConfig.Vertex)
        config.setUnits(QgsTolerance.Pixels)
        config.setTolerance(12)
        config.setMode(2)
        self.snapper.setConfig(config)
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
        pass

    def canvasPressEvent(self, event):
        point=self.point
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            #primero nos fijamos si hay una linea abajo, a ver si insertamos
            if lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Temp':
                width = 0.01 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)                
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    reply = QMessageBox.question(None, 'EnerGis 5', 'Desea borrar el vértice?', QMessageBox.Yes, QMessageBox.No)
                    if reply == QMessageBox.No:
                        return
                    geom = ftr.geometry()
                    #QMessageBox.information(None, '', geom.asWkt())
                    g = self.quitar_vertice(geom, point, 0.01)
                    cnn = self.conn
                    cursor = cnn.cursor()
                    cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
                    rows = cursor.fetchall()
                    cursor.close()
                    srid = rows[0][0]
                    cursor = cnn.cursor()
                    cursor.execute("UPDATE Lineas SET obj = geometry::STGeomFromText(" + "'" + g.asWkt() + "'," + srid + ")  WHERE geoname=" + str(ftr.id()))
                    cnn.commit()
                    self.habilitar_snap()
                    lyr.triggerRepaint()
                    return
            if lyr.name() == 'Areas':
                width = 0.01 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    reply = QMessageBox.question(None, 'EnerGis 5', 'Desea borrar el vértice?', QMessageBox.Yes, QMessageBox.No)
                    if reply == QMessageBox.No:
                        return
                    geom = ftr.geometry()
                    #QMessageBox.information(None, '', geom.asWkt())
                    g = self.quitar_vertice(geom, point, 0.01)
                    cnn = self.conn
                    cursor = cnn.cursor()
                    cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
                    rows = cursor.fetchall()
                    cursor.close()
                    srid = rows[0][0]
                    cursor = cnn.cursor()
                    cursor.execute("UPDATE Areas SET obj = geometry::STGeomFromText(" + "'" + g.asWkt() + "'," + srid + ")  WHERE geoname=" + str(ftr.id()))
                    cnn.commit()
                    self.habilitar_snap()
                    lyr.triggerRepaint()
                    return
            if lyr.name() == 'Parcelas':
                width = 0.01 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    reply = QMessageBox.question(None, 'EnerGis 5', 'Desea borrar el vértice?', QMessageBox.Yes, QMessageBox.No)
                    if reply == QMessageBox.No:
                        return
                    geom = ftr.geometry()
                    #QMessageBox.information(None, '', geom.asWkt())
                    g = self.quitar_vertice(geom, point, 0.01)
                    cnn = self.conn
                    cursor = cnn.cursor()
                    cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
                    rows = cursor.fetchall()
                    cursor.close()
                    srid = rows[0][0]
                    cursor = cnn.cursor()
                    cursor.execute("UPDATE Parcelas SET obj = geometry::STGeomFromText(" + "'" + g.asWkt() + "'," + srid + ")  WHERE geoname=" + str(ftr.id()))
                    cnn.commit()
                    self.habilitar_snap()
                    lyr.triggerRepaint()
                    return
        pass

    def quitar_vertice(self, geom, point, tolerancia):
        punto1, at, b1, after, d1 = geom.closestVertex(point)
        if at==0:
                pass
        elif after==-1:
                pass
        else:
            geom.deleteVertex(at)
        return geom
