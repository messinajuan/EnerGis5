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
from qgis.core import QgsPoint, QgsRectangle, QgsFeatureRequest, QgsVectorLayer, QgsFeature
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrLinea(QgsMapTool):
    def __init__(self, iface, mapCanvas, conn, tension):
        QgsMapTool.__init__(self, mapCanvas)
        self.iface = iface
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.tension = tension
        self.tecla=''
        self.nodo_desde = 0
        self.nodo_hasta = 0
        self.puntos = []
        self.lineas_temp = QgsVectorLayer()

        self.rb = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PointGeometry)
        self.rb.setStrokeColor(QColor('Purple'))
        self.rb.setWidth(2.0)

        #arranco con un snap y despues paso a otro
        self.snapIndicator = QgsSnapIndicator(self.mapCanvas)
        self.snapper = QgsMapCanvasSnappingUtils(self.mapCanvas)
        config = QgsSnappingConfig()
        config.setEnabled(True)
        config.setType(QgsSnappingConfig.Vertex)
        config.setUnits(QgsTolerance.Pixels)
        config.setTolerance(12)
        config.setMode(2)
        self.snapper.setConfig(config)

        n = self.mapCanvas.layerCount()
        b_existe = False
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyrCRS = lyr.crs().authid()
            if lyr.name() == 'Lineas_Temp':
                b_existe = True
                self.lineas_temp = lyr

        if b_existe == False:
            lineas_temp = QgsVectorLayer("LineString?crs=" + lyrCRS, "Lineas_Temp", "memory")
            QgsProject.instance().addMapLayer(lineas_temp)
            self.lineas_temp.renderer().symbol().setWidth(0.4)
            self.lineas_temp.renderer().symbol().setColor(QColor("red"))
        pass

    def habilitar_snap(self):
        config = QgsSnappingConfig()
        config.setEnabled(True)
        config.setType(QgsSnappingConfig.VertexAndSegment)
        config.setUnits(QgsTolerance.Pixels)
        config.setTolerance(12)
        config.setMode(2)
        self.snapper.setConfig(config)

    def keyPressEvent(self, event):
        #QMessageBox.information(None, "Mensaje", str(event.key()))
        if str(event.key()) == '16777249':
            self.tecla = 'Ctrl'
        if str(event.key()) == '16777240':
            self.tecla = 'Shift'
        if str(event.key()) == '16777216':
            self.tecla = 'Esc'
            #QMessageBox.information(None, "Mensaje", str(event.key()))
            self.puntos = []
            #borra todos los objetos de la capa
            if not self.lineas_temp.isEditable():
                self.lineas_temp.startEditing()
            listOfIds = [feat.id() for feat in self.lineas_temp.getFeatures()]
            self.lineas_temp.deleteFeatures(listOfIds)
            self.lineas_temp.commitChanges()
            #----------------------------------
            pass

    def keyReleaseEvent(self, event):
        #QMessageBox.information(None, "Mensaje", tecla)
        self.tecla = ''
        pass
        
    def canvasPressEvent(self, event):
        #self.puntos.append(QgsPoint(self.point.x(),self.point.y()))
        if len(self.puntos) == 0:
            n = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name()[:5] == 'Nodos':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    i = 0
                    for ftr in ftrs:
                        i = i + 1
                    if i > 0:
                        #QMessageBox.information(None, 'EnerGis 5', 'Inicio')
                        #lineas_temp.triggerRepaint()
                        geom = ftr.geometry()
                        if geom.asPoint().x() > 0:
                            self.puntos.append(QgsPoint(geom.asPoint().x(),geom.asPoint().y()))
                            self.nodo_desde = ftr.id()
                            self.tension = lyr.name() [6 - len(lyr.name()):]
                            #QMessageBox.information(None, 'Nodo Desde', str(self.nodo_desde))
                            self.habilitar_snap()
                            return
        else:
            n = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            for lyr in layers:
                #QMessageBox.information(None, 'Capas', lyr.name() + ' - ' + str(lyr.type()))
                if lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Temp':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel() #me alejo 5 de los nodos !
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    i = 0
                    for ftr in ftrs:
                        i = i + 1
                    if i > 0:
                        #QMessageBox.information(None, 'EnerGis 5', 'Pass')
                        #No tengo que hacer nada para permitir el doble click
                        return

            if self.point.x() > 0:
                self.puntos.append(QgsPoint(self.point.x(),self.point.y()))
                pts = QgsGeometry.fromPolyline(self.puntos)
                self.ftrLinea = QgsFeature()
                self.ftrLinea.setGeometry(pts)
                lineas_temp_data = self.lineas_temp.dataProvider()
                lineas_temp_data.addFeatures([self.ftrLinea])
                self.lineas_temp.triggerRepaint()
                #QMessageBox.information(None, 'EnerGis 5', 'Agrego punto ' + str(len(puntos)) + ' - ' + str(ftrLinea.geometry()))
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
            #borra todos los objetos de la capa
            if not self.lineas_temp.isEditable():
                self.lineas_temp.startEditing()
            listOfIds = [feat.id() for feat in self.lineas_temp.getFeatures()]
            self.lineas_temp.deleteFeatures(listOfIds)
            self.lineas_temp.commitChanges()
            #----------------------------------
            self.puntos.append(QgsPoint(self.point.x(),self.point.y()))
            pts = QgsGeometry.fromPolyline(self.puntos)
            self.ftrLinea = QgsFeature()
            self.ftrLinea.setGeometry(pts)
            lineas_temp_data = self.lineas_temp.dataProvider()
            lineas_temp_data.addFeatures([self.ftrLinea])
            self.lineas_temp.triggerRepaint()
            self.puntos.pop()
        pass

    def canvasDoubleClickEvent(self, event):
        #QMessageBox.information(None, 'EnerGis 5', 'Doble click')
        #x = event.pos().x()
        #y = event.pos().y()
        #point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        self.longitud = 0
        if len(self.puntos) != 0:
            n = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() != 'Nodos_Temp':
                    if lyr.name()[:5] == 'Nodos':
                        #QMessageBox.information(None, 'EnerGis 5', lyr.name())
                        width = 5 * self.mapCanvas.mapUnitsPerPixel()
                        rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                        int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                        ftrs = lyr.getFeatures(int)
                        #QMessageBox.information(None, 'EnerGis 5', 'Punto Final ?')
                        for ftr in ftrs:
                            #QMessageBox.information(None, 'EnerGis 5', 'Punto Final')
                            #puntos.append(point)
                            geom = ftr.geometry()
                            #QMessageBox.information(None, 'Geom', str(geom.asPoint().x()))
                            if geom.asPoint().x() > 0:
                                #puntos.pop()
                                self.puntos.append(QgsPoint(geom.asPoint().x(),geom.asPoint().y()))
                                self.nodo_hasta = ftr.id()
                                #QMessageBox.information(None, 'Hasta', str(self.nodo_hasta))
                                #borra todos los objetos de la capa
                                if not self.lineas_temp.isEditable():
                                    self.lineas_temp.startEditing()
                                listOfIds = [feat.id() for feat in self.lineas_temp.getFeatures()]
                                self.lineas_temp.deleteFeatures(listOfIds)
                                self.lineas_temp.commitChanges()
                                #----------------------------------
                                pts = QgsGeometry.fromPolyline(self.puntos)
                                self.ftrLinea = QgsFeature()
                                self.ftrLinea.setGeometry(pts)
                                self.longitud = self.ftrLinea.geometry().length()
                                lineas_temp_data = self.lineas_temp.dataProvider()
                                lineas_temp_data.addFeatures([self.ftrLinea])
                                self.lineas_temp.triggerRepaint()

                                t = lyr.name() [6 - len(lyr.name()):]
                                if t != self.tension:
                                    QMessageBox.information(None, 'EnerGis 5', 'Línea entre dos niveles de Tensión')

                                self.puntos = []
                                self.crearLinea()
                                return

        QMessageBox.information(None, 'EnerGis 5', 'No se encontró nodo final')
        return

    def crearLinea(self):
        from .frm_lineas import frmLineas
        self.dialogo = frmLineas(self.mapCanvas, self.conn, self.tension, self.nodo_desde, self.nodo_hasta, self.longitud, self.ftrLinea, 0)
        self.dialogo.show()
        pass
