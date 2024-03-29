﻿# encoding: utf-8
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

from PyQt5 import QtGui
from PyQt5.QtWidgets import QMessageBox, QMenu
from PyQt5.QtCore import Qt, QPoint
from qgis.gui import QgsMapTool
from qgis.core import QgsRectangle, QgsFeatureRequest, QgsMapLayerType
from qgis.core import QgsProject

import os

from .herr_nodo import herrNodo
from .herr_linea import herrLinea
from .herr_poste import herrPoste
from .herr_area import herrArea
from .herr_parcela import herrParcela
from .herr_zoom import herrZoom
from .herr_navegar_fuentes import herrNavegarFuentes
from .herr_navegar_extremos import herrNavegarExtremos
from .herr_caida_tension import herrCaidaTension

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrSeleccion(QgsMapTool):
    def __init__(self, proyecto, tipo_usuario, mapCanvas, iface, conn, mnodos, mlineas, tension):
        QgsMapTool.__init__(self, mapCanvas)
        self.proyecto = proyecto
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas
        self.iface = iface
        self.conn = conn
        self.mnodos = mnodos
        self.mlineas = mlineas
        self.tension = tension
        self.elmt = 0
        self.estado = 0
        self.clipboard=[]
        self.tecla=''

    def keyPressEvent(self, event):
        if str(event.key()) == '16777249':
            self.tecla = 'Ctrl'
            pass

    def keyReleaseEvent(self, event):
        self.tecla=''
        if str(event.key()) == '16777223':
            self.h_borrar() #copiado textualmente de energis5.py
            pass
        pass

    def h_borrar(self): #copiado textualmente de energis5.py
        ftrs_nodos = []
        ftrs_lineas = []
        ftrs_postes = []
        ftrs_areas = []
        ftrs_parcelas = []
        capas = []
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        str_nodos = '0'
        str_lineas = '0'
        str_postes = '0'
        str_areas = '0'
        str_parcelas = '0'
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                for ftr in lyr.selectedFeatures():
                    ftrs_nodos.append(ftr.id())
                    str_nodos = str_nodos + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
                for ftr in lyr.selectedFeatures():
                    ftrs_lineas.append(ftr.id())
                    str_lineas = str_lineas + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name()[:6] == 'Postes':
                for ftr in lyr.selectedFeatures():
                    ftrs_postes.append(ftr.id())
                    str_postes = str_postes + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name() == 'Areas':
                for ftr in lyr.selectedFeatures():
                    ftrs_areas.append(ftr.id())
                    str_areas = str_areas + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name() == 'Parcelas':
                for ftr in lyr.selectedFeatures():
                    ftrs_parcelas.append(ftr.id())
                    str_parcelas = str_parcelas + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)

        if len(ftrs_nodos) + len(ftrs_lineas) + len(ftrs_postes) + len(ftrs_areas) + len(ftrs_parcelas):
            if len(capas)==1:
                reply = QMessageBox.question(None, 'EnerGis', 'Desea borrar los elementos seleccionados ?', QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
                layers = [self.mapCanvas.layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Lineas WHERE Geoname IN (" + str_lineas + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Lineas !")
                        lyr.triggerRepaint()
                    elif lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Nodos WHERE Geoname IN (" + str_nodos + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Nodos !")
                        lyr.triggerRepaint()
                    elif lyr.name()[:6] == 'Postes':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Postes WHERE Geoname IN (" + str_postes + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Postes !")
                        lyr.triggerRepaint()
                    elif lyr.name() == 'Areas':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Areas WHERE Geoname IN (" + str_areas + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Areas !")
                        lyr.triggerRepaint()
                    elif lyr.name() == 'Parcelas':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Parcelas WHERE Geoname IN (" + str_parcelas + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Parcelas !")
                        lyr.triggerRepaint()
                    else:
                        #lyr.triggerRepaint()
                        pass
            else:
                from .frm_borrar import frmBorrar
                dialogo = frmBorrar(capas)
                dialogo.exec()
                capas=dialogo.capas
                dialogo.close()

                if len(capas)==0:
                    return

                layers = [self.mapCanvas.layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
                        for capa in capas:
                            if capa==lyr.name():
                                str_tension = lyr.name() [7 - len(lyr.name()):]
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Lineas WHERE Tension=" + str_tension + " AND Geoname IN (" + str_lineas + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Lineas !")
                                lyr.triggerRepaint()
                    elif lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                        for capa in capas:
                            if capa==lyr.name():
                                str_tension = lyr.name() [6 - len(lyr.name()):]
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Nodos WHERE Tension=" + str_tension + " AND Geoname IN (" + str_nodos + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Nodos !")
                                lyr.triggerRepaint()
                    elif lyr.name()[:6] == 'Postes':
                        for capa in capas:
                            if capa==lyr.name():
                                str_tension = lyr.name() [7 - len(lyr.name()):]
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Postes WHERE Tension=" + str_tension + " AND Geoname IN (" + str_postes + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Postes !")
                                lyr.triggerRepaint()
                    elif lyr.name() == 'Areas':
                        for capa in capas:
                            if capa=='Areas':
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Areas WHERE Geoname IN (" + str_areas + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Areass !")
                                lyr.triggerRepaint()
                    elif lyr.name() == 'Parcelas':
                        for capa in capas:
                            if capa=='Parcelas':
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Parcelas WHERE Geoname IN (" + str_parcelas + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Parcelas !")
                                lyr.triggerRepaint()
                    else:
                        #lyr.triggerRepaint()
                        pass
            return
        pass

    def lyr_visible(self, layer):
        layer_tree_root = QgsProject.instance().layerTreeRoot()
        layer_tree_layer = layer_tree_root.findLayer(layer)
        return layer_tree_layer.isVisible()

    def canvasPressEvent(self, event):
        #Get the click
        x = event.pos().x()
        y = event.pos().y()
        self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)

        #primero right click
        if event.button() == Qt.RightButton:

            if self.tipo_usuario==4:
                return

            contextMenu = QMenu()
            n = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(n)]

            setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_nodo.png")),"Nodo")
            setCurrentAction.triggered.connect(self.nodo)
            setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_linea.png")),"Linea")
            setCurrentAction.triggered.connect(self.linea)
            setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_poste.png")),"Poste")
            setCurrentAction.triggered.connect(self.poste)
            setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_area.png")),"Area")
            setCurrentAction.triggered.connect(self.area)
            setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_parcela.png")),"Parcela")
            setCurrentAction.triggered.connect(self.parcela)
            contextMenu.addSeparator()

            setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_zoom_in.png")),"Zoom In")
            setCurrentAction.triggered.connect(self.zoomIn)
            setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_zoom_out.png")),"Zoom Out")
            setCurrentAction.triggered.connect(self.zoomOut)
            setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_pan.png")),"Pan")
            setCurrentAction.triggered.connect(self.pan)

            for lyr in layers:
                if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                    if self.lyr_visible(lyr) is True:
                        #QMessageBox.information(None, 'EnerGis 5', lyr.name())
                        lyr.removeSelection()
                        if (lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Temp') or (lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Temp') or lyr.name()[:6] == 'Postes' or lyr.name() == 'Areas' or lyr.name() == 'Parcelas':
                            #QMessageBox.information(None, 'EnerGis 5', lyr.name())
                            width = 5 * self.mapCanvas.mapUnitsPerPixel()
                            rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                            int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                            ftrs = lyr.getFeatures(int)
                            for ftr in ftrs:
                                lyr.select(ftr.id())
                                #geom = ftr.geometry()
                                self.capa = lyr
                                self.ftr = ftr

                                #QMessageBox.information(None, 'EnerGis 5', str(ftr.id()))

                                contextMenu = QMenu()
                                setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_editar.png")),"Editar")
                                setCurrentAction.triggered.connect(self.editar)
                                setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_borrar.png")),"Borrar")
                                setCurrentAction.triggered.connect(self.borrar)
                                contextMenu.addSeparator()
                                #solo se puede cortar de la capa nodos
                                if lyr.name()[:5] == 'Nodos':
                                    setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_cortar.png")),"Cortar")
                                    setCurrentAction.triggered.connect(self.cortar)
                                setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_copiar.png")),"Copiar")
                                setCurrentAction.triggered.connect(self.copiar)
                                #solo se pude pegar si hay algo cortado o copiado
                                if len(self.clipboard)!=0:
                                    capa = self.clipboard[1]
                                    if capa.name()==self.capa.name():
                                        setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_pegar.png")),"Pegar")
                                        setCurrentAction.triggered.connect(self.pegar)

                                contextMenu.addSeparator()

                                if self.capa.name()[:6] == 'Lineas':
                                    setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_poste.png")),"Insertar Postes")
                                    setCurrentAction.triggered.connect(self.insertar_postes)
                                if self.capa.name()[:5] == 'Nodos':
                                    cnn = self.conn
                                    cursor = cnn.cursor()
                                    nodos = []

                                    cursor.execute("SELECT elmt, estado FROM Nodos WHERE geoname=" + str(self.ftr.id()))
                                    #convierto el cursor en array
                                    nodos = tuple(cursor)
                                    cursor.close()
                                    self.elmt = nodos[0][0]
                                    self.estado = nodos[0][1]
                                    if self.estado==3:
                                        contextMenu.addSeparator()
                                        setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_cerrar_elemento_maniobra.png")),"Cerrar")
                                        setCurrentAction.triggered.connect(self.operar_seccionador)

                                    if self.estado==2:
                                        contextMenu.addSeparator()
                                        setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_abrir_elemento_maniobra.png")),"Abrir")
                                        setCurrentAction.triggered.connect(self.operar_seccionador)

                                    contextMenu.addSeparator()
                                    if self.elmt!=1:
                                        setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_nav_fuente.png")),"Navegar a la Fuente")
                                        setCurrentAction.triggered.connect(self.navegar_fuentes)

                                    setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_nav_extremos.png")),"Navegar a los extremos")
                                    setCurrentAction.triggered.connect(self.navegar_extremos)

                                x = event.pos().x() + 5
                                y = event.pos().y()
                                self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
                                #QMessageBox.information(None, 'EnerGis 5', str(point))
                                action = contextMenu.exec_(self.mapCanvas.mapToGlobal(QPoint(event.pos().x()+5, event.pos().y())))
                                #QMessageBox.information(None, 'EnerGis 5', str(action))
                                return

            x = event.pos().x() + 5
            y = event.pos().y()
            self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
            action = contextMenu.exec_(self.mapCanvas.mapToGlobal(QPoint(event.pos().x()+5, event.pos().y())))
            #QMessageBox.information(None, 'EnerGis 5', str(action))
            return

        else:

            #si no tengo apretada Ctrl borro la seleccion anterior
            if self.tecla != 'Ctrl':
                n = self.mapCanvas.layerCount()
                layers = [self.mapCanvas.layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                        lyr.removeSelection()

            n = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            #hacemos que se busque en las capas que queremos !!!
            for lyr in layers:
                if self.lyr_visible(lyr) is True:
                    if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                        #QMessageBox.information(None, 'EnerGis 5', lyr.name())
                        if lyr.name()[:6] == 'Lineas' or lyr.name()[:5] == 'Nodos' or lyr.name()[:6] == 'Postes' or lyr.name() == 'Areas' or lyr.name() == 'Parcelas':
                            #QMessageBox.information(None, 'EnerGis 5', lyr.name())
                            width = 5 * self.mapCanvas.mapUnitsPerPixel()
                            rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                            #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                            int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                            ftrs = lyr.getFeatures(int)
                            for ftr in ftrs:
                                #QMessageBox.information(None, 'EnerGis 5', ftr.geometry().asWkt())
                                #QMessageBox.information(None, 'EnerGis 5', str(ftr.id()))
                                b_seleccionado = False
                                for i in lyr.selectedFeatures():
                                    if i.id() == ftr.id():
                                        b_seleccionado = True

                                if b_seleccionado == True:
                                    seleccion = []
                                    for i in lyr.selectedFeatures():
                                        seleccion.append(i.id())
                                    seleccion.remove(ftr.id())
                                    lyr.removeSelection()
                                    lyr.select(seleccion)
                                    return
                                else:
                                    lyr.select(ftr.id())
                                    return

    def canvasDoubleClickEvent(self, event):

        #Get the click
        x = event.pos().x()
        y = event.pos().y()
        self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        #hacemos que se busque en las capas que queremos !!!
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                if self.lyr_visible(lyr) is True:
                    if (lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Temp') or (lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Temp') or lyr.name()[:6] == 'Postes' or lyr.name() == 'Areas' or lyr.name() == 'Parcelas':
                        #QMessageBox.information(None, 'EnerGis 5', str(lyr.name()))
                        width = 6 * self.mapCanvas.mapUnitsPerPixel()
                        rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                        int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                        ftrs = lyr.getFeatures(int)
                        for ftr in ftrs:
                            #QMessageBox.information(None, 'EnerGis 5', str(ftr.id()))
                            lyr.select(ftr.id())

                            if lyr.name()[:5] == 'Nodos':
                                str_tension = lyr.name() [6 - len(lyr.name()):]
                                if str_tension.strip() == 'Proyectos':
                                    from .frm_nodos_proyecto import frmNodosProyecto
                                    self.dialogo = frmNodosProyecto(self.proyecto, self.tipo_usuario, self.mapCanvas, self.conn, str_tension, ftr.id(), 0)
                                    self.dialogo.show()
                                    return
                                else:
                                    from .frm_nodos import frmNodos
                                    self.dialogo = frmNodos(self.tipo_usuario, self.mapCanvas, self.conn, str_tension, ftr.id(), 0)
                                    self.dialogo.show()
                                    return
                            if lyr.name()[:6] == 'Lineas':
                                str_tension = lyr.name() [7 - len(lyr.name()):]
                                if str_tension.strip() == 'Proyectos':
                                    from .frm_lineas_proyecto import frmLineasProyecto
                                    self.dialogo = frmLineasProyecto(self.proyecto, self.tipo_usuario, self.mapCanvas, self.conn, str_tension, 0, 0, ftr.geometry().length(), None, ftr.id())
                                    self.dialogo.show()
                                    return
                                else:
                                    from .frm_lineas import frmLineas
                                    self.dialogo = frmLineas(self.tipo_usuario, self.mapCanvas, self.conn, str_tension, 0, 0, ftr.geometry().length(), None, ftr.id())
                                    self.dialogo.show()
                                    return
                            if lyr.name()[:6] == 'Postes':
                                str_tension = lyr.name() [7 - len(lyr.name()):]
                                if str_tension.strip() == 'Proyectos':
                                    from .frm_postes_proyecto import frmPostesProyecto
                                    self.dialogo = frmPostesProyecto(self.proyecto, self.tipo_usuario, self.mapCanvas, self.conn, str_tension, ftr.id(), 0, 0, 0)
                                    self.dialogo.show()
                                    return
                                else:
                                    from .frm_postes import frmPostes
                                    self.dialogo = frmPostes(self.tipo_usuario, self.mapCanvas, self.conn, str_tension, ftr.id(), 0, 0, 0)
                                    self.dialogo.show()
                                    return
                            if lyr.name() == 'Areas':
                                from .frm_areas import frmAreas
                                self.dialogo = frmAreas(self.tipo_usuario, self.mapCanvas, self.conn, '', ftr.id())
                                self.dialogo.show()
                                return
                            if lyr.name() == 'Parcelas':
                                from .frm_parcelas import frmParcelas
                                self.dialogo = frmParcelas(self.tipo_usuario, self.mapCanvas, self.conn, '', ftr.id())
                                self.dialogo.show()
                                return
                            return
        pass

    def nodo(self):
        tool = herrNodo(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.mapCanvas.setCursor(curNodo)
        pass
        
    def linea(self):
        tool = herrLinea(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.mapCanvas.setCursor(curLinea)
        pass
               
    def poste(self):
        tool = herrPoste(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.mapCanvas.setCursor(curNodo)
        pass

    def area(self):
        #QMessageBox.information(None, 'h_nodo', str(tension))
        tool = herrArea(self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.mapCanvas.setCursor(curLinea)
        pass

    def parcela(self):
        #QMessageBox.information(None, 'h_nodo', str(tension))
        tool = herrParcela(self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.mapCanvas.setCursor(curLinea)
        pass

    def insertar_postes(self):
        dist, p2, segmento, s = self.ftr.geometry().closestSegmentWithContext(self.point)
        i=0
        for v in self.ftr.geometry().vertices():
            i=i+1
            if i==segmento:
                p1=v
            if i==segmento+1:
                p2=v

        str_tension = self.capa.name() [7 - len(self.capa.name()):]
        from .frm_insertar_postes import frmInsertarPostes
        self.dialogo = frmInsertarPostes(self.proyecto, self.mapCanvas, self.conn, str_tension, self.ftr.id(), p1, p2)
        self.dialogo.show()
        pass

    def editar(self):
        #QMessageBox.information(None, 'EnerGis 5', str(self.ftr))
        if self.capa.name()[:5] == 'Nodos' and self.capa.name() != 'Nodos_Temp':
            str_tension = self.capa.name() [6 - len(self.capa.name()):]
            from .frm_nodos import frmNodos
            self.dialogo = frmNodos(self.tipo_usuario, self.mapCanvas, self.conn, str_tension, self.ftr.id(), 0)
            self.dialogo.show()
            pass
        if self.capa.name()[:6] == 'Lineas' and self.capa.name() != 'Lineas_Temp':
            str_tension = self.capa.name() [7 - len(self.capa.name()):]
            from .frm_lineas import frmLineas
            self.dialogo = frmLineas(self.tipo_usuario, self.mapCanvas, self.conn, str_tension, 0, 0, self.ftr.geometry().length(), None, self.ftr.id())
            self.dialogo.show()
            pass
        if self.capa.name()[:6] == 'Postes':
            str_tension = self.capa.name() [7 - len(self.capa.name()):]
            from .frm_postes import frmPostes
            self.dialogo = frmPostes(self.tipo_usuario, self.mapCanvas, self.conn, str_tension, self.ftr.id(), 0, 0, 0)
            self.dialogo.show()
            pass
        if self.capa.name() == 'Areas':
            from .frm_areas import frmAreas
            self.dialogo = frmAreas(self.tipo_usuario, self.mapCanvas, self.conn, '', self.ftr.id())
            self.dialogo.show()
            pass
        if self.capa.name() == 'Parcelas':
            from .frm_parcelas import frmParcelas
            self.dialogo = frmParcelas(self.tipo_usuario, self.mapCanvas, self.conn, '', self.ftr.id())
            self.dialogo.show()
            pass

    def operar_seccionador(self):
        from .frm_operar_seccionador import frmOperarSeccionador
        self.dialogo = frmOperarSeccionador(self.conn, self.ftr.id(), self.elmt, self.estado, self.capa)
        self.dialogo.show()
        pass

    def cortar(self):
        reply = QMessageBox.question(None, 'EnerGis 5', 'Desea cortar atributos del elemento ' + str(self.ftr.id()) + ' de la capa ' + self.capa.name() + ' ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        self.clipboard = []
        self.clipboard.append("cortar")
        self.clipboard.append(self.capa)
        self.clipboard.append(self.ftr)

    def copiar(self):
        #reply = QMessageBox.question(None, 'EnerGis 5', 'Desea copiar atributos del elemento ' + str(self.ftr.id()) + ' de la capa ' + self.capa.name() + ' ?', QMessageBox.Yes, QMessageBox.No)
        #if reply == QMessageBox.No:
        #    return
        self.clipboard = []
        self.clipboard.append("copiar")
        self.clipboard.append(self.capa)
        self.clipboard.append(self.ftr)

    def pegar(self):
        reply = QMessageBox.question(None, 'EnerGis 5', 'Desea pegar los atributos al elemento ' + str(self.ftr.id()) + ' de la capa ' + self.capa.name() + ' ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        str_operacion = self.clipboard[0]
        capa = self.clipboard[1]
        elemento = self.clipboard[2]

        cnn = self.conn

        if capa.name()[:5] == 'Nodos':
            cursor = cnn.cursor()
            cursor.execute("SELECT ISNULL(nombre, ''), ISNULL(descripcion, ''), elmt, ISNULL(val1, ''), ISNULL(val2, ''), ISNULL(val3, ''), ISNULL(val4, ''), ISNULL(val5, ''), modificacion, estado, ISNULL(uucc, '') FROM Nodos WHERE Geoname=" + str(elemento.id()))
            #convierto el cursor en array
            rst = tuple(cursor)
            cursor.close()

            str_update = "nombre='" + rst[0][0] + "'"
            str_update = str_update + ", descripcion='" + rst[0][1] + "'"
            str_update = str_update + ", elmt=" + str(rst[0][2])
            str_update = str_update + ", val1='" + rst[0][3] + "'"
            str_update = str_update + ", val2='" + rst[0][4] + "'"
            str_update = str_update + ", val3='" + rst[0][5] + "'"
            str_update = str_update + ", val4='" + rst[0][6] + "'"
            str_update = str_update + ", val5='" + rst[0][7] + "'"
            str_update = str_update + ", modificacion='" + str(rst[0][8]).replace('-','') + "'"
            str_update = str_update + ", estado=" + str(rst[0][9])
            str_update = str_update + ", uucc='" + rst[0][10] + "'"

            cursor = cnn.cursor()
            try:
                cursor.execute("UPDATE Nodos SET " + str_update + " WHERE Geoname=" + str(self.ftr.id()))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.information(None, 'EnerGis 5', "No se pudo actualizar !")
            QMessageBox.information(None, '', "Pegado ! Falta ver mnNodos")

            if rst[0][2] == 6:
                if str_operacion == "Copiar":
                    QMessageBox.information(None, '', "No se moverán los usuarios del suministro, quedarán en el nodo origen")
                else:
                    cursor = cnn.cursor()
                    try:
                        cursor.execute("UPDATE suministros SET id_nodo=" + str(self.ftr.id()) + " WHERE id_nodo=" + str(elemento.id()))
                        cnn.commit()
                    except:
                        cnn.rollback()
                        QMessageBox.information(None, 'EnerGis 5', "No se pudo actualizar !")

            if str_operacion == "Cortar":
                cursor = cnn.cursor()
                try:
                    cursor.execute("UPDATE Nodos SET Nombre='', Descripcion='', elmt=0, Val1='',Val2='',Val3='',Val4='',Val5='', estado=0, uucc='' WHERE geoname=" + str(elemento.id()))
                    cnn.commit()
                except:
                    cnn.rollback()
                    QMessageBox.information(None, 'EnerGis 5', "No se pudo actualizar !")
                QMessageBox.information(None, '', "Falta ver mnNodos")

        elif capa.name()[:6] == 'Lineas':
            cursor = cnn.cursor()
            cursor.execute("SELECT elmt, fase, modificacion, exp, disposicion, conservacion, ternas, acometida, uucc FROM Lineas WHERE geoname=" + str(elemento.id()))
            #convierto el cursor en array
            rst = tuple(cursor)
            cursor.close()

            str_update = "elmt=" + str(rst[0][0])
            str_update = str_update + ", fase='" + rst[0][1] + "'"
            str_update = str_update + ", modificacion='" + str(rst[0][2]).replace('-','') + "'"
            str_update = str_update + ", exp='" + rst[0][3] + "'"
            str_update = str_update + ", disposicion='" + rst[0][4] + "'"
            str_update = str_update + ", conservacion='" + rst[0][5] + "'"
            str_update = str_update + ", ternas='" + rst[0][6] + "'"
            str_update = str_update + ", acometida=" + str(rst[0][7])
            str_update = str_update + ", uucc='" + rst[0][8] + "'"

            cursor = cnn.cursor()
            cursor.execute("UPDATE Lineas SET " + str_update + " WHERE geoname=" + str(self.ftr.id()))
            cnn.commit()
            QMessageBox.information(None, '', "Pegado ! Falta ver mnLineas")

        elif capa.name()[:6] == 'Postes':
            cursor = cnn.cursor()
            cursor.execute("SELECT elmt, estructura, rienda, altura, modificacion, ISNULL(descripcion, ''), profundidad, tipo, aislacion, fundacion, comparte, ternas, PAT, descargadores FROM Postes WHERE Geoname=" + str(elemento.id()))
            #convierto el cursor en array
            rst = tuple(cursor)
            cursor.close()

            str_update = "elmt=" + str(rst[0][0])
            str_update = str_update + ", estructura=" + str(rst[0][1])
            str_update = str_update + ", rienda=" + str(rst[0][2])
            str_update = str_update + ", altura=" + str(rst[0][3])
            str_update = str_update + ", modificacion='" + str(rst[0][4]).replace('-','') + "'"
            str_update = str_update + ", descripcion='" + rst[0][5] + "'"
            str_update = str_update + ", profundidad='" + rst[0][6] + "'"
            str_update = str_update + ", tipo='" + rst[0][7] + "'"
            str_update = str_update + ", aislacion='" + rst[0][8] + "'"
            str_update = str_update + ", fundacion=" + str(rst[0][9])
            str_update = str_update + ", comparte='" + rst[0][10] + "'"
            str_update = str_update + ", ternas='" + rst[0][11] + "'"
            str_update = str_update + ", PAT=" + str(rst[0][12])
            str_update = str_update + ", descargadores=" + str(rst[0][13])

            cursor = cnn.cursor()
            try:
                cursor.execute("UPDATE Postes SET " + str_update + " WHERE geoname=" + str(self.ftr.id()))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.information(None, 'EnerGis 5', "No se pudo actualizar !")
            QMessageBox.information(None, '', "Pegado !")

        capa.triggerRepaint()

    def borrar(self):
        reply = QMessageBox.question(None, 'EnerGis 5', 'Desea borrar de capa ' + self.capa.name() + ' ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        if self.capa.name()[:5] == 'Nodos' and self.capa.name()!='Nodos_Temp':
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("DELETE FROM Nodos WHERE geoname=" + str(self.ftr.id()))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.information(None, 'EnerGis 5', "No se pudo actualizar !")
            self.capa.triggerRepaint()
            return

        if self.capa.name()[:6] == 'Lineas' and self.capa.name()!='Lineas_Temp':
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("DELETE FROM Lineas WHERE geoname=" + str(self.ftr.id()))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Lineas !")
            self.capa.triggerRepaint()
            return

        if self.capa.name()[:6] == 'Postes':
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("DELETE FROM Postes WHERE geoname=" + str(self.ftr.id()))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Postes !")
            self.capa.triggerRepaint()
            return

        if self.capa.name() == 'Areas':
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("DELETE FROM Areas WHERE geoname=" + str(self.ftr.id()))
                cnn.commit()
            except:
                cnn.rollback()
            self.capa.triggerRepaint()
            QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Areas !")
            return

        if self.capa.name() == 'Parcelas':
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("DELETE FROM Parcelas WHERE geoname=" + str(self.ftr.id()))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Parcelas !")
            self.capa.triggerRepaint()
            return

        pass

    def zoomIn(self):
        #QMessageBox.information(None, '', "zoomin")
        tool = herrZoom(self.iface.mapCanvas(), 'ZoomIn')
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punZoom = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_zoom_in.png'))
        punZoom.setMask(punZoom.mask())
        curZoom = QtGui.QCursor(punZoom)
        self.mapCanvas.setCursor(curZoom)
        pass

    def zoomOut(self):
        #QMessageBox.information(None, '', "zoomout")
        tool = herrZoom(self.iface.mapCanvas(), 'ZoomOut')
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punZoom = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_zoom_out.png'))
        punZoom.setMask(punZoom.mask())
        curZoom = QtGui.QCursor(punZoom)
        self.mapCanvas.setCursor(curZoom)
        pass
        
    def pan(self):
        #QMessageBox.information(None, 'h_nodo', "pan")
        tool = herrZoom(self.iface.mapCanvas(), 'Pan')
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punZoom = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_pan.png'))
        punZoom.setMask(punZoom.mask())
        curZoom = QtGui.QCursor(punZoom)
        self.mapCanvas.setCursor(curZoom)
        pass

    def navegar_fuentes(self):
        herrNavegarFuentes(self.iface.mapCanvas(), self.conn, self.ftr.id())
        pass

    def caida_tension(self):
        herrCaidaTension(self.iface.mapCanvas(), self.conn, self.ftr.id())
        pass

    def navegar_extremos(self):
        herrNavegarExtremos(self.iface.mapCanvas(), self.conn, self.ftr.id())
        pass
