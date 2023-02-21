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
from qgis.core import QgsSnappingConfig, QgsWkbTypes, QgsTolerance
from qgis.gui import QgsMapCanvasSnappingUtils, QgsSnapIndicator, QgsRubberBand
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from qgis.gui import QgsMapTool
from qgis.core import QgsRectangle, QgsFeatureRequest, QgsFeature, QgsMapLayerType
from qgis.core import QgsPoint
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrMover(QgsMapTool):

    def __init__(self, iface, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.iface = iface
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.p1 = QgsPoint()
        self.p2 = QgsPoint()
        self.ftrs_nodos = []
        self.ftrs_lineas = []
        self.ftrs_postes = []
        self.ftrs_areas = []
        self.ftrs_parcelas = []
        self.elmt=''

        self.rb = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PointGeometry)

        self.rb.reset(True)

        self.rb.setStrokeColor(QColor('Blue'))
        self.rb.setWidth(2)

        self.snapIndicator = QgsSnapIndicator(self.mapCanvas)
        self.snapper = QgsMapCanvasSnappingUtils(self.mapCanvas)

        self.habilitar_snap()

        #armo las colecciones de objetos a mover en grupo
        n = mapCanvas.layerCount()
        layers = [mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_nodos.append(ftr.id())
            if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
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
        if len(self.ftrs_nodos) + len(self.ftrs_lineas) + len(self.ftrs_areas) + len(self.ftrs_parcelas) > 0:
            self.tipo_herramienta='muchos'
            from .frm_mover import frmMover
            self.dialogo = frmMover(self.mapCanvas, self.conn, self.ftrs_nodos, self.ftrs_lineas, self.ftrs_postes, self.ftrs_areas, self.ftrs_parcelas)
            #self.dialogo.setWindowTitle('Simple')
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & QtCore.Qt.CustomizeWindowHint)
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint)
            self.dialogo.show()
        else:
            self.tipo_herramienta='uno'
        pass

    def habilitar_snap(self):
        config = QgsSnappingConfig()
        config.setEnabled(True)
        config.setType(QgsSnappingConfig.VertexAndSegment)
        config.setUnits(QgsTolerance.Pixels)
        config.setTolerance(12)
        config.setMode(2)
        self.snapper.setConfig(config)

    def deshabilitar_snap(self):
        config = QgsSnappingConfig()
        config.setEnabled(False)
        self.snapper.setConfig(config)

    def canvasPressEvent(self, event):
        if self.tipo_herramienta=='muchos':
            return
        if event.button() == Qt.RightButton:
            return
        self.elmt = ''
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                #QMessageBox.information(None, 'vertices', lyr.name())
                if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        self.ftr = ftr
                        p = QgsFeature()
                        p.setGeometry(geom)
                        self.p1 = QgsPoint(geom.asPoint().x(), geom.asPoint().y())
                        self.elmt = 'Nodo'
                        self.habilitar_snap()
                        return

                if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        self.ftr = ftr
                        vertices  = geom.asPolyline()
                        m = len(vertices)
                        #QMessageBox.information(None, 'vertices', str(m))
                        for i in range(m):
                            vertice=QgsPoint(vertices [i][0],vertices [i][1])
                            if abs(self.point.x()-vertices [i][0])<width and abs(self.point.y()-vertices [i][1])<width:
                                #QMessageBox.information(None, 'vertice', str(i))
                                v = QgsFeature()
                                v.setGeometry(vertice)
                                self.p1 = QgsPoint(vertice.x(), vertice.y())
                                self.elmt = 'Vertice ' + str(i)
                                self.habilitar_snap()
                                return

                if lyr.name()[:6] == 'Postes':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        self.ftr = ftr
                        p = QgsFeature()
                        p.setGeometry(geom)
                        self.p1 = QgsPoint(geom.asPoint().x(), geom.asPoint().y())
                        self.elmt = 'Poste'
                        self.habilitar_snap()
                        return

                if lyr.name() == 'Areas':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        self.ftr = ftr
                        poligono = geom.asPolygon()
                        n = len(poligono[0])
                        for i in range(n):
                            vertice=QgsPoint(poligono [0][i])
                            if abs(self.point.x()-vertice.x())<width and abs(self.point.y()-vertice.y())<width:
                                v = QgsFeature()
                                v.setGeometry(vertice)
                                self.p1 = QgsPoint(vertice.x(), vertice.y())
                                self.elmt = 'Oertice ' + str(i)
                                self.habilitar_snap()
                                return

                if lyr.name() == 'Parcelas':
                    width = 1 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        self.ftr = ftr
                        poligono = geom.asPolygon()
                        n = len(poligono[0])
                        for i in range(n):
                            vertice=QgsPoint(poligono [0][i])
                            if abs(self.point.x()-vertice.x())<width and abs(self.point.y()-vertice.y())<width:
                                v = QgsFeature()
                                v.setGeometry(vertice)
                                self.p1 = QgsPoint(vertice.x(), vertice.y())
                                self.elmt = 'Pertice ' + str(i)
                                self.habilitar_snap()
                                return
        pass

    def canvasMoveEvent(self, event):
        if self.tipo_herramienta=='muchos':
            return
        x = event.pos().x()
        y = event.pos().y()
        self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)

        snapMatch = self.snapper.snapToMap(event.pos())
        self.snapIndicator.setMatch(snapMatch)
        if str(self.snapIndicator.match().point())!='<QgsPointXY: POINT EMPTY>':
            #QMessageBox.information(None, "Mensaje", str(self.snapIndicator.match().point()))
            self.point = self.snapIndicator.match().point()
        pass

    def canvasReleaseEvent(self, event):
        if self.tipo_herramienta=='muchos':
            return
        if self.elmt=='':
            return
        self.p2 = QgsPoint(self.point.x(), self.point.y())
        self.dx = self.p2.x() - self.p1.x()
        self.dy = self.p2.y() - self.p1.y()

        #QMessageBox.information(None, 'EnerGis 5', self.elmt)
        if self.elmt=='Nodo':
            nodo = self.detecto_nodo(self.point)
            if nodo!=0:
                QMessageBox.information(None, 'EnerGis 5', 'Ya hay un nodo en esa posicion')
                return
            #linea = self.detecto_linea(self.point)
            #if linea!=0:
            #    QMessageBox.information(None, 'EnerGis 5', 'Ya hay una linea en esa posicion')
            #    return
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("mover_nodo " + str(self.ftr.id()) + ', ' + str(self.dx) + ', ' + str(self.dy))
            cnn.commit()
            zona = self.detecto_zona(self.point)
            if zona!=0:
                #QMessageBox.information(None, 'EnerGis 5', 'Tomo zona ' + str(zona))
                cnn = self.conn
                cursor = cnn.cursor()
                cursor.execute("SELECT nombre, descripcion, localidad FROM Areas WHERE Geoname=" + str(zona))
                rst = cursor.fetchall()
                cursor.close()
                cursor.execute("UPDATE Nodos SET Zona='" + rst[0][0] + "', subzona='" + rst[0][1] + "', localidad=" + rst[0][2] + " WHERE Geoname=" + str(self.ftr.id()))
                cnn.commit()
                pass
            poste = self.detecto_poste(self.point)
            if poste!=0:
                #QMessageBox.information(None, 'EnerGis 5', 'Tomo poste ' + str(poste))
                cnn = self.conn
                cursor = cnn.cursor()
                cursor.execute("UPDATE Postes SET id_nodo=" + str(self.ftr.id()) + " WHERE Geoname=" + str(poste))
                cnn.commit()
        if self.elmt=='Poste':
            poste = self.detecto_poste(self.point)
            if poste!=0:
                QMessageBox.information(None, 'EnerGis 5', 'Ya hay un poste en esa posicion')
                return
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("mover_poste " + str(self.ftr.id()) + ', ' + str(self.dx) + ', ' + str(self.dy))
            cnn.commit()
            zona = self.detecto_zona(self.point)
            if zona!=0:
                #QMessageBox.information(None, 'EnerGis 5', 'Tomo zona ' + str(zona))
                pass
            nodo = self.detecto_nodo(self.point)
            if nodo!=0:
                #QMessageBox.information(None, 'EnerGis 5', 'Tomo nodo ' + str(nodo))
                cnn = self.conn
                cursor = cnn.cursor()
                cursor.execute("UPDATE Postes SET id_nodo=" + str(nodo) + " WHERE Geoname=" + str(poste))
                cnn.commit()
            else:
                linea = self.detecto_linea(self.point)
                if linea!=0:
                    #QMessageBox.information(None, 'EnerGis 5', 'Tomo linea ' + str(linea))
                    cnn = self.conn
                    cursor = cnn.cursor()
                    cursor.execute("DELETE FROM Lineas_Postes WHERE id_linea=" + str(linea))
                    cnn.commit()
                    cursor.execute("INSERT INTO Lineas_Postes (id_linea, id_poste) VALUES (" + str(linea) + ", " +  str(self.ftr.id()) + ")")
                    cnn.commit()

        if self.elmt[:7]=='Vertice':
            nodo = self.detecto_nodo(self.point)
            if nodo!=0:
                QMessageBox.information(None, 'EnerGis 5', 'Ya hay un nodo en esa posicion')
                return
            str_vertice = self.elmt[8:]
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("mover_linea " + str(self.ftr.id()) + ', ' + str_vertice + ', ' + str(self.dx) + ', ' + str(self.dy))
            cnn.commit()
            poste = self.detecto_poste(self.point)
            if poste!=0:
                #QMessageBox.information(None, 'EnerGis 5', 'Tomo poste ' + str(poste))
                cnn = self.conn
                cursor = cnn.cursor()
                cursor.execute("DELETE FROM Lineas_Postes WHERE id_linea=" + str(str(id)))
                cursor.execute("INSERT INTO Lineas_Postes (id_linea, id_poste) VALUES (" + str(self.ftr.id()) + ", " + str(poste) + ")")
                cnn.commit()

        if self.elmt[:7]=='Oertice':
            str_vertice = self.elmt[8:]
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("mover_area " + str(self.ftr.id()) + ', ' + str_vertice + ', ' + str(self.dx) + ', ' + str(self.dy))
            cnn.commit()

        if self.elmt[:7]=='Pertice':
            str_vertice = self.elmt[8:]
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("mover_parcela " + str(self.ftr.id()) + ', ' + str_vertice + ', ' + str(self.dx) + ', ' + str(self.dy))
            cnn.commit()

        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            lyr.triggerRepaint()

        self.habilitar_snap()
        self.elmt = ''
        self.ftr = None
        self.p1 = None
        self.p2 = None

    def detecto_poste(self, point):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Postes':
                width = 0.1 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    return ftr.id()
        return 0

    def detecto_zona(self, point):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name() == 'Areas':
                width = 0.1 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    return ftr.id()
        return 0

    def detecto_linea(self, point):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
                width = 5 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    return ftr.id()
        return 0

    def detecto_nodo(self, point):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                width = 5 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    return ftr.id()
        return 0
