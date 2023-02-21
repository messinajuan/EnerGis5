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

class herrAgregarVertice(QgsMapTool):
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
        config.setType(QgsSnappingConfig.VertexAndSegment)
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
                width = 1 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)                
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    geom = ftr.geometry()
                    #QMessageBox.information(None, '', geom.asWkt())
                    g = self.agregar_vertice(geom, point, 1)
                    cnn = self.conn
                    cursor = cnn.cursor()
                    cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
                    rows = cursor.fetchall()
                    cursor.close()
                    srid = rows[0][0]
                    cursor = cnn.cursor()
                    cursor.execute("UPDATE Lineas SET obj = geometry::STGeomFromText(" + "'" + g.asWkt() + "'," + srid + ")  WHERE geoname=" + str(ftr.id()))
                    cnn.commit()
                    QMessageBox.information(None, 'Energis 5', 'Vertice Agregado')
                    self.habilitar_snap()
                    return

            if lyr.name() == 'Areas':
                width = 1 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    geom = ftr.geometry()
                    QMessageBox.information(None, '', geom.asWkt())
                    g = self.agregar_vertice(geom, point, 1)
                    cnn = self.conn
                    cursor = cnn.cursor()
                    cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
                    rows = cursor.fetchall()
                    cursor.close()
                    srid = rows[0][0]
                    cursor = cnn.cursor()
                    cursor.execute("UPDATE Areas SET obj = geometry::STGeomFromText(" + "'" + g.asWkt() + "'," + srid + ")  WHERE geoname=" + str(ftr.id()))
                    cnn.commit()
                    QMessageBox.information(None, 'Energis 5', 'Vertice Agregado')
                    self.habilitar_snap()
                    return

            if lyr.name() == 'Parcelas':
                width = 1 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    geom = ftr.geometry()
                    QMessageBox.information(None, '', geom.asWkt())
                    g = self.agregar_vertice(geom, point, 1)
                    cnn = self.conn
                    cursor = cnn.cursor()
                    cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
                    rows = cursor.fetchall()
                    cursor.close()
                    srid = rows[0][0]
                    cursor = cnn.cursor()
                    cursor.execute("UPDATE Parcelas SET obj = geometry::STGeomFromText(" + "'" + g.asWkt() + "'," + srid + ")  WHERE geoname=" + str(ftr.id()))
                    cnn.commit()
                    QMessageBox.information(None, 'Energis 5', 'Vertice Agregado')
                    self.habilitar_snap()
                    return
            pass

    def agregar_vertice(self, geom, point, tolerancia):
        p1, at, b1, after, d1 = geom.closestVertex(point)
        dist, p2, segmento, s = geom.closestSegmentWithContext(point)
        if at == 0:
            if dist < tolerancia:
                # insert into first segment
                geom.insertVertex(point.x(), point.y(), after)
            else:
                # insert before first vertex
                geom.insertVertex(point.x(), point.y(), 0)
        elif after == -1:
            if dist < tolerancia:
                # insert after last vertex
                geom.insertVertex(point.x(), point.y(), at)
            else:
                # insert into last segment
                last = geom.vertexAt(at)
                geom.moveVertex(point.x(), point.y(), at)
                geom.insertVertex(last.x(), last.y(), at)
        else:
            # insert into any other segment
            geom.insertVertex(point.x(), point.y(), segmento)
        return geom
