# encoding: utf-8
#-----------------------------------------------------------
# Copyright (C) 2026 Juan Messina
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

import os
import pyodbc
import json
import tempfile
import subprocess

from qgis.core import QgsApplication, QgsLayerTreeLayer, QgsField, QgsFields
from qgis.core import QgsProject, QgsMapLayerType, QgsVectorFileWriter, QgsSimpleMarkerSymbolLayerBase
from qgis.core import QgsVectorLayer, QgsFeature, QgsPoint, QgsGeometry, QgsCoordinateReferenceSystem

from datetime import datetime
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtGui import QIcon, QFont, QColor
from PyQt5.QtWidgets import QMessageBox, QComboBox, QAction, QInputDialog, QToolBar, QFileDialog, QVBoxLayout, QTableWidget, QWidget, QDockWidget, QTableWidgetItem
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QLineEdit, QMenuBar, QListWidgetItem
from PyQt5.QtWidgets import QApplication, QProgressDialog

from PyQt5.QtCore import Qt, QVariant, QTimer

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class EnerGis5(object):

    def __init__(self, iface):
        #da acceso a la interfaz QGIS
        self.iface = iface
        self.mapCanvas = iface.mapCanvas()
        #self.utils = iface.mapCanvas().snappingUtils()
        # create action that will start plugin configuration
        self.energis_action = QAction(QIcon(os.path.join(basepath,"icons", 'energis.ico')), "EnerGis", self.iface.mainWindow())
        self.energis_action.setWhatsThis("")
        self.energis_action.setStatusTip("Detenido")
        self.energis_action.triggered.connect(self.run)
        # add toolbar button and menu item
        self.iface.addToolBarIcon(self.energis_action)
        self.iface.addPluginToMenu("EnerGis 5", self.energis_action)
        self.id_usuario_sistema = 0
        self.tipo_usuario = 4
        self.tension = '0'
        self.mnodos=()
        self.mlineas=()
        self.seleccion_n = []
        self.seleccion_l = []
        self.tensiones = []
        self.proyecto = ''
        self.conn = None
        self.red_verificada=False

    def initGui(self):
        #llamado cuando se carga el complemento
        #La versión cambiará cuando cambie la db
        self.version = '5.5.3'
        self.seleccion = []
        self.lyrSeleccion = None

    def detecto_cambio_seleccion(self):
        n=0
        n = self.iface.mapCanvas().layerCount()
        if n<1:
            return
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        if len(self.seleccion)==0:
            self.seleccion.append([])
        i = 0
        s = 0
        for lyr in layers:
            if i + 1 > len(self.seleccion):
                self.seleccion.append([])
            if lyr.name() == 'Areas' or lyr.name() == 'Parcelas' or lyr.name()[:5] == 'Nodos' or lyr.name()[:6] == 'Lineas' or lyr.name()[:6] == 'Postes':
                if lyr.selectedFeatures():
                    s = s + len(lyr.selectedFeatures())
                    if len(self.seleccion[i])>0:
                        if lyr.selectedFeatures() != self.seleccion[i]:
                            ftr = lyr.selectedFeatures()[0]
                            self.lleno_combo_propiedades(lyr, ftr)
                            self.seleccion[i] = lyr.selectedFeatures()
                    else:
                        ftr = lyr.selectedFeatures()[0]
                        self.lleno_combo_propiedades(lyr, ftr)
                        self.seleccion[i] = lyr.selectedFeatures()
                else:
                    self.seleccion[i]=[]
            i = i + 1
        if s == 0:
            try:
                self.tblPropiedades.setRowCount(0)
                self.cmbPropiedades.clear()
            except:
                pass

    def lleno_combo_propiedades(self, lyr, ftr):
        try:
            self.cmbPropiedades.clear()
            self.tblPropiedades.setRowCount(0)
            if lyr.name()[:5] == 'Nodos':
                self.cmbPropiedades.addItem('Nodo')
                conn = self.conn
                cursor = conn.cursor()
                cursor.execute("SELECT elmt FROM Nodos WHERE Geoname=" + str(ftr.id()))
                elemento = tuple(cursor)
                cursor.close()
                if elemento[0][0]==1:
                    self.cmbPropiedades.addItem('Fuente')
                if elemento[0][0]==2:
                    self.cmbPropiedades.addItem('Elemento de Maniobra')
                if elemento[0][0]==3:
                    self.cmbPropiedades.addItem('Elemento de Maniobra')
                if elemento[0][0]==4:
                    self.cmbPropiedades.addItem('Centro de Transformación')
                    conn = self.conn
                    cursor = conn.cursor()
                    cursor.execute("SELECT id_trafo FROM Transformadores INNER JOIN Nodos ON Transformadores.id_ct=Nodos.Nombre WHERE elmt=4 AND geoname=" + str(ftr.id()))
                    encontrados = tuple(cursor)
                    cursor.close()
                    for i in range (0, len(encontrados)):
                        self.cmbPropiedades.addItem('Transformador ' + str(encontrados[i][0]))
                if elemento[0][0]==5:
                    self.cmbPropiedades.addItem('Luminaria')
                if elemento[0][0]==6:
                    self.cmbPropiedades.addItem('Suministro')
                    conn = self.conn
                    cursor = conn.cursor()
                    cursor.execute("SELECT id_suministro FROM Suministros WHERE id_suministro IN (SELECT id_suministro FROM Usuarios) AND id_nodo=" + str(ftr.id()))
                    encontrados = tuple(cursor)
                    cursor.close()
                    for i in range (0, len(encontrados)):
                        self.cmbPropiedades.addItem('Suministro ' + encontrados[i][0])
                if elemento[0][0]==7:
                    self.cmbPropiedades.addItem('Capacitor')
                if elemento[0][0]==9:
                    self.cmbPropiedades.addItem('Regulador')
                if elemento[0][0]==11:
                    self.cmbPropiedades.addItem('Generador')
            if lyr.name()[:6] == 'Lineas':
                self.cmbPropiedades.addItem('Linea')
            if lyr.name()[:6] == 'Postes':
                self.cmbPropiedades.addItem('Poste')
            if lyr.name() == 'Areas':
                self.cmbPropiedades.addItem('Area')
            if lyr.name() == 'Parcelas':
                self.cmbPropiedades.addItem('Parcela')
            self.id_seleccionado = ftr.id()
            self.cmbPropiedades.activated.connect(self.elijo_elemento_propiedad)
            if self.cmbPropiedades.count()>0:
                #self.cmbPropiedades.setCurrentIndex(0)
                #QMessageBox.critical(None, 'EnerGis 5', self.cmbPropiedades.currentText())
                self.elijo_elemento_propiedad()
        except:
            pass

    def elijo_elemento_propiedad(self):
        font = QFont()
        font.setPointSize(8)
        self.tblPropiedades.setFont(font)
        self.tblPropiedades.verticalHeader().setVisible(False)
        self.tblPropiedades.setColumnCount(2)
        self.tblPropiedades.setHorizontalHeaderLabels(['Propiedad','Valor'])
        self.tblPropiedades.setColumnWidth(1, self.tblPropiedades.viewport().width() - self.tblPropiedades.columnWidth(0))
        self.tblPropiedades.setRowCount(0)
        #QMessageBox.critical(None, 'EnerGis 5', self.cmbPropiedades.currentText())
        if self.cmbPropiedades.currentText() == 'Nodo':
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT Geoname, Nombre, Descripcion, ROUND(XCoord, 1) AS X, ROUND(YCoord, 1) AS Y, Tension, Zona, Alimentador, UUCC FROM Nodos WHERE Geoname=" + str(self.id_seleccionado))
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            if len(encontrados) > 0:
                self.tblPropiedades.setRowCount(len(encontrados[0])+1)
            for i in range (0, len(encontrados[0])):
                propiedad = QTableWidgetItem(encabezado[i])
                valor = QTableWidgetItem(str(encontrados[0][i]))
                self.tblPropiedades.setRowHeight(i, 9)
                self.tblPropiedades.setItem(i,0,propiedad)
                self.tblPropiedades.setItem(i,1,valor)
            i = i + 1
            from .mod_coordenadas import convertir_coordenadas
            coordenadas = str(convertir_coordenadas(self, encontrados[0][3], encontrados[0][4], self.srid, 4326)).replace('[','').replace(']','')
            propiedad = QTableWidgetItem('Coordenadas')
            valor = QTableWidgetItem(coordenadas)
            self.tblPropiedades.setRowHeight(i, 9)
            self.tblPropiedades.setItem(i,0,propiedad)
            self.tblPropiedades.setItem(i,1,valor)
        if self.cmbPropiedades.currentText() == 'Elemento de Maniobra':
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT Nodos.Val1 AS Aparato, CASE WHEN elmt=3 THEN 'NA' ELSE 'NC' END AS Estado_Normal, CASE WHEN estado=3 THEN 'NA' ELSE 'NC' END AS Estado_Actual, LTRIM(LEFT(Nodos.Val2,15)) AS Tipo, LTRIM(LEFT(RIGHT(Nodos.Val2,35),5)) AS Corriente, LTRIM(RIGHT(Nodos.Val2,15)) AS PAT, Val3 AS Telemando, Val4 AS Descargadores, Val5 AS Poder_corte FROM Nodos WHERE geoname=" + str(self.id_seleccionado))
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            if len(encontrados) > 0:
                self.tblPropiedades.setRowCount(len(encontrados[0]))
            for i in range (0, len(encontrados[0])):
                propiedad = QTableWidgetItem(encabezado[i])
                valor = QTableWidgetItem(str(encontrados[0][i]))
                self.tblPropiedades.setRowHeight(i, 9)
                self.tblPropiedades.setItem(i,0,propiedad)
                self.tblPropiedades.setItem(i,1,valor)
        if self.cmbPropiedades.currentText()[:13] == 'Transformador':
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT id_trafo, potencia, conexionado, marca, Tension_1, Tension_2, n_chapa, anio_fabricacion AS año, aceite AS lts_aceite, Cromatografia, Certificado FROM Transformadores WHERE id_trafo=" + self.cmbPropiedades.currentText()[14:])
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            if len(encontrados) > 0:
                self.tblPropiedades.setRowCount(len(encontrados[0]))
            for i in range (0, len(encontrados[0])):
                propiedad = QTableWidgetItem(encabezado[i])
                valor = QTableWidgetItem(str(encontrados[0][i]))
                self.tblPropiedades.setRowHeight(i, 9)
                self.tblPropiedades.setItem(i,0,propiedad)
                self.tblPropiedades.setItem(i,1,valor)
        if self.cmbPropiedades.currentText() == 'Centro de Transformación':
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT Geoname, Elementos_Nodos.Descripcion AS Tipo, Ct.Tipo_ct, Ct.Mat_plataf, Ct.Tipo_oceba, Ct.Fecha_alta, caeis+caeies+caees+caeees AS Entradas, casis+casies+cases+casees AS Salidas, Exp, tipo_oceba, Ct.Conservacion, SUM(Transformadores.Potencia) AS Pot_Instalada, MAX(Transformadores.Conexionado) AS Conexionado, MAX(Transformadores.Tension_1) AS V1, MAX(Transformadores.Tension_2) AS V2 FROM Ct LEFT OUTER JOIN Transformadores ON Ct.Id_ct = Transformadores.Id_ct RIGHT OUTER JOIN Nodos ON Ct.Id_ct = Nodos.Nombre RIGHT OUTER JOIN Elementos_Nodos ON Nodos.Elmt = Elementos_Nodos.Id WHERE geoname=" + str(self.id_seleccionado) + " GROUP BY Nodos.Geoname, Elementos_Nodos.Descripcion, Ct.Tipo_ct, Ct.Mat_plataf, Ct.tipo_oceba, Ct.fecha_alta, Ct.conservacion, caeis+caeies+caees+caeees, casis+casies+cases+casees, Exp, tipo_oceba")
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            if len(encontrados) > 0:
                self.tblPropiedades.setRowCount(len(encontrados[0]))
            for i in range (0, len(encontrados[0])):
                propiedad = QTableWidgetItem(encabezado[i])
                valor = QTableWidgetItem(str(encontrados[0][i]))
                self.tblPropiedades.setRowHeight(i, 9)
                self.tblPropiedades.setItem(i,0,propiedad)
                self.tblPropiedades.setItem(i,1,valor)
        if self.cmbPropiedades.currentText()[:10] == 'Suministro':
            conn = self.conn
            cursor = conn.cursor()
            if self.cmbPropiedades.currentText() == 'Suministro':
                cursor.execute("SELECT Geoname, COUNT(Suministros.id_suministro) AS Cant_Sum, COUNT(Usuarios.id_usuario) AS Cant_Usuarios FROM Elementos_Nodos LEFT OUTER JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt LEFT OUTER JOIN Usuarios RIGHT OUTER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro ON Nodos.Geoname = Suministros.id_nodo WHERE geoname=" + str(self.id_seleccionado) + " GROUP BY Nodos.Geoname")
            else:
                cursor.execute("SELECT 'Cant Usuarios' AS Tarifa, T1AP,T1GAC,T1GBC,T1R,T2BT,T2MT,T3BT,T3MT,T4NR,T4R,T5BT,T5MT,T6BT,T6MT FROM (SELECT Tarifas.id_OCEBA AS Tarifa, Usuarios.id_usuario FROM Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa WHERE (Usuarios.id_suministro = '" + self.cmbPropiedades.currentText()[11:] + "')) AS S PIVOT (COUNT(id_usuario) FOR Tarifa IN (T1AP,T1GAC,T1GBC,T1R,T2BT,T2MT,T3BT,T3MT,T4NR,T4R,T5BT,T5MT,T6BT,T6MT)) AS P")
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            if len(encontrados) > 0:
                self.tblPropiedades.setRowCount(1)
                n=1
                for i in range (1, len(encontrados[0])):
                    if encontrados[0][i]>0:
                        n=n+1
                self.tblPropiedades.setRowCount(n)
                j=0
                for i in range (0, len(encontrados[0])):
                    if i==0:
                        propiedad = QTableWidgetItem(encabezado[i])
                        valor = QTableWidgetItem(str(encontrados[0][i]))
                        self.tblPropiedades.setRowHeight(i, 9)
                        self.tblPropiedades.setItem(i,0,propiedad)
                        self.tblPropiedades.setItem(i,1,valor)
                    else:
                        if encontrados[0][i]>0:
                            j=j+1
                            propiedad = QTableWidgetItem(encabezado[i])
                            valor = QTableWidgetItem(str(encontrados[0][i]))
                            self.tblPropiedades.setRowHeight(j, 9)
                            self.tblPropiedades.setItem(j,0,propiedad)
                            self.tblPropiedades.setItem(j,1,valor)
        if self.cmbPropiedades.currentText() == 'Fuente' or self.cmbPropiedades.currentText() == 'Generador':
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(Descripcion, '') AS SSEE, Val1 AS Tension, Val5 AS tipo_generacion, Val4 FROM Nodos WHERE Nodos.Tension>0 AND geoname=" + str(self.id_seleccionado))
            #convierto el cursor en array
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            str_matriz = str(encontrados[0][3]).split("|")
            tipo_fuente = str_matriz[0]
            if tipo_fuente=='0':
                self.tblPropiedades.setRowCount(6)
            else:
                self.tblPropiedades.setRowCount(10)
            #-----------------------------------------------
            propiedad = QTableWidgetItem("SSEE")
            valor = QTableWidgetItem(encontrados[0][0])
            self.tblPropiedades.setRowHeight(0, 9)
            self.tblPropiedades.setItem(0,0,propiedad)
            self.tblPropiedades.setItem(0,1,valor)
            #-----------------------------------------------
            propiedad = QTableWidgetItem("Tension [V]")
            valor = QTableWidgetItem(encontrados[0][1])
            self.tblPropiedades.setRowHeight(1, 9)
            self.tblPropiedades.setItem(1,0,propiedad)
            self.tblPropiedades.setItem(1,1,valor)
            if tipo_fuente=='0':
                #-----------------------------------------------
                propiedad = QTableWidgetItem("Tipo")
                valor = QTableWidgetItem("Punto de Compra")
                self.tblPropiedades.setRowHeight(2, 9)
                self.tblPropiedades.setItem(2,0,propiedad)
                self.tblPropiedades.setItem(2,1,valor)
            else:
                #-----------------------------------------------
                propiedad = QTableWidgetItem("Tipo")
                valor = QTableWidgetItem("Generación")
                self.tblPropiedades.setRowHeight(2, 9)
                self.tblPropiedades.setItem(2,0,propiedad)
                self.tblPropiedades.setItem(2,1,valor)
            #-----------------------------------------------
            propiedad = QTableWidgetItem("Tipo_generacion")
            valor = QTableWidgetItem(encontrados[0][2])
            self.tblPropiedades.setRowHeight(3, 9)
            self.tblPropiedades.setItem(3,0,propiedad)
            self.tblPropiedades.setItem(3,1,valor)
            #-----------------------------------------------
            propiedad = QTableWidgetItem("Expediente")
            valor = QTableWidgetItem(str_matriz[1])
            self.tblPropiedades.setRowHeight(4, 9)
            self.tblPropiedades.setItem(4,0,propiedad)
            self.tblPropiedades.setItem(4,1,valor)
            #-----------------------------------------------
            propiedad = QTableWidgetItem("Scc [MVA]")
            valor = QTableWidgetItem(str_matriz[6])
            self.tblPropiedades.setRowHeight(5, 9)
            self.tblPropiedades.setItem(5,0,propiedad)
            self.tblPropiedades.setItem(5,1,valor)
            #-----------------------------------------------
            if tipo_fuente=='1':
                propiedad = QTableWidgetItem("P [kW]")
                valor = QTableWidgetItem(str_matriz[2])
                self.tblPropiedades.setRowHeight(5, 9)
                self.tblPropiedades.setItem(5,0,propiedad)
                self.tblPropiedades.setItem(5,1,valor)
                #-----------------------------------------------
                propiedad = QTableWidgetItem("Vmax [p.u.]")
                valor = QTableWidgetItem(str_matriz[3])
                self.tblPropiedades.setRowHeight(6, 9)
                self.tblPropiedades.setItem(6,0,propiedad)
                self.tblPropiedades.setItem(6,1,valor)
                #-----------------------------------------------
                propiedad = QTableWidgetItem("Qmax [kVAr]")
                valor = QTableWidgetItem(str_matriz[4])
                self.tblPropiedades.setRowHeight(7, 9)
                self.tblPropiedades.setItem(7,0,propiedad)
                self.tblPropiedades.setItem(7,1,valor)
                #-----------------------------------------------
                propiedad = QTableWidgetItem("Qmin [kVAr]")
                valor = QTableWidgetItem(str_matriz[5])
                self.tblPropiedades.setRowHeight(8, 9)
                self.tblPropiedades.setItem(8,0,propiedad)
                self.tblPropiedades.setItem(8,1,valor)
                #-----------------------------------------------
        if self.cmbPropiedades.currentText() == 'Capacitor':
            #strSql = "SELECT geoname, elmt FROM Nodos WHERE geoname=" + str(self.id_seleccionado)
            pass
        if self.cmbPropiedades.currentText() == 'Regulador':
            #strSql = "SELECT geoname, elmt FROM Nodos WHERE geoname=" + str(self.id_seleccionado)
            pass
        if self.cmbPropiedades.currentText() == 'Linea':
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT Geoname, Elementos_Lineas.Descripcion, Fase, CASE Val8 WHEN 'A' THEN 'Aéreo' WHEN 'S' THEN 'Subterráneo' WHEN 'P' THEN 'Preensamblado' ELSE 'Otro' END AS Tipo, Disposicion, Ternas, Conservacion, ROUND(Longitud, 2) AS Longitud, Tension, Zona, CASE WHEN CHARINDEX('-', Alimentador) > 0 THEN LEFT(Alimentador, CHARINDEX('-', Alimentador) - 1) ELSE Alimentador END AS Alimentador, CASE Acometida WHEN '0' THEN 'Línea' ELSE 'Acometida' END AS Uso, UUCC FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt = Elementos_Lineas.Id WHERE Geoname=" + str(self.id_seleccionado))
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            if len(encontrados) > 0:
                self.tblPropiedades.setRowCount(len(encontrados[0]))
            for i in range (0, len(encontrados[0])):
                propiedad = QTableWidgetItem(encabezado[i])
                valor = QTableWidgetItem(str(encontrados[0][i]))
                self.tblPropiedades.setRowHeight(i, 9)
                self.tblPropiedades.setItem(i,0,propiedad)
                self.tblPropiedades.setItem(i,1,valor)
                #propiedad.setFlags(valor.flags() & ~Qt.ItemIsEditable)
                #valor.setFlags(valor.flags() & ~Qt.ItemIsEditable)
                #if i == -1:
                #    valor.setFlags(valor.flags() | Qt.ItemIsEditable)
            #aca va a ver si tiene opciones de combo
            #cmbCelda = QComboBox()
            #cmbCelda.addItems(["Opción 1", "Opción 2", str(encontrados[i][j]), "Opción 3"])
            #cmbCelda.setCurrentIndex(2)
            #self.tblPropiedades.setCellWidget(i, j, cmbCelda)
        if self.cmbPropiedades.currentText() == 'Poste':
            #strSql = "SELECT geoname, elmt FROM Postes WHERE geoname=" + str(self.id_seleccionado)
            pass
        if self.cmbPropiedades.currentText() == 'Area':
            #strSql = "SELECT geoname, nombre FROM Areas WHERE geoname=" + str(self.id_seleccionado)
            pass
        if self.cmbPropiedades.currentText() == 'Parcela':
            #strSql = "SELECT geoname, parcela FROM Parcelas WHERE geoname=" + str(self.id_seleccionado)
            pass

    def conectar_db(self):
        if self.conn==None or self.conn.close:
            self.conn = pyodbc.connect(self.str_conexion)

    def run(self):
        if os.path.isdir('c:/gis/energis5/')==False:
            os.mkdir('c:/gis/energis5/')
        if self.energis_action.statusTip()=="Detenido":
            self.energis_action.setStatusTip("Iniciado")
            wt = str(self.energis_action.whatsThis())
            conexiones = wt.split('|')
            if len(conexiones)<2:
                return
            str_conexion = conexiones[0]
            self.str_conexion_seguridad = conexiones[1]
            self.nombre_modelo = QgsProject.instance().title()
            #----------------------------------------------
            self.timer = QTimer()
            self.timer.timeout.connect(self.detecto_cambio_seleccion)
            self.timer.start(500)  # 0.5 segundos
            #----------------------------------------------
        else:
            self.energis_action.setStatusTip("Detenido")
            str_conexion = ""
            try:
                self.timer.stop()
            except:
                pass

        if self.energis_action.statusTip()=="Iniciado":
            try:
                if str_conexion!="":
                    self.str_conexion = str_conexion
                    self.actualizar_base_datos()
                else:
                    return
            except:
                QMessageBox.critical(None, 'EnerGis 5', 'No se pudo conectar al modelo ' + str_conexion)
                self.energis_action.setStatusTip("Detenido")
                str_conexion = ""
                return
            cursor = self.conn.cursor()
            cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
            rows = cursor.fetchall()
            cursor.close()
            self.srid = rows[0][0]
            #Creo barras de herramientas
            self.actions = []
            self.menu = ('EnerGIS')
            self.iface.mainWindow().addToolBarBreak()
            self.toolbar_h = self.iface.addToolBar('EnerGis Dibujo')
            #------------------------------------------
            #Creo paneles
            # Crear el DockWidget 1 - Panel de Propiedades
            #try:
            self.dock_widget = QDockWidget('Propiedades', self.iface.mainWindow())
            self.dock_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
            self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            # Agregar varios widgets al layout
            self.cmbPropiedades = QComboBox()
            self.tblPropiedades = QTableWidget()
            dock_widget_content = QWidget()
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)  # Márgenes: izquierdo, superior, derecho, inferior
            layout.addWidget(self.cmbPropiedades)
            layout.addWidget(self.tblPropiedades)
            # Configurar el contenido del DockWidget
            dock_widget_content.setLayout(layout)
            #except:
            #    pass
            # Agregar el contenido al QDockWidget
            self.dock_widget.setWidget(dock_widget_content)
            #self.dock_widget.setMinimumHeight(300)
            self.dock_widget.resize(self.dock_widget.width(), 300)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
            #------------------------------------------
            # Crear el DockWidget 2 - Panel de Nuevos Usuarios
            try:
                self.dock_widget2 = QDockWidget('Usuarios Nuevos', self.iface.mainWindow())
                self.dock_widget2.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
                self.dock_widget2.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
                # Crear el widget principal
                dock_widget_content = QWidget()
                layout = QVBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)  # Márgenes: izquierdo, superior, derecho, inferior
                dock_widget_content.setLayout(layout)
            except:
                pass
            # 1. Agregar un menú en la parte superior
            menu_bar = QMenuBar()
            m_acciones = menu_bar.addMenu('Acciones')
            action = QAction('Separar Usuarios del Suministro', self.iface.mainWindow())
            action.triggered.connect(self.m_separar_suministros)
            m_acciones.addAction(action)
            action = QAction('Seleccionar Suministros sin Usuarios', self.iface.mainWindow())
            action.triggered.connect(self.m_suministros_sin_usuarios)
            m_acciones.addAction(action)
            m_dibujar = menu_bar.addMenu('Dibujar')
            action = QAction('Suministros con Coordenadas Externas', self.iface.mainWindow())
            action.triggered.connect(self.m_suministros_con_coordenadas_externas)
            m_dibujar.addAction(action)
            action = QAction('Suministros con Ejes de Calle', self.iface.mainWindow())
            action.triggered.connect(self.m_suministros_con_ejes_de_calle)
            m_dibujar.addAction(action)
            action = QAction('Suministros por Catastro', self.iface.mainWindow())
            action.triggered.connect(self.m_suministros_por_catastro)
            m_dibujar.addAction(action)
            m_dibujar.addSeparator()
            action = QAction('Conectar Suministros Aislados', self.iface.mainWindow())
            action.triggered.connect(self.m_conectar_suministros_aislados)
            m_dibujar.addAction(action)
            layout.addWidget(menu_bar)
            # 2. Agregar un QTableWidget debajo del menú
            self.tblUsuariosNuevos = QTableWidget()  # Crear una tabla
            self.tblUsuariosNuevos. setAlternatingRowColors(True)
            #self.tblUsuariosNuevos.setSortingEnabled(True)
            # 3. Agregar el primer QHBoxLayout con dos QTextEdit
            hbox_layout1 = QHBoxLayout()
            self.txtUsuario = QLineEdit("")
            self.txtUsuario.setReadOnly(True)  # Hacer solo lectura
            self.txtNombre = QLineEdit("")
            self.txtNombre.setReadOnly(True)  # Hacer solo lectura
            hbox_layout1.addWidget(self.txtUsuario)
            hbox_layout1.addWidget(self.txtNombre)
            # Establecer los tamaños de los textos
            hbox_layout1.setStretch(0, 3)  # txtUsuario ocupa 3 partes
            hbox_layout1.setStretch(1, 7)  # txtNombre ocupa 7 partes
            # 4. Agregar el segundo QHBoxLayout con dos QTextEdit
            hbox_layout2 = QHBoxLayout()
            self.txtCalle = QLineEdit("")
            self.txtCalle.setReadOnly(True)  # Hacer solo lectura
            self.txtNumero = QLineEdit("")
            self.txtNumero.setReadOnly(True)  # Hacer solo lectura
            hbox_layout2.addWidget(self.txtCalle)
            hbox_layout2.addWidget(self.txtNumero)
            # Establecer los tamaños de los textos
            hbox_layout2.setStretch(0, 7)  # txtCalle ocupa 7 partes
            hbox_layout2.setStretch(1, 3)  # txtNumero ocupa 3 partes
            # 5. Agregar el tercer QHBoxLayout con dos QPushButton
            hbox_layout3 = QHBoxLayout()
            self.cmdActualizar = QPushButton("Actualizar")
            self.cmdAproximar = QPushButton("Aproximar")
            hbox_layout3.addWidget(self.cmdActualizar)
            hbox_layout3.addWidget(self.cmdAproximar)
            # Agregar un espacio flexible después de los botones
            hbox_layout3.addStretch()
            # Configurar layout principal con stretch
            layout.addWidget(self.tblUsuariosNuevos)
            layout.setStretch(1, 8)  # QTableWidget ocupa 8 partes
            layout.addLayout(hbox_layout1)
            layout.setStretch(2, 1)  # Primer QHBoxLayout ocupa 1 parte
            layout.addLayout(hbox_layout2)
            layout.setStretch(3, 1)  # Segundo QHBoxLayout ocupa 1 parte
            layout.addLayout(hbox_layout3)
            layout.setStretch(4, 1)  # Tercer QHBoxLayout ocupa 1 parte
            self.cmdActualizar.clicked.connect(self.actualizar_usuarios)
            self.cmdAproximar.clicked.connect(self.aproximar_usuarios)            
            # Configurar el contenido del DockWidget
            dock_widget_content.setLayout(layout)
            # Agregar el contenido al QDockWidget
            self.dock_widget2.setWidget(dock_widget_content)
            #self.dock_widget2.setMinimumHeight(300)
            self.dock_widget2.resize(self.dock_widget2.width(), 300)
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget2)
            font = QFont()
            font.setPointSize(8)
            self.tblUsuariosNuevos.setFont(font)
            self.tblUsuariosNuevos.verticalHeader().setVisible(False)
            self.tblUsuariosNuevos.setColumnCount(4)
            self.tblUsuariosNuevos.setHorizontalHeaderLabels(['Calle','Numero','Ruta','Suministro'])
            self.dock_widget2.resize(self.dock_widget2.width(), 260)
            self.tblUsuariosNuevos.setRowCount(0)
            self.tblUsuariosNuevos.clicked.connect(self.elijo_suministro)
            self.dock_widget2.setVisible(False)
            #------------------------------------------
            main_window = self.iface.mainWindow()
            self.toolbar_v = QToolBar('EnerGis Busqueda')
            self.toolbar_v.setOrientation(Qt.Vertical)
            main_window.addToolBar(Qt.LeftToolBarArea, self.toolbar_v)
            self.toolbar_p = QToolBar('EnerGis Proyectos')
            self.toolbar_e = self.iface.addToolBar('EnerGis Ejes')
            main_window.addToolBar(Qt.BottomToolBarArea, self.toolbar_p)
            main_window.addToolBar(Qt.BottomToolBarArea, self.toolbar_e)
            #self.elijo_tension()
            #------------------------------------------
            #icon = QIcon(os.path.join(basepath,"icons", 'img_vivo.png'))
            #self.action_vivo = QAction(icon, 'Vivo', None)
            #self.action_vivo.triggered.connect(self.vivo)
            #self.action_vivo.setCheckable(True)
            #self.action_vivo.setChecked(True)
            #self.toolbar_h.addAction(self.action_vivo)
            #------------------------------------------
            inicio = QtWidgets.QPushButton("Menú")
            self.toolbar_h.addWidget(inicio)
            menu = QtWidgets.QMenu()
            #------------------------------------------
            self.m_listados = menu.addMenu('Listados')
            #------------------------------------------
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_seccionador.png')), 'Elem. de Prot. y Maniobra', self.iface.mainWindow())
            action.triggered.connect(self.listado_seccionadores)
            self.m_listados.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_poste.png')), 'Postes', self.iface.mainWindow())
            action.triggered.connect(self.listado_postes)
            self.m_listados.addAction(action)
            #------------------------------------------
            self.m_listado_transformadores = self.m_listados.addMenu('Transformadores')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Centros de Transformación', self.iface.mainWindow())
            action.triggered.connect(self.listado_cts)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Transformadores', self.iface.mainWindow())
            action.triggered.connect(self.listado_transformadores)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Transformadores en la Red', self.iface.mainWindow())
            action.triggered.connect(self.listado_transformadores_red)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Movimientos de Transformadores', self.iface.mainWindow())
            action.triggered.connect(self.listado_movimiento_transformadores)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Movimientos de un Transformador', self.iface.mainWindow())
            action.triggered.connect(self.listado_movimientos_trafo)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Movimientos en un CT', self.iface.mainWindow())
            action.triggered.connect(self.listado_movimientos_ct)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            self.m_listado_usuarios = self.m_listados.addMenu('Usuarios')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_usuarios.png')), 'Usuarios', self.iface.mainWindow())
            action.triggered.connect(self.listado_usuarios)
            self.m_listado_usuarios.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_usuarios.png')), 'Usuarios en la Red', self.iface.mainWindow())
            action.triggered.connect(self.listado_usuarios_red)
            self.m_listado_usuarios.addAction(action)
            #------------------------------------------
            self.m_listado_usuarios = self.m_listados.addMenu('Líneas')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_linea.png')), 'Lineas', self.iface.mainWindow())
            action.triggered.connect(self.listado_lineas)
            self.m_listado_usuarios.addAction(action)
            #------------------------------------------
            self.m_analisis = menu.addMenu('Análisis')
            #------------------------------------------
            #action = QAction(QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Carga de Transformadores', self.iface.mainWindow())
            #action.triggered.connect(self.analisis_carga)
            #self.m_analisis.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_usuarios.png')), 'Cálculo de Cargas', self.iface.mainWindow())
            action.triggered.connect(self.calculo_cargas)
            self.m_analisis.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_caida_tension.png')), 'Momentos Eléctricos', self.iface.mainWindow())
            action.triggered.connect(self.momentos_electricos)
            self.m_analisis.addAction(action)
            #------------------------------------------
            self.m_modelo = menu.addMenu('Modelo')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_energias.png')), 'Resumen Sistema', self.iface.mainWindow())
            action.triggered.connect(self.resumen_sistema)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_verificar.png')), 'Reiniciar Conectividad', self.iface.mainWindow())
            action.triggered.connect(self.crear_red)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_seccionador.png')), 'Llevar Red al Estado Normal', self.iface.mainWindow())
            action.triggered.connect(self.red_a_estado_normal)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_seccionador.png')), 'Definir Configuración Actual como Normal', self.iface.mainWindow())
            action.triggered.connect(self.establecer_estado_normal)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_seccionador.png')), 'Ver Elementos en Estado Distinto al Normal', self.iface.mainWindow())
            action.triggered.connect(self.ver_elementos_estado_anormal)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_vertices.png')), 'Actualizar Postes de Líneas', self.iface.mainWindow())
            action.triggered.connect(self.actualizar_postes_lineas)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_area.png')), 'Actualizar Zonas', self.iface.mainWindow())
            action.triggered.connect(self.actualizar_zonas)
            self.m_modelo.addAction(action)
            #------------------------------------------
            if self.tipo_navegacion!=0:
                action = QAction(QIcon(os.path.join(basepath,"icons", 'img_caida_tension.png')), 'Actualizar Alimentadores', self.iface.mainWindow())
                action.triggered.connect(self.actualizar_alimentadores)
                self.m_modelo.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Transformadores en Almacén', self.iface.mainWindow())
            action.triggered.connect(self.transformadores_almacen)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Centros de Transformación', self.iface.mainWindow())
            action.triggered.connect(self.centros_transformacion)
            self.m_modelo.addAction(action)
            #------------------------------------------
            self.m_exportar = self.m_modelo.addMenu('Exportar')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_esri.png')), 'ESRI shp', self.iface.mainWindow())
            action.triggered.connect(self.exportar_esri)
            self.m_exportar.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_mapinfo')), 'MapInfo tab', self.iface.mainWindow())
            action.triggered.connect(self.exportar_mapinfo)
            self.m_exportar.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_qfield.png')), 'QField', self.iface.mainWindow())
            action.triggered.connect(self.exportar_qfield)
            self.m_exportar.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_coordenadas.png')), 'Google', self.iface.mainWindow())
            action.triggered.connect(self.exportar_google)
            self.m_exportar.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_linea.png')), 'Demitec', self.iface.mainWindow())
            action.triggered.connect(self.exportar_demitec)
            self.m_exportar.addAction(action)
            #------------------------------------------
            #action = QAction(QIcon(os.path.join(basepath,"icons", 'img_editar.png')), 'Texto', self.iface.mainWindow())
            #action.triggered.connect(self.exportar_txt)
            #self.m_exportar.addAction(action)
            #------------------------------------------
            self.m_importar = self.m_modelo.addMenu('Importar')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_access.png')), 'MS Access', self.iface.mainWindow())
            action.triggered.connect(self.importar_access)
            self.m_importar.addAction(action)
            #------------------------------------------
            self.m_administrador = menu.addMenu('Administrador')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_sql.png')), 'Ejecutar SQL', self.iface.mainWindow())
            action.triggered.connect(self.ejecutar_sql)
            self.m_administrador.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_seguridad.png')), 'Seguridad', self.iface.mainWindow())
            action.triggered.connect(self.seguridad)
            self.m_administrador.addAction(action)
            #------------------------------------------
            if self.tipo_navegacion==0:
                action = QAction(QIcon(os.path.join(basepath,"icons", 'abajo.png')), 'Actualizar a .NET', self.iface.mainWindow())
                action.triggered.connect(self.actualizar_a_net)
                self.m_administrador.addAction(action)
            #------------------------------------------
            self.m_archivos = menu.addMenu('Datos Comerciales')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_usuarios3.png')), 'Usuarios (OCEBA)', self.iface.mainWindow())
            action.triggered.connect(self.importar_usuarios_oceba)
            self.m_archivos.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_energias.png')), 'Energias Facturadas (DPE)', self.iface.mainWindow())
            action.triggered.connect(self.importar_energias_dpe)
            self.m_archivos.addAction(action)
            #------------------------------------------
            self.m_oceba = menu.addMenu('OCEBA')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Transformadores Res 811', self.iface.mainWindow())
            action.triggered.connect(self.res_811)
            self.m_oceba.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_usuarios.png')), 'Usuarios', self.iface.mainWindow())
            action.triggered.connect(self.exportar_usuarios_oceba)
            self.m_oceba.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'CTs', self.iface.mainWindow())
            action.triggered.connect(self.cts_oceba)
            self.m_oceba.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_caida_tension.png')), 'Cadena Eléctrica 1', self.iface.mainWindow())
            action.triggered.connect(self.cadena1)
            self.m_oceba.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_caida_tension.png')), 'Cadena Eléctrica 2', self.iface.mainWindow())
            action.triggered.connect(self.cadena2)
            self.m_oceba.addAction(action)
            #------------------------------------------
            self.m_dpe = menu.addMenu('DPE')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_provincia.png')), 'kml DPE', self.iface.mainWindow())
            action.triggered.connect(self.exportar_kml)
            self.m_dpe.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_provincia.png')), 'Res2/2022', self.iface.mainWindow())
            action.triggered.connect(self.exportar_dpe)
            self.m_dpe.addAction(action)
            #------------------------------------------
            inicio.setMenu(menu)
            #------------------------------------------
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_usuarios.png'), 'Usuarios', self.usuarios, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_verificar.png'), 'Verificar Red', self.h_verificar_red, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_elementos_seleccionados.png'), 'Ubicar Selección', self.h_elementos_seleccionados, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_seleccion.png'), 'Selección', self.h_seleccion, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_seleccion_aleatoria.png'), 'Selección por Area', self.h_seleccion_aleatoria, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_seleccion_circular.png'), 'Selección Circular', self.h_seleccion_circular, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_seleccionar_elementos.png'), 'Seleccionar Elementos', self.h_seleccionar_elementos, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            #--------------------------------------------------
            self.cmbTension  = QComboBox(self.iface.mainWindow())
            #--------------------------------------------------
            cursor = self.conn.cursor()
            cursor.execute("SELECT Tension FROM Niveles_Tension WHERE Tension>=50")
            #convierto el cursor en array
            self.tensiones = tuple(cursor)
            cursor.close()
            self.cmbTension.clear()
            for t in range (0, len(self.tensiones)):
                self.cmbTension.addItem(str(self.tensiones[t][0]))
            n = self.iface.mapCanvas().layerCount()
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Nodos Proyectos' or lyr.name() == 'Lineas Proyectos' or lyr.name() == 'Postes Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'@@'")
                if lyr.name() == 'Cotas':
                    lyr.setSubsetString('"proyecto" = ' + "'@@'")
            #--------------------------------------------------
            self.cmbTensionAction = self.toolbar_h.addWidget(self.cmbTension)
            self.cmbTension.currentIndexChanged.connect(self.elijo_tension)
            self.cmbTension.setToolTip("Capa")
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_nodo.png'), 'Nodo', self.h_nodo, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_linea.png'), 'Linea', self.h_linea, True, False, True, True, None, None, self.iface.mainWindow())
            #boton desplegable
            self.tool_button = QtWidgets.QToolButton()
            self.tool_button.setText("Vertices")
            self.tool_button.setIcon(QIcon(os.path.join(basepath,"icons", 'img_vertices.png')))
            menu_boton = QtWidgets.QMenu()
            self.vertices_1 = QAction(QIcon(os.path.join(basepath,"icons", 'img_agregar_vertice.png')), 'Agregar Vertice', self.toolbar_h)
            self.vertices_2 = QAction(QIcon(os.path.join(basepath,"icons", 'img_quitar_vertice.png')), 'Borrar Vertice', self.toolbar_h)
            self.vertices_1.triggered.connect(self.h_agregar_vertice)
            self.vertices_2.triggered.connect(self.h_quitar_vertice)
            menu_boton.addAction(self.vertices_1)
            menu_boton.addAction(self.vertices_2)
            self.tool_button.setMenu(menu_boton)
            self.tool_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
            self.toolbar_h.addWidget(self.tool_button)
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_conectar.png'), 'Conectar', self.h_conectar, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_poste.png'), 'Poste', self.h_poste, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_area.png'), 'Area', self.h_area, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_parcela.png'), 'Parcela', self.h_parcela, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_anotacion.png'), 'Anotacion', self.h_anotacion, True, False, True, True, None, None, self.iface.mainWindow())
            #self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_girar.png'), 'Girar', self.h_girar, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_mover.png'), 'Mover', self.h_mover, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_rotar.png'), 'Rotar', self.h_rotar, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_borrar.png'), 'Borrar', self.h_borrar, True, False, True, True, None, None, self.iface.mainWindow())
            #--------------------------------------------------
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_zoom.png'), 'Zoom', self.h_zoom, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_pan.png'), 'Pan', self.h_Pan, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_buscar.png'), 'Buscar', self.h_buscar, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_buscar_direccion.png'), 'Buscar Direccion', self.h_buscar_direccion, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_nav_fuente.png'), 'Navegar a la Fuente', self.h_navegar_a_la_fuente, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_nav_extremos.png'), 'Navegar a los Extremos', self.h_navegar_extremos, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_desconectados.png'), 'Desconectados', self.h_desconectados, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_aislados.png'), 'Aislados', self.h_aislados, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_loops.png'), 'Loops', self.h_loops, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_reclamos.png'), 'Reclamos', self.h_reclamos, True, True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_contingencias.png'), 'Contingencias', self.carga_contingencias, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            if self.modulo_calculos==1:
                #boton desplegable
                self.tool_button = QtWidgets.QToolButton()
                self.tool_button.setText("Vertices")
                self.tool_button.setIcon(QIcon(os.path.join(basepath,"icons", 'img_calculadora.png')))
                menu_boton = QtWidgets.QMenu()
                self.flujo = QAction(QIcon(os.path.join(basepath,"icons", 'img_caida_tension.png')), 'Flujo de Cargas', self.toolbar_v)
                #self.flujo_3f = QAction(QIcon(os.path.join(basepath,"icons", 'img_flujo3f.png')), 'Flujo Desequilibrado', self.toolbar_v)
                self.corto = QAction(QIcon(os.path.join(basepath,"icons", 'img_corto.png')), 'Cortocircuito', self.toolbar_v)
                self.flujo.triggered.connect(self.h_flujo)
                #self.flujo_3f.triggered.connect(self.h_flujo_desequilibrado)
                self.corto.triggered.connect(self.h_cortocircuito)
                menu_boton.addAction(self.flujo)
                #menu_boton.addAction(self.flujo_3f)
                menu_boton.addAction(self.corto)
                self.tool_button.setMenu(menu_boton)
                self.tool_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
                self.toolbar_v.addWidget(self.tool_button)
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_usuario.png'), 'Usuarios Nuevos', self.h_usuarios_nuevos, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_electrodependientes.png'), 'Usuarios Electrodependientes', self.h_electrodependientes, True, True, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_resultado_seleccion.png'), 'Datos de la Selección', self.h_datos_seleccion, True, False, True, True, None, None, self.iface.mainWindow())
            #--------------------------------------------------
            self.cmbProyecto = QComboBox(self.iface.mainWindow())
            #--------------------------------------------------
            cursor = self.conn.cursor()
            cursor.execute("SELECT Nombre FROM Proyectos")
            #convierto el cursor en array
            proyectos = tuple(cursor)
            cursor.close()
            self.cmbProyecto.clear()
            self.cmbProyecto.addItem("<Proyecto>")
            for p in range (0, len(proyectos)):
                self.cmbProyecto.addItem(str(proyectos[p][0]))
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_nuevo.png'), 'Nuevo Proyecto', self.h_crear_proyecto, True, False, True, True, None, None, self.iface.mainWindow())
            #--------------------------------------------------
            self.cmbProyectoAction = self.toolbar_p.addWidget(self.cmbProyecto)
            self.cmbProyecto.currentIndexChanged.connect(self.elijo_proyecto)
            self.cmbProyecto.setToolTip("Proyecto")
            self.cmbProyecto.setFixedWidth(200)
            #--------------------------------------------------
            self.toolbar_p.addSeparator()
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_editar.png'), 'Modificar Proyecto', self.h_editar_proyecto, True, True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_incorporar.png'), 'Incorporar Proyecto', self.h_incorporar_proyecto, False, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_quitar.png'), 'Borrar Proyecto', self.h_borrar_proyecto, False, False, True, True, None, None, self.iface.mainWindow())
            #--------------------------------------------------
            self.toolbar_p.addSeparator()
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_cotas.png'), 'Agregar Cota', self.h_cotas, False, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_borrar_ultima_cota.png'), 'Borrar última Cota', self.h_borrar_ultima_cota, False, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_borrar_cotas.png'), 'Borrar Cotas', self.h_borrar_cotas, False, False, True, True, None, None, self.iface.mainWindow())
            for action in self.actions:
                if str(action.text())=='Modificar Proyecto':
                    action.setEnabled(False)
            #Esta etiqueta va ultima
            #--------------------------------------------------
            #self.lblTension = QLabel(self.iface.mainWindow())
            #--------------------------------------------------
            #self.lblTension.setText('0')
            #self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_nuevo.png'), 'Tension', self.h_crear_proyecto, True, False, True, True, None, None, self.iface.mainWindow())
            #--------------------------------------------------
            #self.lblTensionAction = self.toolbar_p.addWidget(self.lblTension)
            #self.lblTension.setToolTip("Proyecto")
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_seleccion_ejes.png'), 'Seleccionar Eje', self.h_seleccionar_ejes, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_eje.png'), 'Eje de Calle', self.h_eje, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_editar_ejes.png'), 'Cargar Datos', self.h_datos_eje, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_mover.png'), 'Mover Ejes', self.h_mover_ejes, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_rotar.png'), 'Rotar Ejes', self.h_rotar_ejes, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_borrar.png'), 'Borrar Eje de Calle', self.h_borrar_ejes, True, False, True, True, None, None, self.iface.mainWindow())
            self.actualizar_db()
            self.h_login()
            self.iface.mapCanvas().setMapTool(None)
        else:
            try:
                main_window = self.iface.mainWindow()
                self.toolbar_h.deleteLater()
                self.toolbar_p.deleteLater()
                self.toolbar_e.deleteLater()
                self.toolbar_v.deleteLater()
                self.dock_widget.deleteLater()
                self.dock_widget2.deleteLater()
            except:
                pass
        self.descargo_red()
        self.h_seleccion()

    def actualizar_base_datos(self):
        self.tipo_navegacion=0
        self.modulo_calculos=0
        try:
            import clr
            clr.AddReference("mscorlib")
            clr.AddReference("System")
            clr.AddReference(os.path.join(basepath, 'NavRed7.dll'))
            from EnerGis5.NavRed7 import NavRed
            from System import Int64
            prueba = Int64(self.tipo_navegacion)
            self.tipo_navegacion=1
        except:
            pass
        #pandas pandapower sqlalchemy numba numpy
        try:
            import pandas as pd
            import pandapower as pp
            prueba = pd.DataFrame()
            self.modulo_calculos=1
        except:
            pass

        self.conectar_db()
        conn = self.conn
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM lineas WHERE desde=0 OR hasta=0 OR desde=hasta")
            conn.commit()
        except:
            conn.rollback()

    def actualizar_a_net(self):
        qgis_path = QgsApplication.applicationDirPath()
        try:
            f = open('c:/gis/energis5/install_pip.bat','w')
            f.writelines("cd " + qgis_path + "/.." +  "\n")
            f.writelines("OSGeo4W.bat python3.exe -m pip install --upgrade pip" + "\n")
            f.writelines("exit" + "\n")
            f.close()
            subprocess.run('c:/gis/energis5/install_pip.bat')
            #--------------------------------------------------
            f = open('c:/gis/energis5/install_pyodbc.bat','w')
            f.writelines("cd " + qgis_path + "/.." +  "\n")
            f.writelines("OSGeo4W.bat pip install pyodbc" + "\n")
            f.writelines("exit" + "\n")
            f.close()
            subprocess.run('c:/gis/energis5/install_pyodbc.bat')
            #--------------------------------------------------
            f = open('c:/gis/energis5/install_matplotlib.bat','w')
            f.writelines("cd " + qgis_path + "/.." +  "\n")
            f.writelines("OSGeo4W.bat pip install matplotlib" + "\n")
            f.writelines("exit" + "\n")
            f.close()
            subprocess.run('c:/gis/energis5/install_matplotlib.bat')
            #--------------------------------------------------
            f = open('c:/gis/energis5/install_pythonnet.bat','w')
            f.writelines("cd " + qgis_path + "/.." +  "\n")
            f.writelines("OSGeo4W.bat pip install pythonnet" + "\n")
            f.writelines("exit" + "\n")
            f.close()
            subprocess.run('c:/gis/energis5/install_pythonnet.bat')
            #--------------------------------------------------
            f = open('c:/gis/energis5/install_xlwt.bat','w')
            f.writelines("cd " + qgis_path + "/.." +  "\n")
            f.writelines("OSGeo4W.bat pip install xlwt" + "\n")
            f.writelines("exit" + "\n")
            f.close()
            subprocess.run('c:/gis/energis5/install_xlwt.bat')
            #--------------------------------------------------
            #subprocess.run('winget install Microsoft.DotNet.DesktopRuntime.6')
            subprocess.run('winget install Microsoft.DotNet.DesktopRuntime.9')
            #--------------------------------------------------
            QMessageBox.warning(None, 'EnerGis 5', "Actualizado !")
        except:
            QMessageBox.warning(None, 'EnerGis 5', "No se pudo instalar el entorno !")

            self.tipo_navegacion=0
            try:
                import clr
            except:
                QMessageBox.warning(None, 'EnerGis 5', "No se pudo importar clr !")
            try:
                clr.AddReference("mscorlib")
            except:
                QMessageBox.warning(None, 'EnerGis 5', "No se pudo agregar mscorlib !")
            try:
                clr.AddReference("System")
            except:
                QMessageBox.warning(None, 'EnerGis 5', "No se pudo agregar el System !")
            try:
                clr.AddReference(os.path.join(basepath, 'NavRed7.dll'))
            except:
                QMessageBox.warning(None, 'EnerGis 5', "No se pudo agregar " + os.path.join(basepath, 'NavRed7.dll') + " !")
            try:
                from EnerGis5.NavRed7 import NavRed
            except:
                QMessageBox.warning(None, 'EnerGis 5', "No se pudo importar NavRed !")
            try:
                from System import Int64
            except:
                QMessageBox.warning(None, 'EnerGis 5', "No se pudo importar Int64 !")
            try:
                prueba = Int64(self.tipo_navegacion)
            except:
                QMessageBox.warning(None, 'EnerGis 5', "No se pudo cargar la prueba !")
                self.tipo_navegacion=1
            try:
                import System
            except:
                QMessageBox.warning(None, 'EnerGis 5', "No se pudo importar System !")
                QMessageBox.warning(None, 'EnerGis 5', "Ver en: " + str(System._path_))

    def agregar_herramienta(self, toolbar, icon_path, text, callback, enabled_flag, checkable_flag, add_to_menu, add_to_toolbar, status_tip, whats_this, parent):
        try:
            icon = QIcon(icon_path)
            action = QAction(icon, text, parent)
            action.triggered.connect(callback)
            action.setEnabled(enabled_flag)
            action.setCheckable(checkable_flag)
            if status_tip is not None:
                action.setStatusTip(status_tip)
            if whats_this is not None:
                action.setWhatsThis(whats_this)
            if add_to_toolbar:
                toolbar.addAction(action)
            if add_to_menu:
                #self.iface.addPluginToVectorMenu(self.menu, action)
                pass
            self.actions.append(action)
            return action
        except:
            return None

    def unload(self):
        self.iface.removeToolBarIcon(self.energis_action)
        try:
            self.toolbar_h.deleteLater()
            main_window = self.iface.mainWindow()
            main_window.removeToolBar(self.toolbar_p)
            main_window.removeToolBar(self.toolbar_v)
            self.toolbar_p.deleteLater()
            self.toolbar_v.deleteLater()
            self.iface.mapCanvas().setMapTool(None)
        except:
            pass

    def elijo_tension(self):
        self.tension = self.cmbTension.currentText()
        #Si cambio de tension despues de elegir la herramienta, queda seteada en la herramienta la tension anterior
        # Obtener la herramienta actual del canvas del mapa
        current_map_tool = str(self.iface.mapCanvas().mapTool())
        indice = current_map_tool.find('herrNodo')
        if indice != -1:
            self.h_nodo()
        indice = current_map_tool.find('herrLinea')
        if indice != -1:
            self.h_linea()
        indice = current_map_tool.find('herrPoste')
        if indice != -1:
            self.h_poste()

    def usuarios(self):
        from .frm_datos_usuarios import frmDatosUsuarios
        self.dialogo = frmDatosUsuarios(self.conn, 0)
        self.dialogo.show()

    def carga_contingencias(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        if self.tipo_usuario==4:
            return
        if self.tipo_navegacion==0:
            from .mod_navegacion_ant import nodos_por_transformador
            nodos_por_transformador(self, self.conn)
            from .frm_contingencias_ant import frmContingencias
            self.dialogo = frmContingencias(self.conn, self.iface.mapCanvas(), self.tipo_usuario, self.red_verificada)
            self.dialogo.show()

        else:
            from .frm_contingencias import frmContingencias
            self.dialogo = frmContingencias(self.conn, self.iface.mapCanvas(), self.tipo_usuario, self.mnodos, self.mlineas, self.red_verificada)
            self.dialogo.show()

    def listado_lineas(self):
        from .frm_listado_lineas import frmListadoLineas
        self.dialogo = frmListadoLineas(self.conn)
        self.dialogo.show()

    def listado_seccionadores(self):
        str_sql = "SELECT Nodos.Geoname As id_nodo, Nodos.Nombre As secc, Nodos.Val1 As tipo, Nodos.Val2 As subtipo, Nodos.Val3 As fusible, Nodos.Val4 As marca, Nodos.Val5 As modelo, Nodos.Nivel As nivel, Nodos.Tension As tension, Nodos.Zona As zona, Nodos.Alimentador As alimentador, Nodos.XCoord As x, Nodos.YCoord As y FROM Nodos WHERE Nodos.Tension>0 AND Nodos.Elmt = 2 Or Nodos.Elmt = 3"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de Seccionadores")
        self.dialogo.show()

    def listado_postes(self):
        str_sql = "SELECT Postes.Geoname AS id_poste, Elementos_Postes.Descripcion AS material, Estructuras.Descripcion AS estructura, Postes.Altura, Riendas.Descripcion AS rienda, Lineas.Zona AS zona, Lineas.Alimentador AS alimentador, Lineas.Tension AS tension, Postes.XCoord AS x, Postes.YCoord AS y FROM (Lineas_Postes INNER JOIN (Riendas RIGHT JOIN ((Postes LEFT JOIN Elementos_Postes ON Postes.Elmt = Elementos_Postes.Id) LEFT JOIN Estructuras ON Postes.Estructura = Estructuras.Id) ON Riendas.Id = Postes.Rienda) ON Lineas_Postes.id_poste = Postes.Geoname) INNER JOIN Lineas ON Lineas_Postes.id_linea = Lineas.Geoname"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de Postes")
        self.dialogo.show()

    def listado_cts(self):
        str_sql = "SELECT Transformadores.Id_trafo AS id_trafo, Nodos.Geoname AS id_nodo, Ct.id_ct, Ct.Ubicacion AS ubicacion, Transformadores.Potencia AS potencia, Transformadores.Tension_1 AS v1, Transformadores.Tension_2 AS v2, Tipo_Trafo.Tipo AS tipo_trafo, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_chapa AS nro_chapa, Transformadores.Obs AS Observaciones, Transformadores.Anio_fabricacion AS año, Ct.Mat_plataf AS plataforma, Ct.Tipo_ct AS tipo_ct, Nodos.Nivel AS nivel, Nodos.Tension AS tension_nodo, Nodos.Zona AS zona, Nodos.Alimentador AS alimentador_mt, Nodos.XCoord AS x, Nodos.YCoord AS y, Transformadores.Kit AS kit, Transformadores.Cromatografia AS cromatografia, Transformadores.Anomalia AS anomalia, Transformadores.Fecha_norm AS fecha_norm, Transformadores.Obs_pcb AS observaciones_pcb FROM Tipo_Trafo INNER JOIN Transformadores ON Tipo_Trafo.Numero = Transformadores.Tipo RIGHT OUTER JOIN Nodos RIGHT OUTER JOIN Ct ON Nodos.Nombre = Ct.Id_ct ON Transformadores.Id_ct = Ct.Id_ct WHERE Nodos.Elmt = 4 ORDER BY Ct.Id_ct"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de CTs")
        self.dialogo.show()

    def listado_transformadores(self):
        str_sql = "SELECT Transformadores.Id_trafo AS id_trafo, Transformadores.id_ct AS id_ct, Ubicaciones.Descripcion AS [ubicado en], Ct.Ubicacion AS ubicacion, Transformadores.Potencia AS potencia, Transformadores.Tension_1 AS v1, Transformadores.Tension_2 AS v2, Tipo_Trafo.Tipo AS tipo_trafo, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_chapa AS nro_chapa, Transformadores.Anio_fabricacion AS año, Ct.Mat_plataf AS plataforma, Ct.Tipo_Ct AS tipo_ct, Transformadores.Kit AS kit, Transformadores.Cromatografia AS cromatografia, Transformadores.Anomalia AS anomalia, Transformadores.Fecha_norm AS fecha_norm, Transformadores.Obs_pcb AS observaciones_pcb FROM ((Tipo_Trafo INNER JOIN Transformadores ON Tipo_Trafo.Numero = Transformadores.Tipo) LEFT JOIN Ct ON Transformadores.id_ct = Ct.id_ct) LEFT JOIN Ubicaciones ON Transformadores.Usado = Ubicaciones.Id_Ubicacion"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de Transformadores")
        self.dialogo.show()

    def listado_transformadores_red(self):
        str_sql = "SELECT Transformadores.Id_trafo AS id_trafo, Nodos.Geoname AS id_nodo, Nodos.Nombre AS id_ct, Ct.Ubicacion AS ubicacion, Transformadores.Potencia AS potencia, Transformadores.Tension_1 AS v1, Transformadores.Tension_2 AS v2, Tipo_Trafo.Tipo AS tipo_trafo, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_chapa AS nro_chapa, Transformadores.Obs AS Observaciones, Transformadores.Anio_fabricacion AS año, Ct.Mat_plataf AS plataforma, Ct.Tipo_ct AS tipo_ct, Nodos.Nivel AS nivel, Nodos.Tension AS tensión_nodo, Nodos.Zona AS zona, Nodos.Alimentador AS alimentador_mt, Nodos.XCoord AS x, Nodos.YCoord AS y, Transformadores.Kit AS kit, Transformadores.Cromatografia AS cromatografia, Transformadores.Anomalia AS anomalia,  Transformadores.Fecha_norm AS fecha_norm, Transformadores.Obs_pcb AS observaciones_pcb, COUNT(Usuarios.id_usuario) AS cant_usuarios FROM Transformadores INNER JOIN Nodos INNER JOIN Ct ON Nodos.Nombre = Ct.Id_ct ON Transformadores.Id_ct = Ct.Id_ct INNER JOIN Tipo_Trafo ON Transformadores.Tipo = Tipo_Trafo.Numero LEFT OUTER JOIN Suministros_Trafos LEFT OUTER JOIN Usuarios RIGHT OUTER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro ON Suministros_Trafos.Geoname_s = Suministros.id_nodo ON Nodos.Geoname = Suministros_Trafos.Geoname_t WHERE Usuarios.ES = 1 GROUP BY Transformadores.Id_trafo, Nodos.Geoname, Nodos.Nombre, Ct.Ubicacion, Transformadores.Potencia, Transformadores.Tension_1, Transformadores.Tension_2, Tipo_Trafo.Tipo, Transformadores.Conexionado, Transformadores.Marca, Transformadores.N_chapa, Transformadores.Obs, Transformadores.Anio_fabricacion, Ct.Mat_plataf, Ct.Tipo_ct, Nodos.Nivel, Nodos.Tension, Nodos.Zona, Nodos.Alimentador, Nodos.XCoord, Nodos.YCoord, Transformadores.Kit, Transformadores.Cromatografia, Transformadores.Anomalia, Transformadores.Fecha_norm, Transformadores.Obs_pcb"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de Transformadores en la Red")
        self.dialogo.show()

    def importar_usuarios_oceba(self):
        import re
        a=0
        n=0
        fecha_baja=''
        cursor = self.conn.cursor()
        cursor.execute("SELECT Codigo FROM Empresa")
        #convierto el cursor en array
        empresa = tuple(cursor)
        cursor.close()
        codigo_empresa = empresa[0][0]
        dialog = QFileDialog()
        oFileName = dialog.getOpenFileName(None, "Archivo de Usuarios", "", "TXT files (*.txt)")
        fileName=oFileName[0]
        if fileName:
            f = open(fileName,'r')
            txt_usuarios_oceba = f.readlines()
            f.close()
            ilinea=0
            reply = QMessageBox.question(None, 'EnerGis', "El archivo tiene " + str(len(txt_usuarios_oceba)) + " lineas. Desea importar ?", QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            #----------------------------------------------------------------------------
            progress = QProgressDialog("Procesando...", "Cancelar", 0, 100)
            progress.setWindowTitle("Progreso")
            progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
            progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
            progress.setValue(0)  # Inicia el progreso en 0
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            for linea in range (1, len(txt_usuarios_oceba)):
                #----------------------------------------------------------------------------
                progress.setValue(int(40*linea/len(txt_usuarios_oceba)))
                if progress.wasCanceled():
                    return
                QApplication.processEvents()
                #----------------------------------------------------------------------------
                registro_usuario = txt_usuarios_oceba[linea].split(';')
                ilinea=ilinea+1
                if registro_usuario[0].strip()!=codigo_empresa:
                    QMessageBox.warning(None, 'EnerGis 5', "El archivo no es válido, corresponde a otra empresa:" + registro_usuario[0].strip())
                    return
                if len(registro_usuario)<28:
                    QMessageBox.warning(None, 'EnerGis 5', "El archivo no es válido, contiene " + str(len(registro_usuario)) + " campos en línea " + str(ilinea))
                    return
            reply = QMessageBox.question(None, 'EnerGis', 'Desea borrar los datos en la base antes de importar ?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                cursor = self.conn.cursor()
                try:
                    cursor.execute("DELETE FROM VW_CCDATOSCOMERCIALES")
                    self.conn.commit()
                except:
                    self.conn.rollback()
            #----------------------------------------------------------------------------
            progress.setValue(40)
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            for linea in range (1, len(txt_usuarios_oceba)):
                #----------------------------------------------------------------------------
                progress.setValue(40 + int(50*linea/len(txt_usuarios_oceba)))
                if progress.wasCanceled():
                    return
                QApplication.processEvents()
                #----------------------------------------------------------------------------
                registro_usuario = txt_usuarios_oceba[linea].split(';')
                str_campos = "Id_Usuario,Nro_Medidor,Apellido,Nombre,DNI,CUIT,Direccion_Postal,Calle,Numero,Piso,Dto,Entre, Localidad,Partido,Codigo_Postal,Telefono,E_Mail,Tarifa,Tarifa_Especial,Ruta,Tension_Suministro,Potencia_Declarada,Nomenclatura_Catastral,Fecha_Alta"
                str_valores = ""
                for i in range (2, 28):
                    str_valor = registro_usuario[i].strip()
                    str_valor = str_valor.replace("'", "")
                    if i==8 or i==9:
                        str_valor = re.sub(r"\s+", " ", str_valor)
                    if i==17 or i==23:
                        str_valor = str_valor.lstrip('0')
                    if i==28:
                        if str_valor!="":
                            str_campos = str_campos + ",Fecha_Baja"
                    if i>26: #fechas
                        if i==28: #fecha baja
                            if str_valor=="":
                                pass
                            else:
                                str_valor = datetime.strptime(str_valor, "%d/%m/%Y").strftime("%Y%m%d")
                                fecha_baja = str_valor
                                str_valores = str_valores + "'" + str_valor + "',"
                        elif i==27: #fecha alta
                            if str_valor=="":
                                fecha_alta = "1980-01-01"
                                str_valores = str_valores + "'1980-01-01',"
                            else:
                                str_valor = datetime.strptime(str_valor, "%d/%m/%Y").strftime("%Y%m%d")
                                fecha_alta = str_valor
                                str_valores = str_valores + "'" + str_valor + "',"
                    else:
                        if i!=25 and i!=26: #salteo lat y long
                            str_valores = str_valores + "'" + str_valor + "',"
                #saco la última coma
                str_valores = str_valores[:-1]
                cursor = self.conn.cursor()
                cursor.execute("SELECT * FROM VW_CCDATOSCOMERCIALES WHERE id_usuario='" + str(registro_usuario[2]) + "'")
                #convierto el cursor en array
                usuario = tuple(cursor)
                cursor.close()
                if len(usuario)==0:
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute("INSERT INTO VW_CCDATOSCOMERCIALES (" + str_campos + ") VALUES (" + str_valores + ")")
                        self.conn.commit()
                        n = n + 1
                    except:
                        QMessageBox.warning(None, 'EnerGis 5', "Fallo al insertar en fila " + str(n+1) + "- INSERT INTO VW_CCDATOSCOMERCIALES (" + str_campos + ") VALUES (" + str_valores + ")")
                        self.conn.rollback()
                        return
                else:
                    str_sql = "UPDATE VW_CCDATOSCOMERCIALES SET "
                    str_sql = str_sql + "Nro_Medidor='" + registro_usuario[3].strip() + "',"
                    str_sql = str_sql + "Apellido='" + registro_usuario[4].strip() + "',"
                    str_sql = str_sql + "Nombre='" + registro_usuario[5].strip() + "',"
                    str_sql = str_sql + "DNI='" + registro_usuario[6].strip() + "',"
                    str_sql = str_sql + "CUIT='" + registro_usuario[7].strip() + "',"
                    str_sql = str_sql + "Direccion_Postal='" + re.sub(r"\s+", " ", registro_usuario[8].strip()) + "',"
                    str_sql = str_sql + "Calle='" + re.sub(r"\s+", " ", registro_usuario[9].strip()) + "',"
                    str_sql = str_sql + "Numero='" + registro_usuario[10].strip() + "',"
                    str_sql = str_sql + "Piso='" + registro_usuario[11].strip() + "',"
                    str_sql = str_sql + "Dto='" + registro_usuario[12].strip() + "',"
                    str_sql = str_sql + "Entre='" + registro_usuario[13].strip() + "',"
                    str_sql = str_sql + "Localidad='" + registro_usuario[14].strip() + "',"
                    str_sql = str_sql + "Partido='" + registro_usuario[15].strip() + "',"
                    str_sql = str_sql + "Codigo_Postal='" + registro_usuario[16].strip() + "',"
                    str_sql = str_sql + "Telefono='" + registro_usuario[17].strip().lstrip('0') + "',"
                    str_sql = str_sql + "E_Mail='" + registro_usuario[18].strip() + "',"
                    str_sql = str_sql + "Tarifa='" + registro_usuario[19].strip() + "',"
                    str_sql = str_sql + "Tarifa_Especial='" + registro_usuario[20].strip() + "',"
                    str_sql = str_sql + "Ruta='" + registro_usuario[21].strip() + "',"
                    str_sql = str_sql + "Tension_Suministro='" + registro_usuario[22].strip() + "',"
                    str_sql = str_sql + "Potencia_Declarada='" + registro_usuario[23].strip().lstrip('0') + "',"
                    str_sql = str_sql + "Nomenclatura_Catastral='" + registro_usuario[24].strip() + "',"
                    str_sql = str_sql + "Fecha_Alta='" + fecha_alta + "',"
                    if fecha_baja=='':
                        str_sql = str_sql + "Fecha_Baja=NULL,"
                    else:
                        str_sql = str_sql + "Fecha_Baja='" + fecha_baja + "',"
                    #saco la última coma
                    str_sql = str_sql[:-1]
                    str_sql = str_sql + " WHERE id_usuario='" + str(registro_usuario[2].strip()) + "'"
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute(str_sql)
                        self.conn.commit()
                        a = a + 1
                    except:
                        QMessageBox.warning(None, 'EnerGis 5', "Fallo al actualizar en fila " + str(a+1) + "- " + str_sql)
                        self.conn.rollback()
                        return
            QMessageBox.warning(None, 'EnerGis 5', "Fin. " + str(n) + " registros nuevos, y " + str(a) + " registros actualizados")
            #----------------------------------------------------------------------------
            progress.setValue(90)
            QApplication.processEvents()
            #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE A SET d=o FROM (SELECT VW_CCDATOSCOMERCIALES.[Apellido] + ' ' + VW_CCDATOSCOMERCIALES.[nombre] AS o, Usuarios.nombre AS d FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE VW_CCDATOSCOMERCIALES.[Apellido] + ' ' + VW_CCDATOSCOMERCIALES.[nombre] <> Usuarios.nombre AND VW_CCDATOSCOMERCIALES.[Apellido] <> VW_CCDATOSCOMERCIALES.[nombre]) AS A ")
            cursor.execute("UPDATE A SET d=o FROM (SELECT VW_CCDATOSCOMERCIALES.[Tarifa] AS o, Usuarios.Tarifa AS d FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE VW_CCDATOSCOMERCIALES.[Tarifa] <> Usuarios.Tarifa) AS A")
            cursor.execute("UPDATE A SET d=o FROM (SELECT VW_CCDATOSCOMERCIALES.[Calle] AS o, Usuarios.Calle AS d FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE VW_CCDATOSCOMERCIALES.[Calle] <> Usuarios.Calle) AS A")
            cursor.execute("UPDATE A SET d=o FROM (SELECT VW_CCDATOSCOMERCIALES.[Numero] AS o, Usuarios.Altura AS d FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE VW_CCDATOSCOMERCIALES.[Numero] <> Usuarios.Altura) AS A")
            cursor.execute("UPDATE Usuarios SET Electrodependiente='N' WHERE Electrodependiente<>'N'")
            cursor.execute("UPDATE Usuarios SET Electrodependiente='S' WHERE Electrodependiente<>'S' AND id_usuario IN (SELECT id_usuario FROM VW_CCDATOSCOMERCIALES WHERE tarifa_especial ='TE')")
            cursor.execute("UPDATE A SET ES = 1 FROM (SELECT Usuarios.[ES] FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE (((VW_CCDATOSCOMERCIALES.Fecha_Baja) IS NULL) AND ((Usuarios.[ES])=0))) AS A")
            cursor.execute("UPDATE A SET ES = 0 FROM (SELECT Usuarios.[ES] FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE (((Usuarios.[ES])=1) AND ((VW_CCDATOSCOMERCIALES.Fecha_Baja) IS NOT NULL))) AS A")
            cursor.execute("INSERT INTO Usuarios SELECT VW_CCDATOSCOMERCIALES.Id_Usuario AS Id_Usuario,0 AS Tipo,VW_CCDATOSCOMERCIALES.Apellido AS Nombre,VW_CCDATOSCOMERCIALES.Calle AS Calle,VW_CCDATOSCOMERCIALES.Numero AS Altura,VW_CCDATOSCOMERCIALES.Piso + ' ' + VW_CCDATOSCOMERCIALES.Dto AS Altura_Ex,VW_CCDATOSCOMERCIALES.Codigo_Postal AS Zona,VW_CCDATOSCOMERCIALES.Id_Usuario AS Id_Suministro,VW_CCDATOSCOMERCIALES.Tarifa AS Tarifa,123 AS Fase,1 AS ES,VW_CCDATOSCOMERCIALES.Localidad AS SubZona,CASE WHEN [Tarifa_Especial]='TE' THEN 'S' ELSE 'N' END AS Electrodependiente,'N' AS Fae,'' AS Prosumidor FROM VW_CCDATOSCOMERCIALES LEFT JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE VW_CCDATOSCOMERCIALES.Fecha_Baja IS NULL AND Usuarios.id_usuario IS NULL")
            cursor.execute("UPDATE Usuarios SET ES = 1 WHERE Es=0 AND id_usuario IN (SELECT id_usuario FROM VW_CCDATOSCOMERCIALES WHERE Fecha_Baja IS NULL)")
            cursor.execute("UPDATE Usuarios SET ES = 0 WHERE Es=1 AND id_usuario IN (SELECT id_usuario FROM VW_CCDATOSCOMERCIALES WHERE not Fecha_Baja IS NULL)")
            cursor.execute("UPDATE Usuarios SET ES = 0 WHERE Es=1 AND id_usuario NOT IN (SELECT id_usuario from VW_CCDATOSCOMERCIALES)")
            cursor.execute("INSERT INTO medidores SELECT '0' AS nro_medidor, id_usuario, '' AS marca, '' AS modelo, 1980 AS anio, '' AS relacion, '' AS fases, '' AS tipo FROM Usuarios WHERE id_usuario NOT IN (SELECT id_usuario FROM medidores)")
            cursor.execute("UPDATE A SET d=o FROM (SELECT VW_CCDATOSCOMERCIALES.nro_medidor AS o, Medidores.Nro_Medidor AS d FROM VW_CCDATOSCOMERCIALES INNER JOIN Medidores ON VW_CCDATOSCOMERCIALES.Id_Usuario = medidores.id_usuario WHERE VW_CCDATOSCOMERCIALES.Nro_Medidor <> medidores.Nro_Medidor AND VW_CCDATOSCOMERCIALES.nro_medidor<>'') AS A")
            self.conn.commit()
        except:
            self.conn.rollback()
        #----------------------------------------------------------------------------
        progress.setValue(100)
        QApplication.processEvents()
        #----------------------------------------------------------------------------

    def importar_energias_dpe(self):
        a=0
        n=0
        dialog = QFileDialog()
        oFileName = dialog.getOpenFileName(None, "Archivo de Consumos", "", "TXT files (*.txt)")
        fileName=oFileName[0]
        if fileName:
            #----------------------------------------------------------------------------
            progress = QProgressDialog("Procesando...", "Cancelar", 0, 100)
            progress.setWindowTitle("Progreso")
            progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
            progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
            progress.setValue(0)  # Inicia el progreso en 0
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            f = open(fileName,'r')
            txt_consumos_dpe = f.readlines()
            f.close()
            ilinea=0
            reply = QMessageBox.question(None, 'EnerGis', "El archivo tiene " + str(len(txt_consumos_dpe)) + " lineas. Desea importar ?", QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            for linea in range (0, len(txt_consumos_dpe)):
                registro_energia = txt_consumos_dpe[linea].split(',')
                ilinea=ilinea+1
                if len(registro_energia)!=14:
                    QMessageBox.warning(None, 'EnerGis 5', "El archivo no es válido, contiene " + str(len(registro_energia)) + " campos en línea " + str(ilinea))
                    return
            for linea in range (0, len(txt_consumos_dpe)):
                #----------------------------------------------------------------------------
                # Actualiza el progreso
                progress.setValue(int(100*linea/len(txt_consumos_dpe)))
                if progress.wasCanceled():
                    break
                # Permitir que la GUI se actualice (similar a DoEvents)
                QApplication.processEvents()
                #----------------------------------------------------------------------------
                registro_energia = txt_consumos_dpe[linea].split(',')
                str_campos = "Id_Usuario,Periodo,Tipo_Periodo,Tarifa,Contrato_Especial,E,Ep,EFp,Er,Ev,Pp,Pfp,Pcp,Pcfp"
                str_valores = ""
                for i in range (0, len(registro_energia)):
                    str_valor = registro_energia[i].strip()
                    str_valor = str_valor.replace("'", "")
                    str_valores = str_valores + "'" + str_valor + "',"
                #saco la última coma
                str_valores = str_valores[:-1]
                cursor = self.conn.cursor()
                try:
                    cursor.execute("SELECT * FROM Energias_DPE WHERE id_usuario='" + str(registro_energia[0]) + "' AND periodo='" + str(registro_energia[1]) + "'")
                    #convierto el cursor en array
                    usuario = tuple(cursor)
                    cursor.close()
                except:
                    QMessageBox.critical(None, 'EnerGis 5', 'Error en ' + "SELECT * FROM Energias_DPE WHERE id_usuario='" + str(registro_energia[0]) + "' AND periodo='" + str(registro_energia[1]) + "'")
                    return
                try:
                    if len(usuario)==1:
                        cursor = self.conn.cursor()
                        cursor.execute("DELETE FROM Energias_DPE WHERE id_usuario='" + str(registro_energia[0]) + "' AND periodo='" + str(registro_energia[1]) + "'")
                        #cursor.execute("DELETE FROM Energia_Facturada WHERE id_usuario='" + str(registro_energia[0]) + "' AND periodo='" + str(registro_energia[1])[:4] + "/" + str(registro_energia[1])[-2:] + "'")
                        a = a + 1
                    cursor = self.conn.cursor()
                    cursor.execute("INSERT INTO Energias_DPE (" + str_campos + ") VALUES (" + str_valores + ")")
                    #cursor.execute("INSERT INTO Energia_Facturada SELECT LEFT(Periodo,4)+'/'+RIGHT(Periodo,2) AS Periodo,CAST(LEFT(Periodo,4)+RIGHT(Periodo,2)+'01' AS date) AS Desde,CASE WHEN Tipo_Periodo='M' THEN DATEADD(d,-1,DATEADD(M,1,CAST(LEFT(Periodo,4)+RIGHT(Periodo,2)+'01' AS date))) ELSE DATEADD(d,-1,DATEADD(M,2,CAST(LEFT(Periodo,4)+RIGHT(Periodo,2)+'01' AS date))) END AS Hasta,Id_Usuario,E+Ep+Efp+Er+Ev AS EtF FROM Energias_DPE WHERE id_usuario='" + str(registro_energia[0]) + "' AND periodo='" + str(registro_energia[1]) + "'")
                    self.conn.commit()
                    n = n + 1
                except:
                    QMessageBox.warning(None, 'EnerGis 5', "Fallo al insertar en fila " + str(n+1) + "- INSERT INTO Energias_DPE (" + str_campos + ") VALUES (" + str_valores + ")")
                    self.conn.rollback()
                    return
            QMessageBox.warning(None, 'EnerGis 5', "Fin. " + str(n) + " registros nuevos, y " + str(a) + " registros actualizados")

    def listado_movimiento_transformadores(self):
        str_sql = "SELECT Movimiento_Transformadores.id_mov AS id_movimiento, Movimiento_Transformadores.Fecha AS fecha_movimiento, Ubicaciones.Descripcion AS ubicacion_desde, Ubicaciones_1.Descripcion AS ubicacion_hasta, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo AS id_trafo, Transformadores.Potencia AS potencia, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_Chapa AS nro_chapa, Transformadores.Anio_fabricacion AS año FROM Ct, ((Movimiento_Transformadores INNER JOIN Transformadores ON Movimiento_Transformadores.id_trafo = Transformadores.Id_Trafo) INNER JOIN Ubicaciones ON Movimiento_Transformadores.mov_desde = Ubicaciones.Id_Ubicacion) INNER JOIN Ubicaciones AS Ubicaciones_1 ON Movimiento_Transformadores.mov_hasta = Ubicaciones_1.Id_Ubicacion GROUP BY Movimiento_Transformadores.id_mov, Movimiento_Transformadores.Fecha, Ubicaciones.Descripcion, Ubicaciones_1.Descripcion, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo, Transformadores.Potencia, Transformadores.Conexionado, Transformadores.Marca, Transformadores.N_Chapa, Transformadores.Anio_fabricacion ORDER BY Movimiento_Transformadctores.Fecha"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Movimiento de Transformadores")
        self.dialogo.show()

    def listado_movimientos_trafo(self):
        id_trafo=''
        str_sql = "SELECT Movimiento_Transformadores.id_mov AS id_movimiento, Movimiento_Transformadores.Fecha AS fecha_movimiento, Ubicaciones.Descripcion AS ubicacion_desde, Ubicaciones_1.Descripcion AS ubicacion_hasta, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo AS id_trafo, Transformadores.Potencia AS potencia, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_Chapa AS nro_chapa, Transformadores.Anio_fabricacion AS año FROM Ct, ((Movimiento_Transformadores INNER JOIN Transformadores ON Movimiento_Transformadores.id_trafo = Transformadores.Id_Trafo) INNER JOIN Ubicaciones ON Movimiento_Transformadores.mov_desde = Ubicaciones.Id_Ubicacion) INNER JOIN Ubicaciones AS Ubicaciones_1 ON Movimiento_Transformadores.mov_hasta = Ubicaciones_1.Id_Ubicacion GROUP BY Movimiento_Transformadores.id_mov, Movimiento_Transformadores.Fecha, Ubicaciones.Descripcion, Ubicaciones_1.Descripcion, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo, Transformadores.Potencia, Transformadores.Conexionado, Transformadores.Marca, Transformadores.N_Chapa, Transformadores.Anio_fabricacion HAVING Transformadores.id_trafo=" + id_trafo + " ORDER BY Movimiento_Transformadores.Fecha"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Movimiento de Transformadores")
        self.dialogo.show()

    def listado_movimientos_ct(self):
        id_ct=''
        str_sql = "SELECT Movimiento_Transformadores.id_mov AS id_movimiento, Movimiento_Transformadores.Fecha AS fecha_movimiento, Ubicaciones.Descripcion AS ubicacion_desde, Ubicaciones_1.Descripcion AS ubicacion_hasta, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo AS id_trafo, Transformadores.Potencia AS potencia, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_Chapa AS nro_chapa, Transformadores.Anio_fabricacion AS año FROM Ct, ((Movimiento_Transformadores INNER JOIN Transformadores ON Movimiento_Transformadores.id_trafo = Transformadores.Id_Trafo) INNER JOIN Ubicaciones ON Movimiento_Transformadores.mov_desde = Ubicaciones.Id_Ubicacion) INNER JOIN Ubicaciones AS Ubicaciones_1 ON Movimiento_Transformadores.mov_hasta = Ubicaciones_1.Id_Ubicacion GROUP BY Movimiento_Transformadores.id_mov, Movimiento_Transformadores.Fecha, Ubicaciones.Descripcion, Ubicaciones_1.Descripcion, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo, Transformadores.Potencia, Transformadores.Conexionado, Transformadores.Marca, Transformadores.N_Chapa, Transformadores.Anio_fabricacion HAVING Movimiento_Transformadores.observaciones LIKE '%CT " + id_ct + "%' OR Movimiento_Transformadores.observaciones LIKE '%SET " + id_ct + "%' ORDER BY Movimiento_Transformadores.Fecha"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Movimientos")
        self.dialogo.show()

    def listado_usuarios(self):
        str_sql = "SELECT Usuarios.id_usuario, Medidores.nro_medidor, Usuarios.nombre, Usuarios.calle, Usuarios.altura, Usuarios.altura_ex, Usuarios.zona, Usuarios.subzona, Usuarios.id_suministro, Usuarios.tarifa, Usuarios.fase, Usuarios.ES AS En_Servicio, Usuarios.electrodependiente, Ct.Id_ct AS codigoct, Nodos_1.XCoord AS xct, Nodos_1.YCoord AS yct, Nodos_1.Nivel AS nivelct, Nodos_1.Tension AS tensionct, Nodos_1.Zona AS zonact, Nodos_1.Alimentador AS alimct, Ct.Ubicacion AS ubicct, Ct.Mat_plataf AS matct, Ct.Tipo_ct AS tipoct, Ct.Obs AS obsct FROM Medidores RIGHT OUTER JOIN Suministros LEFT OUTER JOIN Ct RIGHT OUTER JOIN Nodos AS Nodos_1 ON Ct.Id_ct = Nodos_1.Nombre RIGHT OUTER JOIN Suministros_Trafos ON Nodos_1.Geoname = Suministros_Trafos.Geoname_t ON Suministros.id_nodo = Suministros_Trafos.Geoname_s RIGHT OUTER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro ON Medidores.id_usuario = Usuarios.id_usuario"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de Usuarios")
        self.dialogo.show()

    def listado_usuarios_red(self):
        str_sql = "SELECT Usuarios.id_usuario, Medidores.nro_medidor, Usuarios.nombre, Usuarios.calle, Usuarios.altura, Usuarios.altura_ex, Usuarios.zona, Usuarios.Subzona, Usuarios.id_suministro, Usuarios.tarifa, Usuarios.fase, Usuarios.ES AS En_Servicio, Usuarios.electrodependiente, Ct.Id_ct AS codigoct, Nodos_1.XCoord AS xct, Nodos_1.YCoord AS yct, Nodos_1.Nivel AS nivelct, Nodos_1.Tension AS tensionct, Nodos_1.Zona AS zonact, Nodos_1.Alimentador AS alimct, Ct.Ubicacion AS ubicct, Ct.Mat_plataf AS matct, Ct.Tipo_ct AS tipoct, Ct.Obs AS obsct FROM (Ct INNER JOIN Nodos AS Nodos_1 ON Ct.Id_ct = Nodos_1.Nombre) INNER JOIN ((Medidores RIGHT JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Medidores.id_usuario = Usuarios.id_usuario) INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s) ON Nodos_1.Geoname = Suministros_Trafos.Geoname_t"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de Usuarios en la Red")
        self.dialogo.show()

    def h_login(self):
        import winreg
        nombre_usuario=''
        try:
            # Definir la ruta de la clave del registro que quieres leer
            ruta_clave = r"SOFTWARE\EnerGis"
            # Abrir la clave del registro en modo de solo lectura
            clave_registro = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta_clave, 0, winreg.KEY_READ)
            # Leer el valor de una entrada en la clave del registro
            valor, tipo = winreg.QueryValueEx(clave_registro, "Usuario") #el tipo no lo usamos
            if valor!=None:
                nombre_usuario=valor
            # Cerrar la clave del registro
            winreg.CloseKey(clave_registro)
        except:
            pass

        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion.png'))
        seleccion_px.setMask(seleccion_px.mask())
        seleccion_cursor = QtGui.QCursor(seleccion_px)
        self.iface.mapCanvas().setCursor(seleccion_cursor)

        from .frm_login import frmLogin
        dialogo = frmLogin(self.version, self.str_conexion_seguridad, nombre_usuario)
        dialogo.exec()
        nombre_usuario = dialogo.nombre_usuario
        self.id_usuario_sistema = dialogo.id_usuario_sistema
        self.tipo_usuario = dialogo.tipo_usuario

        self.iface.mainWindow().setWindowTitle('EnerGis (Versión: ' + self.version + ') - ' + self.nombre_modelo + ' - Usuario: ' + nombre_usuario)

        dialogo.close()
        if str(self.tipo_usuario)=='4':
            #deshabilito los botones
            self.toolbar_e.setEnabled(False)
            self.toolbar_p.setEnabled(False)
            for action in self.actions:
                if str(action.text())=='Verificar Red':
                    action.setEnabled(False)
                if str(action.text())=='Nodo':
                    action.setEnabled(False)
                if str(action.text())=='Linea':
                    action.setEnabled(False)
                if str(action.text())=='Poste':
                    action.setEnabled(False)
                if str(action.text())=='Girar':
                    action.setEnabled(False)
                if str(action.text())=='Mover':
                    action.setEnabled(False)
                if str(action.text())=='Rotar':
                    action.setEnabled(False)
                if str(action.text())=='Anotacion':
                    action.setEnabled(False)
                if str(action.text())=='Conectar':
                    action.setEnabled(False)
                if str(action.text())=='Area':
                    action.setEnabled(False)
                if str(action.text())=='Parcela':
                    action.setEnabled(False)
                if str(action.text())=='Borrar':
                    action.setEnabled(False)
                if str(action.text())=='Contingencias':
                    action.setEnabled(False)
                if str(action.text())=='Usuarios Nuevos':
                    action.setEnabled(False)
            self.tool_button.setEnabled(False)
            self.m_administrador.setEnabled(False)
            self.m_modelo.setEnabled(False)
            self.m_archivos.setEnabled(False)

    def actualizar_db(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Configuracion")
        #convierto el cursor en array
        configuracion = tuple(cursor)
        cursor.close()
        for c in configuracion:
            if c[0]=='Version':
                version_instalada = c[1]
        versiones_nuevas = self.version.split('.')
        version_nueva1 = int(versiones_nuevas[0])
        version_nueva2 = int(versiones_nuevas[1])
        version_nueva3 = int(versiones_nuevas[2])
        versiones_instaladas = version_instalada.split('.')
        version_instalada1 = int(versiones_instaladas[0])
        version_instalada2 = int(versiones_instaladas[1])
        version_instalada3 = int(versiones_instaladas[2])
        if (version_nueva1<version_instalada1) or (version_nueva1==version_instalada1 and version_nueva2<version_instalada2) or (version_nueva1==version_instalada1 and version_nueva2==version_instalada2 and version_nueva3<version_instalada3) or (version_nueva1==version_instalada1 and version_nueva2==version_instalada2 and version_nueva3==version_instalada3):
            return
        conn = self.conn
        cursor = conn.cursor()
        #Esto se ejecuta siempre
        try:
            cursor.execute("UPDATE lineas SET Longitud=obj.STLength() WHERE Longitud < obj.STLength()")
            cursor.execute("UPDATE Transformadores SET usado=1 WHERE usado IS NULL AND id_ct=''")
            cursor.execute("UPDATE Transformadores SET usado=3 WHERE id_ct<>''")            
            cursor.execute("UPDATE Usuarios SET prosumidor='' WHERE prosumidor<>'' AND LEN(prosumidor)<20")
            cursor.execute("UPDATE Nodos SET Val1='Seccionador' WHERE elmt IN (2,3) AND (Val1='' OR Val1 IS NULL)")
            conn.commit()
        except:
            conn.rollback()
        #-------------------------------------------------------------------------------------------------
        #------------------------------------------ actualizar -------------------------------------------
        #-------------------------------------------------------------------------------------------------

        if version_instalada1<=5 and version_instalada2 <=0 and version_instalada3<=16:
            try:
                cursor.execute("CREATE TABLE [Fotos]([Id] [int] IDENTITY(1,1) NOT NULL,[Geoname] [int] NULL,[Nombre] [varchar](50) NULL,[Imagen] [image] NULL, CONSTRAINT [PK_Fotos] PRIMARY KEY CLUSTERED ([Id] ASC) ON [PRIMARY]) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TABLE [Almacenes]([id_almacen] [smallint] NULL,[Nombre] [varchar](50) NULL,[Direccion] [varchar](100) NULL) ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TABLE [Proyectos]([id] [int] IDENTITY(1,1) NOT NULL,[nombre] [varchar](15) NULL,[descripcion] [varchar](100) NULL,[fecha] [date] NULL) ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE FUNCTION Split (@cadena VARCHAR(255), @separador VARCHAR(1)) RETURNS @returnList TABLE (Name nvarchar (500)) AS BEGIN DECLARE @name NVARCHAR(255) DECLARE @pos INT WHILE CHARINDEX(@separador, @cadena) > 0 BEGIN SELECT @pos  = CHARINDEX(@separador, @cadena) SELECT @name = SUBSTRING(@cadena, 1, @pos-1) INSERT INTO @returnList SELECT @name SELECT @cadena = SUBSTRING(@cadena, @pos+1, LEN(@cadena)-@pos) END INSERT INTO @returnList SELECT @cadena RETURN END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE FUNCTION Split (@cadena VARCHAR(255), @separador VARCHAR(1)) RETURNS @returnList TABLE (Name nvarchar (500)) AS BEGIN DECLARE @name NVARCHAR(255) DECLARE @pos INT WHILE CHARINDEX(@separador, @cadena) > 0 BEGIN SELECT @pos  = CHARINDEX(@separador, @cadena) SELECT @name = SUBSTRING(@cadena, 1, @pos-1) INSERT INTO @returnList SELECT @name SELECT @cadena = SUBSTRING(@cadena, @pos+1, LEN(@cadena)-@pos) END INSERT INTO @returnList SELECT @cadena RETURN END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE FUNCTION MAXIMO(@valor1 INT, @valor2 INT) RETURNS INT AS BEGIN DECLARE @resultado INT SET @resultado = @valor1 IF @valor2 > @resultado BEGIN SET @resultado = @valor2 END RETURN @resultado END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE PROCEDURE Compilar_Red AS BEGIN SET NOCOUNT ON DECLARE @t TABLE(Elemento VARCHAR(10), Problema VARCHAR(100), Geoname INT, Nombre VARCHAR(50)) INSERT INTO @t SELECT DISTINCT 'Lineas' AS Elemento, 'lineas con iguales nodo desde/hasta' AS Problema,Max(A.Geoname) AS Geoname,'Linea' AS Nombre FROM (SELECT Geoname,Desde,Hasta FROM Lineas WHERE Tension>0 UNION SELECT Geoname,Hasta,Desde FROM Lineas WHERE Tension>0) AS A GROUP BY A.Desde, A.Hasta HAVING Count(A.Geoname)>1 INSERT INTO @t SELECT 'Lineas' AS Elemento, 'lineas con longitud menor a cero' AS Problema,Geoname,'Linea' AS Nombre FROM Lineas WHERE Longitud<=0 AND Tension>0 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'seccionadores sin nombre' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND (Elmt = 2 OR Elmt = 3) AND ((Nombre) Is null OR Nombre = '') INSERT INTO @t SELECT 'Nodos' AS Elemento, 'seccionadores con nombre repetido' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND (Elmt = 2 OR Elmt = 3) GROUP BY Geoname, Nombre HAVING Count(Nodos.Geoname)>1 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'CTs con nombre repetido' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND Elmt = 4 GROUP BY Geoname, Nombre HAVING Count(Nodos.Geoname)>1 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'salidas de alimentador sin códi de alimentador' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND Elmt = 8 AND ((Val1) Is null OR Val1 = '') INSERT INTO @t SELECT 'Nodos' AS Elemento, 'fuentes con errores de tensión' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND Elmt = 1 AND Val1 IS NULL INSERT INTO @t SELECT 'Nodos' AS Elemento, 'fuentes con mas de una línea' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND Nodos.estado=1 AND cant_lineas>1 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'seccionadores con mas de dos líneas' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND (Nodos.estado=2 OR Nodos.estado=3) AND cant_lineas>2 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'CTs con mas de dos líneas' AS Problema, Nodos.Geoname, Nodos.Nombre as Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND Nodos.estado=4 AND cant_lineas>2 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'CTs con usuarios y sin máquina' AS Problema, Nodos.Geoname, Nodos.Nombre FROM (Nodos INNER JOIN ((Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s) ON Nodos.Geoname = Suministros_Trafos.Geoname_t) LEFT JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct WHERE Tension>0 AND Nodos.elmt = 4 AND Usuarios.ES = 1 AND Transformadores.Id_trafo IS NULL GROUP BY Nodos.Geoname, Nodos.Nombre HAVING Count(Usuarios.id_usuario)>0 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'transformadores con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Transformadores INNER JOIN Nodos ON Transformadores.Id_ct = Nodos.Nombre INNER JOIN mNodos ON Nodos.Geoname = mNodos.Geoname WHERE Nodos.Tension>0 AND ((mNodos.fases IN (1,2,3) AND Transformadores.Conexionado <> 'M') OR (mNodos.fases IN ('12','23','13') AND Transformadores.Conexionado NOT IN ('M','B'))) AND Nodos.Elmt=4 GROUP BY nodos.Geoname, nodos.Nombre INSERT INTO @t SELECT 'Nodos' AS Elemento, 'usuarios con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo  WHERE Tension>0 AND Usuarios.fase='123' GROUP BY nodos.Geoname, nodos.Nombre HAVING MIN(fase) IN ('1','2','3','12','23','13') INSERT INTO @t SELECT 'Nodos' AS Elemento, 'nodos con inconsistencias de tarifas' AS Problema,A.Geoname, A.Nombre FROM (SELECT Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE Tension>0 GROUP BY Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension) AS A GROUP BY A.Geoname, A.Nombre HAVING Count(A.Nivel_Tension)>1 INSERT INTO @t SELECT DISTINCT 'Nodos' AS Elemento, 'nodos con inconsistencias de tarifas' AS Problema,Nodos.Geoname, Usuarios.tarifa AS Nombre FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE (Tension>0 AND ((Nodos.Tension)>1000) AND ((Tarifas.Nivel_Tension)='BT')) OR (Tension>0 AND ((Nodos.Tension)<1000) AND ((Tarifas.Nivel_Tension)='MT')) INSERT INTO @t SELECT 'Nodos' AS Elemento, 'usuarios con tarifas erroneas' AS Problema, Nodos.Geoname, CAST(Usuarios.id_usuario AS varchar) + '->'+ Usuarios.Tarifa AS Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo WHERE (Tension>0 AND Usuarios.ES=1 AND Usuarios.tarifa IS NULL) OR (Tension>0 AND Usuarios.tarifa NOT IN (SELECT tarifa from tarifas)) INSERT INTO @t SELECT 'Nodos' AS Elemento, 'alimentadores sin Nombre' AS Problema, nodos.Geoname, nodos.Nombre FROM Nodos WHERE Tension>0 AND Elmt = 8 AND (Val1='' OR Val1 IS NULL) INSERT INTO @t SELECT 'Nodos' AS Elemento, 'cambios de tension sin trafos' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta WHERE (Nodos.Tension>0 AND Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Tension>0 AND Nodos.Elmt=5 AND Lineas.Tension>0) INSERT INTO @t SELECT 'Nodos' AS Elemento, 'nodos con inconsistenacias de tensión' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE Nodos.Tension>0 AND Nodos.Geoname<>0 AND ((Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Elmt=5 AND Lineas.Tension>0)) SELECT * from @t END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE PROCEDURE Crear_Red AS BEGIN SET NOCOUNT ON UPDATE Nodos SET Aux=0 WHERE Tension=0 UPDATE Lineas SET Aux=0 WHERE Tension=0 UPDATE A SET d=o FROM (SELECT ROW_NUMBER() OVER (ORDER BY Geoname) AS o, Aux AS d FROM Nodos WHERE Tension>0) A UPDATE A SET d=o FROM (SELECT ROW_NUMBER() OVER (ORDER BY Geoname) AS o, Aux AS d FROM Lineas WHERE Tension>0) A TRUNCATE TABLE mNodos TRUNCATE TABLE mLineas INSERT INTO mNodos SELECT 0 AS aux, 0 AS geoname, 0 AS estado, 0 AS navegado, 0 AS cant_lineas,0 AS linea1,0 AS linea2,0 AS linea3,0 AS linea4,0 AS linea5,0 AS linea6,0 AS linea7,0 AS linea8,0 AS linea9,0 AS linea10,0 AS linea11,0 AS linea12,0 AS linea13,0 AS linea14,0 AS linea15,0 AS linea16,0 AS linea17,0 AS linea18,0 AS linea19,0 AS linea20,0 AS linea21,0 AS linea22,0 AS linea23,0 AS linea24,0 AS linea25,0 AS linea26,0 AS linea27,0 AS linea28,0 AS linea29,0 AS linea30,0 AS linea31,0 AS linea32,0 AS fases, 1 AS tension, 0 AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, 0 AS aux8, 0 AS alim INSERT INTO mNodos SELECT aux, geoname, estado, 0 AS navegado, cant_lineas,ISNULL(linea1, 0) AS linea1,ISNULL(linea2, 0) AS linea2,ISNULL(linea3, 0) AS linea3,ISNULL(linea4, 0) AS linea4,ISNULL(linea5, 0) AS linea5,ISNULL(linea6, 0) AS linea6,ISNULL(linea7, 0) AS linea7,ISNULL(linea8, 0) AS linea8,ISNULL(linea9, 0) AS linea9,ISNULL(linea10, 0) AS linea10,ISNULL(linea11, 0) AS linea11,ISNULL(linea12, 0) AS linea12,ISNULL(linea13, 0) AS linea13,ISNULL(linea14, 0) AS linea14,ISNULL(linea15, 0) AS linea15,ISNULL(linea16, 0) AS linea16,ISNULL(linea17, 0) AS linea17,ISNULL(linea18, 0) AS linea18,ISNULL(linea19, 0) AS linea19,ISNULL(linea20, 0) AS linea20,ISNULL(linea21, 0) AS linea21,ISNULL(linea22, 0) AS linea22,ISNULL(linea23, 0) AS linea23,ISNULL(linea24, 0) AS linea24,ISNULL(linea25, 0) AS linea25,ISNULL(linea26, 0) AS linea26,ISNULL(linea27, 0) AS linea27,ISNULL(linea28, 0) AS linea28,ISNULL(linea29, 0) AS linea29,ISNULL(linea30, 0) AS linea30,ISNULL(linea31, 0) AS linea31,ISNULL(linea32, 0) AS linea32,0 AS fases, tension, elmt AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, 0 AS aux8,  alim FROM (SELECT C.aux, geoname, elmt, estado, tension, numero, linea, cant_lineas, alim FROM (SELECT aux, geoname, elmt, estado, B.tension, 'linea' + LTRIM(STR(ROW_NUMBER() OVER (PARTITION BY aux ORDER BY aux))) AS numero, linea, ISNULL(Alimentadores.Id, 0) AS alim FROM (SELECT Nodos.Aux, Nodos.Geoname, Nodos.Elmt, Nodos.Estado, Nodos.Tension, Lineas.Aux AS linea, nodos.Alimentador FROM Lineas INNER JOIN Nodos ON Lineas.Desde = Nodos.Geoname UNION SELECT Nodos_1.Aux, Nodos_1.Geoname, Nodos_1.Elmt, Nodos_1.Estado, Nodos_1.Tension, Lineas_1.Aux AS linea, nodos_1.Alimentador FROM Lineas AS Lineas_1 INNER JOIN Nodos AS Nodos_1 ON Lineas_1.Hasta = Nodos_1.Geoname) B LEFT JOIN Alimentadores ON B.Alimentador=Alimentadores.Id_Alim) C INNER JOIN (SELECT aux, COUNT(linea) AS cant_lineas FROM (SELECT aux, linea FROM (SELECT Nodos.Aux, Lineas.Aux AS linea FROM Lineas INNER JOIN Nodos ON Lineas.Desde = Nodos.Geoname UNION SELECT Nodos_1.Aux, Lineas_1.Aux AS linea FROM Lineas AS Lineas_1 INNER JOIN Nodos AS Nodos_1 ON Lineas_1.Hasta = Nodos_1.Geoname) D) E GROUP BY aux) A ON C.aux=A.aux WHERE Tension>0 ) Sal PIVOT (SUM(linea) FOR numero IN (linea1,linea2,linea3,linea4,linea5,linea6,linea7,linea8,linea9,linea10,linea11,linea12,linea13,linea14,linea15,linea16,linea17,linea18,linea19,linea20,linea21,linea22,linea23,linea24,linea25,linea26,linea27,linea28,linea29,linea30,linea31,linea32)) Pvt order by aux INSERT INTO mLineas SELECT  0 AS aux, 0 AS geoname, 0 AS desde, 0 AS hasta, 0 AS fuente, 1 AS tension, 0 AS fases, 0 AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, 0 AS alim INSERT INTO mLineas SELECT Lineas.aux, Lineas.geoname, Nodos.Aux AS desde, Nodos_1.Aux AS hasta, 0 AS fuente, Lineas.tension, Lineas.Fase AS fases, 0 AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, Alimentadores.Id AS alim FROM Lineas INNER JOIN Nodos ON Lineas.Desde = Nodos.Geoname INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname LEFT JOIN Alimentadores ON Lineas.Alimentador = Alimentadores.Id_Alim WHERE Lineas.Tension>0 ORDER BY Lineas.Aux UPDATE B SET d=o FROM  (SELECT mNodos.Fases AS d, A.Fases AS o FROM mNodos INNER JOIN (SELECT F.Geoname, MAX(F.Fases) AS Fases FROM (SELECT mNodos.Geoname, CONVERT(SMALLINT, mLineas.Fases) AS Fases FROM mLineas INNER JOIN mNodos ON mLineas.Desde = mNodos.Aux UNION SELECT mNodos.Geoname, CONVERT(SMALLINT, mLineas.Fases) AS Fases FROM mLineas INNER JOIN mNodos ON mLineas.Hasta = mNodos.Aux) F GROUP BY F.Geoname) A ON mNodos.Geoname=A.Geoname) B iNSERT INTO mNodos SELECT aux, geoname, estado, 0 AS navegado, 0 AS cant_lineas, 0 AS linea1,0 AS linea2,0 AS linea3,0 AS linea4, 0 AS linea5,0 AS linea6,0 AS linea7,0 AS linea8, 0 AS linea9,0 AS linea10,0 AS linea11,0 AS linea12, 0 AS linea13,0 AS linea14,0 AS linea15,0 AS linea16, 0 AS linea17,0 AS linea18,0 AS linea19,0 AS linea20, 0 AS linea21,0 AS linea22,0 AS linea23,0 AS linea24, 0 AS linea25,0 AS linea26,0 AS linea27,0 AS linea28, 0 AS linea29,0 AS linea30,0 AS linea31,0 AS linea32, 0 AS fases, tension, elmt AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, 0 AS aux8, 0 AS alim FROM Nodos WHERE Tension>0 AND Geoname NOT IN (SELECT Geoname FROM mNodos) END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE PROCEDURE Mover_Area @AREA INT, @VERTICE SMALLINT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @X1 DECIMAL(9,2) DECLARE @Y1 DECIMAL(9,2) DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_par VARCHAR(MAX) DECLARE @str_final VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @k SMALLINT DECLARE @SRID SMALLINT DECLARE @v SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=Areas.obj FROM Areas WHERE Areas.Geoname = @AREA SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @str_final='POLYGON ((' SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=0 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @X1=@X SET @Y1=@Y SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @V=0 WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) IF @VERTICE<>-1 BEGIN SET @V=@v+1 IF @VERTICE=@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END IF @VERTICE<>@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) END END IF @VERTICE=-1 BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=0 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) SET @str_final = @str_final + '))' SET @obj = geometry::STGeomFromText(@str_final, @SRID) SET @obj=@obj.MakeValid() IF @obj.STGeometryType()='Polygon' BEGIN UPDATE Areas SET obj=@obj WHERE Geoname = @AREA END END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE PROCEDURE Mover_Eje @EJE INT, @VERTICE SMALLINT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @X1 DECIMAL(9,2) DECLARE @Y1 DECIMAL(9,2) DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_par VARCHAR(MAX) DECLARE @str_final VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @SRID SMALLINT DECLARE @v SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=Ejes.obj FROM Ejes WHERE Ejes.Geoname = @EJE SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '')  SET @str_final='LINESTRING (' SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=1 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @X1=@X SET @Y1=@Y SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) set @str_par = @str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<>1 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) SET @str_final = @str_final + ')' UPDATE Ejes SET obj=geometry::STGeomFromText(@str_final, @SRID) WHERE Geoname = @EJE END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE PROCEDURE Mover_Linea @LINEA INT, @VERTICE SMALLINT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_par VARCHAR(MAX) DECLARE @str_final VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @SRID SMALLINT DECLARE @v SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=Lineas.obj FROM Lineas WHERE Lineas.Geoname = @LINEA SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SET @str_final='LINESTRING (' SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @V=0 WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) IF @VERTICE<>0 BEGIN  SET @V=@v+1 IF @VERTICE=@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END IF @VERTICE<>@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) END END IF @VERTICE=0 BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) SET @str_final = @str_final + ')' UPDATE Lineas SET obj=geometry::STGeomFromText(@str_final, @SRID) WHERE Geoname = @LINEA END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE PROCEDURE Mover_Nodo @NODO INT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(17,10) DECLARE @Y DECIMAL(17,10) DECLARE @LINEA INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=obj FROM Nodos WHERE Geoname = @NODO SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POINT (','') SET @str_obj = REPLACE(@str_obj, ')','') SELECT @i = CHARINDEX(' ', @str_obj) SET @X = LEFT(@str_obj, @i-1) + @DX SET @Y = RIGHT(@str_obj, LEN(@str_obj)-@i) + @DY SET @str_obj = 'POINT (' + CAST(@X AS VARCHAR) + ' ' +  CAST(@Y AS VARCHAR) + ')' UPDATE Nodos SET XCoord=@X, YCoord=@Y, obj=geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname=@NODO END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE PROCEDURE Mover_Parcela @PARCELA INT, @VERTICE SMALLINT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @X1 DECIMAL(9,2) DECLARE @Y1 DECIMAL(9,2) DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_par VARCHAR(MAX) DECLARE @str_final VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @k SMALLINT DECLARE @SRID SMALLINT DECLARE @v SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=Parcelas.obj FROM Parcelas WHERE Parcelas.Geoname = @PARCELA SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @str_final='POLYGON ((' SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=0 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @X1=@X SET @Y1=@Y SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @V=0 WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) IF @VERTICE<>-1 BEGIN SET @V=@v+1 IF @VERTICE=@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END IF @VERTICE<>@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) END END IF @VERTICE=-1 BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=0 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) SET @str_final = @str_final + '))' SET @obj = geometry::STGeomFromText(@str_final, @SRID) SET @obj=@obj.MakeValid() IF @obj.STGeometryType()='Polygon' BEGIN UPDATE Parcelas SET obj=@obj WHERE Geoname = @PARCELA END END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE PROCEDURE Mover_Poste @POSTE INT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(17,10) DECLARE @Y DECIMAL(17,10) DECLARE @LINEA INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=obj FROM Postes WHERE Geoname = @POSTE SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POINT (','') SET @str_obj = REPLACE(@str_obj, ')','') SELECT @i = CHARINDEX(' ', @str_obj) SET @X = LEFT(@str_obj, @i-1) + @DX SET @Y = RIGHT(@str_obj, LEN(@str_obj)-@i) + @DY SET @str_obj = 'POINT (' + CAST(@X AS VARCHAR) + ' ' +  CAST(@Y AS VARCHAR) + ')' UPDATE Postes SET XCoord=@X, YCoord=@Y, obj=geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname=@POSTE END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE PROCEDURE Normalizar_Linea @LINEA INT, @SRID SMALLINT AS BEGIN SET NOCOUNT ON DECLARE @X1 DECIMAL(17,10) DECLARE @Y1 DECIMAL(17,10) DECLARE @X2 DECIMAL(17,10) DECLARE @Y2 DECIMAL(17,10) DECLARE @NODO INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT SELECT @X1=Nodos.XCoord, @Y1=Nodos.YCoord, @X2=Nodos_1.XCoord, @Y2=Nodos_1.YCoord, @obj=Lineas.obj FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname WHERE Lineas.Geoname = @LINEA SET @str_obj = @obj.ToString() IF NOT @str_obj IS NULL BEGIN SELECT @i = CHARINDEX(',', @str_obj) SET @str_obj = 'LINESTRING (' + CAST(@X1 AS VARCHAR) + ' ' +  CAST(@Y1 AS VARCHAR) + ',' + RIGHT(@str_obj, LEN(@str_obj)-@i) SELECT @str_obj UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA SET @str_obj = @obj.ToString() SELECT @j = CHARINDEX(',', @str_obj) SET @i=@j WHILE @j<>0 BEGIN SET @i=@j SELECT @j = CHARINDEX(',', @str_obj, @i+1) END SET @str_obj = LEFT(@str_obj, @i-1) + ', ' + CAST(@X2 AS VARCHAR) + ' ' +  CAST(@Y2 AS VARCHAR) SELECT @str_obj UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA END IF @str_obj IS NULL BEGIN SET @str_obj = 'LINESTRING (' + CAST(@X1 AS VARCHAR) + ' ' +  CAST(@Y1 AS VARCHAR) + ',' + CAST(@X2 AS VARCHAR) + ' ' +  CAST(@Y2 AS VARCHAR) + ')' SELECT @str_obj UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA END END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE PROCEDURE Normalizar_Nodo @NODO INT, @SRID SMALLINT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(17,10) DECLARE @Y DECIMAL(17,10) DECLARE @LINEA INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT SELECT @obj=obj FROM Nodos WHERE Geoname = @NODO SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POINT (','') SET @str_obj = REPLACE(@str_obj, ')','') SELECT @i = CHARINDEX(' ', @str_obj) SET @X = LEFT(@str_obj, @i-1) SET @Y = RIGHT(@str_obj, LEN(@str_obj)-@i) UPDATE Nodos SET XCoord=@X, YCoord=@Y WHERE Geoname=@NODO DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM Lineas WHERE Desde=@NODO OPEN RS FETCH NEXT FROM RS INTO @LINEA, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SELECT @i = CHARINDEX(',', @str_obj) SET @str_obj = 'LINESTRING (' + CAST(@X AS VARCHAR) + ' ' +  CAST(@Y AS VARCHAR) + ',' + RIGHT(@str_obj, LEN(@str_obj)-@i) UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA FETCH NEXT FROM RS INTO @LINEA, @obj END CLOSE RS DEALLOCATE RS DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM Lineas WHERE Hasta=@NODO OPEN RS FETCH NEXT FROM RS INTO @LINEA, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SELECT @j = CHARINDEX(',', @str_obj) SET @i=@j WHILE @j<>0 BEGIN SET @i=@j SELECT @j = CHARINDEX(',', @str_obj, @i+1) END SET @str_obj = LEFT(@str_obj, @i-1) + ', ' + CAST(@X AS VARCHAR) + ' ' +  CAST(@Y AS VARCHAR) + ')' UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA FETCH NEXT FROM RS INTO @LINEA, @obj END CLOSE RS DEALLOCATE RS END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE PROCEDURE Normalizar_Poste @POSTE INT, @SRID SMALLINT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(17,10) DECLARE @Y DECIMAL(17,10) DECLARE @LINEA INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT SELECT @obj=obj FROM Postes WHERE Geoname = @POSTE SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POINT (','') SET @str_obj = REPLACE(@str_obj, ')','') SELECT @i = CHARINDEX(' ', @str_obj) SET @X = LEFT(@str_obj, @i-1) SET @Y = RIGHT(@str_obj, LEN(@str_obj)-@i) UPDATE Postes SET XCoord=@X, YCoord=@Y WHERE Geoname=@POSTE END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TRIGGER [Actualizo_Nodos] ON [Nodos] AFTER UPDATE AS BEGIN SET NOCOUNT ON DECLARE @geoname INT DECLARE @estado SMALLINT DECLARE @elmt SMALLINT DECLARE @tension INT DECLARE @x FLOAT DECLARE @y FLOAT DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' IF UPDATE(obj) BEGIN DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname WHILE (@@FETCH_STATUS = 0) BEGIN EXEC Normalizar_Nodo @geoname, @SRID INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'ACTUALIZO_NODO', NOMBRE + ';' + (CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[XCOORD])) +';'+ CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[YCOORD]))) FROM INSERTED WHERE Geoname = @geoname FETCH NEXT FROM RS INTO @geoname END CLOSE RS DEALLOCATE RS END IF UPDATE(XCOORD) OR UPDATE (YCOORD) BEGIN DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, xcoord, ycoord FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @x, @y WHILE (@@FETCH_STATUS = 0) BEGIN UPDATE Nodos SET obj=geometry::Point(@x, @y, @SRID) WHERE Geoname=@geoname EXEC Normalizar_Nodo @geoname, @SRID FETCH NEXT FROM RS INTO @geoname, @x, @y END CLOSE RS END IF UPDATE(elmt) OR UPDATE(estado) BEGIN DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, elmt, estado FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @elmt, @estado WHILE (@@FETCH_STATUS = 0) BEGIN IF @estado IS NULL BEGIN SET @estado = @elmt END UPDATE mNodos SET estado=@estado, aux2=@elmt WHERE geoname=@geoname FETCH NEXT FROM RS INTO @geoname, @elmt, @estado END CLOSE RS DEALLOCATE RS END IF UPDATE(tension) BEGIN DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, tension FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @tension WHILE (@@FETCH_STATUS = 0) BEGIN UPDATE mNodos SET tension=@tension WHERE geoname=@geoname FETCH NEXT FROM RS INTO @geoname, @tension END CLOSE RS DEALLOCATE RS END END")
                cursor.execute("ALTER TABLE Nodos ENABLE TRIGGER Actualizo_Nodos")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TRIGGER [Borro_Nodos] ON [Nodos] AFTER DELETE AS BEGIN SET NOCOUNT ON DECLARE @geoname INT DECLARE @nombre VARCHAR(50) DECLARE @elmt SMALLINT DECLARE @tension SMALLINT DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, nombre, elmt, tension FROM DELETED OPEN RS FETCH NEXT FROM RS INTO @geoname, @nombre, @elmt, @tension WHILE (@@FETCH_STATUS = 0) BEGIN IF @tension>0 BEGIN DELETE FROM Lineas WHERE Desde=@geoname OR Hasta=@geoname IF @elmt = 6 BEGIN DELETE FROM Suministros WHERE id_nodo = @geoname END IF @elmt = 4 BEGIN UPDATE Transformadores SET id_ct='', usado=1 WHERE id_ct = @nombre END UPDATE mNodos SET geoname=0,estado=0,navegado=0,cant_lineas=0,linea1=0,linea2=0,linea3=0,linea4=0,linea5=0,linea6=0,linea7=0,linea8=0,linea9=0,linea10=0,linea11=0,linea12=0,linea13=0,linea14=0,linea15=0,linea16=0,linea17=0,linea18=0,linea19=0,linea20=0,linea21=0,linea22=0,linea23=0,linea24=0,linea25=0,linea26=0,linea27=0,linea28=0,linea29=0,linea30=0,linea31=0,linea32=0,fases=0,tension=0,aux2=0,aux3=0,aux4=0,aux5=07,aux6=0,aux7=0,aux8=0,alim=0 WHERE geoname = @geoname INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'BORRO_NODO', NOMBRE + ';' + (CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[XCOORD])) +';'+ CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[YCOORD]))) FROM DELETED WHERE GEONAME = @geoname INSERT INTO Nodos_Borrados SELECT * FROM DELETED WHERE GEONAME = @geoname END FETCH NEXT FROM RS INTO @geoname, @nombre, @elmt, @tension END CLOSE RS DEALLOCATE RS END")
                cursor.execute("ALTER TABLE Nodos ENABLE TRIGGER Borro_Nodos")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TRIGGER [Creo_Nodos] ON [Nodos] AFTER INSERT AS BEGIN SET NOCOUNT ON DECLARE @aux INT DECLARE @geoname INT DECLARE @elmt SMALLINT DECLARE @tension INT DECLARE @flag_nuevo_aux TINYINT SELECT @geoname = geoname, @elmt = ISNULL(elmt, 0), @tension = tension FROM INSERTED IF @tension>0 BEGIN SELECT @aux = MAX(aux) FROM mNodos WHERE geoname=0 SET @flag_nuevo_aux=0 IF @aux=0 BEGIN SELECT @aux = COUNT(*) FROM mNodos SET @flag_nuevo_aux=1 END IF @flag_nuevo_aux=0 BEGIN UPDATE mNodos SET geoname=@geoname,estado=@elmt,navegado=0,cant_lineas=0,linea1=0,linea2=0,linea3=0,linea4=0,linea5=0,linea6=0,linea7=0,linea8=0,linea9=0,linea10=0,linea11=0,linea12=0,linea13=0,linea14=0,linea15=0,linea16=0,linea17=0,linea18=0,linea19=0,linea20=0,linea21=0,linea22=0,linea23=0,linea24=0,linea25=0,linea26=0,linea27=0,linea28=0,linea29=0,linea30=0,linea31=0,linea32=0,fases=0,tension=@tension,aux2=@elmt,aux3=0,aux4=0,aux5=0,aux6=0,aux7=0,aux8=0,alim=0 WHERE aux=@aux END IF @flag_nuevo_aux=1 BEGIN INSERT INTO mNodos (aux,geoname,estado,navegado,cant_lineas,linea1,linea2,linea3,linea4,linea5,linea6,linea7,linea8,linea9,linea10,linea11,linea12,linea13,linea14,linea15,linea16,linea17,linea18,linea19,linea20,linea21,linea22,linea23,linea24,linea25,linea26,linea27,linea28,linea29,linea30,linea31,linea32,fases,tension,aux2,aux3,aux4,aux5,aux6,aux7,aux8,alim) VALUES (@aux,@geoname,@elmt,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,@tension,@elmt,0,0,0,0,0,0,0) END END END")
                cursor.execute("ALTER TABLE Nodos ENABLE TRIGGER Creo_Nodos")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TRIGGER [Actualizo_Lineas] ON [Lineas] AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @quiebres VARCHAR(255) DECLARE @SRID SMALLINT DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(6,2) DECLARE @ddy DECIMAL(6,2) SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @xant = @X SET @yant = @Y SET @str_quiebres = '' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END UPDATE Lineas SET longitud=obj.STLength(), quiebres=@str_quiebres WHERE Geoname = @geoname INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT @geoname, GETDATE(),'ACTUALIZO_LINEA', @quiebres FROM INSERTED FETCH NEXT FROM RS INTO @geoname, @obj END CLOSE RS DEALLOCATE RS END END")
                cursor.execute("ALTER TABLE Lineas ENABLE TRIGGER Actualizo_Lineas")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TRIGGER [Borro_Lineas] ON [Lineas] AFTER DELETE AS BEGIN SET NOCOUNT ON DECLARE @aux INT DECLARE @geoname INT DECLARE @desde INT DECLARE @hasta INT DECLARE @aux_desde INT DECLARE @aux_hasta INT DECLARE @tension INT DECLARE @cant_lineas_desde INT DECLARE @cant_lineas_hasta INT DECLARE @str_sql NVARCHAR(MAX) DECLARE @linea1 INT DECLARE @linea2 INT DECLARE @linea3 INT DECLARE @linea4 INT DECLARE @linea5 INT DECLARE @linea6 INT DECLARE @linea7 INT DECLARE @linea8 INT DECLARE @linea9 INT DECLARE @linea10 INT DECLARE @linea11 INT DECLARE @linea12 INT DECLARE @linea13 INT DECLARE @linea14 INT DECLARE @linea15 INT DECLARE @linea16 INT DECLARE @linea17 INT DECLARE @linea18 INT DECLARE @linea19 INT DECLARE @linea20 INT DECLARE @linea21 INT DECLARE @linea22 INT DECLARE @linea23 INT DECLARE @linea24 INT DECLARE @linea25 INT DECLARE @linea26 INT DECLARE @linea27 INT DECLARE @linea28 INT DECLARE @linea29 INT DECLARE @linea30 INT DECLARE @linea31 INT DECLARE @linea32 INT DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @sql_desde VARCHAR(MAX) DECLARE @sql_hasta VARCHAR(MAX) DECLARE @n SMALLINT DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, desde, hasta, tension FROM DELETED OPEN RS FETCH NEXT FROM RS INTO @geoname, @desde, @hasta, @tension WHILE (@@FETCH_STATUS = 0) BEGIN IF @tension>0 BEGIN SELECT @aux = aux FROM mLineas WHERE Geoname = @geoname SELECT @aux_desde=aux,@cant_lineas_desde=cant_lineas,@linea1=linea1,@linea2=linea2,@linea3=linea3,@linea4=linea4,@linea5=linea5,@linea6=linea6,@linea7=linea7,@linea8=linea8,@linea9=linea9,@linea10=linea10,@linea11=linea11,@linea12=linea12,@linea13=linea13,@linea14=linea14,@linea15=linea15,@linea16=linea16,@linea17=linea17,@linea18=linea18,@linea19=linea19,@linea20=linea20,@linea21=linea21,@linea22=linea22,@linea23=linea23,@linea24=linea24,@linea25=linea25,@linea26=linea26,@linea27=linea27,@linea28=linea28,@linea29=linea29,@linea30=linea30,@linea31=linea31,@linea32=linea32 FROM mNodos WHERE Geoname = @desde SET @i=0 IF @linea1=@aux BEGIN SET @i=1 END IF @linea2=@aux BEGIN SET @i=2 END IF @linea3=@aux BEGIN SET @i=3 END IF @linea4=@aux BEGIN SET @i=4 END IF @linea5=@aux BEGIN SET @i=5 END IF @linea6=@aux BEGIN SET @i=6 END IF @linea7=@aux BEGIN SET @i=7 END IF @linea8=@aux BEGIN SET @i=8 END IF @linea9=@aux BEGIN SET @i=9 END IF @linea10=@aux BEGIN SET @i=10 END IF @linea11=@aux BEGIN SET @i=11 END IF @linea12=@aux BEGIN SET @i=12 END IF @linea13=@aux BEGIN SET @i=13 END IF @linea14=@aux BEGIN SET @i=14 END IF @linea15=@aux BEGIN SET @i=15 END IF @linea16=@aux BEGIN SET @i=16 END IF @linea17=@aux BEGIN SET @i=17 END IF @linea18=@aux BEGIN SET @i=18 END IF @linea19=@aux BEGIN SET @i=19 END IF @linea20=@aux BEGIN SET @i=20 END IF @linea21=@aux BEGIN SET @i=21 END IF @linea22=@aux BEGIN SET @i=22 END IF @linea23=@aux BEGIN SET @i=23 END IF @linea24=@aux BEGIN SET @i=24 END IF @linea25=@aux BEGIN SET @i=25 END IF @linea26=@aux BEGIN SET @i=26 END IF @linea27=@aux BEGIN SET @i=27 END IF @linea28=@aux BEGIN SET @i=28 END IF @linea29=@aux BEGIN SET @i=29 END IF @linea30=@aux BEGIN SET @i=30 END IF @linea31=@aux BEGIN SET @i=31 END IF @linea32=@aux BEGIN SET @i=32 END SET @sql_desde='' SET @n=@i IF @n=0 BEGIN SET @n=1 END WHILE @n < 32 BEGIN SET @sql_desde=@sql_desde + ',linea' + CAST(@n AS VARCHAR) + '=linea' + CAST(@n+1 AS VARCHAR) SET @n = @n + 1 END SET @sql_desde=@sql_desde + ',linea32=0' SELECT @aux_hasta=aux,@cant_lineas_hasta=cant_lineas,@linea1=linea1,@linea2=linea2,@linea3=linea3,@linea4=linea4,@linea5=linea5,@linea6=linea6,@linea7=linea7,@linea8=linea8,@linea9=linea9,@linea10=linea10,@linea11=linea11,@linea12=linea12,@linea13=linea13,@linea14=linea14,@linea15=linea15,@linea16=linea16,@linea17=linea17,@linea18=linea18,@linea19=linea19,@linea20=linea20,@linea21=linea21,@linea22=linea22,@linea23=linea23,@linea24=linea24,@linea25=linea25,@linea26=linea26,@linea27=linea27,@linea28=linea28,@linea29=linea29,@linea30=linea30,@linea31=linea31,@linea32=linea32 FROM mNodos WHERE Geoname = @hasta SET @j=0 IF @linea1=@aux BEGIN SET @j=1 END IF @linea2=@aux BEGIN SET @j=2 END IF @linea3=@aux BEGIN SET @j=3 END IF @linea4=@aux BEGIN SET @j=4 END IF @linea5=@aux BEGIN SET @j=5 END IF @linea6=@aux BEGIN SET @j=6 END IF @linea7=@aux BEGIN SET @j=7 END IF @linea8=@aux BEGIN SET @j=8 END IF @linea9=@aux BEGIN SET @j=9 END IF @linea10=@aux BEGIN SET @j=10 END IF @linea11=@aux BEGIN SET @j=11 END IF @linea12=@aux BEGIN SET @j=12 END IF @linea13=@aux BEGIN SET @j=13 END IF @linea14=@aux BEGIN SET @j=14 END IF @linea15=@aux BEGIN SET @j=15 END IF @linea16=@aux BEGIN SET @j=16 END IF @linea17=@aux BEGIN SET @j=17 END IF @linea18=@aux BEGIN SET @j=18 END IF @linea19=@aux BEGIN SET @j=19 END IF @linea20=@aux BEGIN SET @j=20 END IF @linea21=@aux BEGIN SET @j=21 END IF @linea22=@aux BEGIN SET @j=22 END IF @linea23=@aux BEGIN SET @j=23 END IF @linea24=@aux BEGIN SET @j=24 END IF @linea25=@aux BEGIN SET @j=25 END IF @linea26=@aux BEGIN SET @j=26 END IF @linea27=@aux BEGIN SET @j=27 END IF @linea28=@aux BEGIN SET @j=28 END IF @linea29=@aux BEGIN SET @j=29 END IF @linea30=@aux BEGIN SET @j=30 END IF @linea31=@aux BEGIN SET @j=31 END IF @linea32=@aux BEGIN SET @j=32 END SET @sql_hasta='' SET @n=@j IF @n=0 BEGIN SET @n=1 END WHILE @n < 32 BEGIN SET @sql_hasta=@sql_hasta + ',linea' + CAST(@n AS VARCHAR) + '=linea' + CAST(@n+1 AS VARCHAR) SET @n = @n + 1 END SET @sql_hasta=@sql_hasta + ',linea32=0' UPDATE mLineas SET geoname=0,desde=0,hasta=0,fuente=0,tension=0,fases=0 WHERE geoname = @geoname SET @str_sql = 'UPDATE mNodos SET cant_lineas = ' + CAST(@cant_lineas_desde - 1 AS VARCHAR) + @sql_desde + ' WHERE geoname =' + CAST(@desde AS VARCHAR) EXEC sp_executesql @str_sql SET @str_sql = 'UPDATE mNodos SET cant_lineas = ' + CAST(@cant_lineas_hasta - 1 AS VARCHAR) + @sql_hasta + ' WHERE geoname =' + CAST(@hasta AS VARCHAR) EXEC sp_executesql @str_sql UPDATE B SET d=o FROM (SELECT mNodos.Fases AS d, A.Fases AS o FROM mNodos INNER JOIN (SELECT F.Geoname, MAX(F.Fases) AS Fases FROM (SELECT mNodos.Geoname, CONVERT(SMALLINT, mLineas.Fases) AS Fases FROM mLineas INNER JOIN mNodos ON mLineas.Desde = mNodos.Aux UNION SELECT mNodos.Geoname, CONVERT(SMALLINT, mLineas.Fases) AS Fases FROM mLineas INNER JOIN mNodos ON mLineas.Hasta = mNodos.Aux) F GROUP BY F.Geoname) A ON mNodos.Geoname=A.Geoname WHERE mNodos.geoname IN (@desde,@hasta)) B INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'BORRO_LINEA',LEFT(CONVERT(VARCHAR,DESDE) + ';' + CONVERT(VARCHAR,HASTA) + ';' + CONVERT(VARCHAR,ELMT) + ';' + QUIEBRES,255) FROM DELETED WHERE GEONAME = @geoname INSERT INTO Lineas_Borradas SELECT * FROM DELETED WHERE GEONAME = @geoname END FETCH NEXT FROM RS INTO @geoname, @desde, @hasta, @tension END CLOSE RS DEALLOCATE RS END")
                cursor.execute("ALTER TABLE Lineas ENABLE TRIGGER Borro_Lineas")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TRIGGER [Creo_Lineas] ON [Lineas] AFTER INSERT AS BEGIN SET NOCOUNT ON DECLARE @aux INT DECLARE @geoname INT DECLARE @fases SMALLINT DECLARE @fases_desde SMALLINT DECLARE @fases_hasta SMALLINT DECLARE @desde INT DECLARE @hasta INT DECLARE @aux_desde INT DECLARE @aux_hasta INT DECLARE @cant_lineas_desde INT DECLARE @cant_lineas_hasta INT DECLARE @tension INT DECLARE @flag_nuevo_aux TINYINT DECLARE @str_sql NVARCHAR(MAX) DECLARE @obj GEOMETRY SELECT @geoname = geoname, @fases = fase, @desde = desde, @hasta = hasta, @tension = tension, @obj=obj FROM INSERTED IF @tension>0 BEGIN IF NOT (SELECT TOP 1 geoname FROM Lineas WHERE (desde=@desde AND hasta=@hasta OR desde=@hasta and hasta=@desde) AND geoname<>@geoname) IS NULL BEGIN RAISERROR ('Ya existe una linea entre esos dos nodos', 16, 1) END ELSE BEGIN SELECT @aux = MAX(aux) FROM mLineas WHERE geoname=0 SET @flag_nuevo_aux=0 IF @aux=0 BEGIN SELECT @aux = COUNT(*) FROM mLineas SET @flag_nuevo_aux=1 END SELECT @aux_desde = aux, @cant_lineas_desde = cant_lineas + 1, @fases_desde=fases FROM mNodos WHERE Geoname = @desde SELECT @aux_hasta = aux, @cant_lineas_hasta = cant_lineas + 1, @fases_hasta=fases FROM mNodos WHERE Geoname = @hasta IF @flag_nuevo_aux=0 BEGIN UPDATE mLineas SET geoname=@geoname,desde=@aux_desde,hasta=@aux_hasta,fuente=0,tension=@tension,fases=@fases WHERE aux=@aux END IF @flag_nuevo_aux=1 BEGIN INSERT INTO mLineas (aux,geoname,desde,hasta,fuente,tension,fases,aux2,aux3,aux4,aux5,aux6,aux7) VALUES (@aux,@geoname,@aux_desde,@aux_hasta,0,@tension,@fases,0,0,0,0,0,0) END SET @fases = MAXIMO(@fases,@fases_desde) SET @fases = MAXIMO(@fases,@fases_hasta) SET @str_sql = 'UPDATE mNodos SET cant_lineas = ' + CAST(@cant_lineas_desde AS VARCHAR) + ', linea' + CAST(@cant_lineas_desde AS VARCHAR) + '=' + CAST(@aux AS VARCHAR) + ', fases = ' + CAST(@fases AS VARCHAR) + ' WHERE geoname =' + CAST(@desde AS VARCHAR) EXEC sp_executesql @str_sql SET @str_sql = 'UPDATE mNodos SET cant_lineas = ' + CAST(@cant_lineas_hasta AS VARCHAR) + ', linea' + CAST(@cant_lineas_hasta AS VARCHAR) + '=' + CAST(@aux AS VARCHAR) + ', fases = ' + CAST(@fases AS VARCHAR) + ' WHERE geoname =' + CAST(@hasta AS VARCHAR) EXEC sp_executesql @str_sql DECLARE @quiebres VARCHAR(255) DECLARE @SRID SMALLINT DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(6,2) DECLARE @ddy DECIMAL(6,2) SELECT geoname, obj FROM INSERTED SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @xant = @X SET @yant = @Y SET @str_quiebres = '' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END UPDATE Lineas SET quiebres=@str_quiebres WHERE Geoname = @geoname INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT @geoname, GETDATE(),'ACTUALIZO_LINEA', @quiebres FROM INSERTED END END END")
                cursor.execute("ALTER TABLE Lineas ENABLE TRIGGER Creo_Lineas")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TRIGGER Actualizo_Postes ON Postes AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname WHILE (@@FETCH_STATUS = 0) BEGIN EXEC Normalizar_Poste @geoname, @SRID FETCH NEXT FROM RS INTO @geoname END CLOSE RS DEALLOCATE RS INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'ACTUALIZO_POSTE',(CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),XCOORD)) +';'+ CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),YCOORD))) FROM INSERTED END END")
                cursor.execute("ALTER TABLE Postes ENABLE TRIGGER Actualizo_Postes")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TRIGGER Borro_Postes ON Postes AFTER DELETE AS BEGIN SET NOCOUNT ON INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'BORRO_POSTE',(CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),XCOORD)) +';'+ CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),YCOORD))) FROM DELETED END")
                cursor.execute("ALTER TABLE Postes ENABLE TRIGGER Borro_Postes")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TRIGGER Actualizo_Areas ON Areas AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @Xc DECIMAL(9,2) DECLARE @Yc DECIMAL(9,2) DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(9,2) DECLARE @ddy DECIMAL(9,2) DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @Xc = @obj.STCentroid().STX SET @Yc = @obj.STCentroid().STY SET @xant = @Xc SET @yant = @Yc SET @str_quiebres = '' SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) UPDATE Areas SET xcoord=@Xc, ycoord=@Yc, quiebres=@str_quiebres WHERE Geoname = @geoname FETCH NEXT FROM RS INTO @geoname, @obj END CLOSE RS DEALLOCATE RS END END")
                cursor.execute("ALTER TABLE Areas ENABLE TRIGGER Actualizo_Areas")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TRIGGER Creo_Areas ON  Areas AFTER INSERT AS BEGIN SET NOCOUNT ON DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @Xc DECIMAL(9,2) DECLARE @Yc DECIMAL(9,2) DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(9,2) DECLARE @ddy DECIMAL(9,2) DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @geoname=geoname, @obj=obj FROM INSERTED SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @Xc = @obj.STCentroid().STX SET @Yc = @obj.STCentroid().STY SET @xant = @Xc SET @yant = @Yc SET @str_quiebres = '' SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) UPDATE Areas SET xcoord=@Xc, ycoord=@Yc, quiebres=@str_quiebres WHERE Geoname = @geoname END")
                cursor.execute("ALTER TABLE Areas ENABLE TRIGGER Creo_Areas")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TRIGGER Actualizo_Parcelas ON Parcelas AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @Xc DECIMAL(9,2) DECLARE @Yc DECIMAL(9,2) DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(9,2) DECLARE @ddy DECIMAL(9,2) DECLARE @SRID SMALLINT 	 SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @Xc = @obj.STCentroid().STX SET @Yc = @obj.STCentroid().STY SET @xant = @Xc SET @yant = @Yc SET @str_quiebres = '' SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) UPDATE Parcelas SET xcoord=@Xc, ycoord=@Yc, quiebres=@str_quiebres WHERE Geoname = @geoname FETCH NEXT FROM RS INTO @geoname, @obj END CLOSE RS DEALLOCATE RS END END")
                cursor.execute("ALTER TABLE Parcelas ENABLE TRIGGER Actualizo_Parcelas")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TRIGGER Creo_Parcelas ON  Parcelas AFTER INSERT AS BEGIN SET NOCOUNT ON DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @Xc DECIMAL(9,2) DECLARE @Yc DECIMAL(9,2) DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(9,2) DECLARE @ddy DECIMAL(9,2) DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @geoname=geoname, @obj=obj FROM INSERTED SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @Xc = @obj.STCentroid().STX SET @Yc = @obj.STCentroid().STY SET @xant = @Xc SET @yant = @Yc SET @str_quiebres = '' SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) UPDATE Parcelas SET xcoord=@Xc, ycoord=@Yc, quiebres=@str_quiebres WHERE Geoname = @geoname END")
                cursor.execute("ALTER TABLE Parcelas ENABLE TRIGGER Creo_Parcelas")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TRIGGER Actualizo_Ejes ON Ejes AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @SRID SMALLINT DECLARE @str_obj VARCHAR(MAX) DECLARE @str_izquierda VARCHAR(50) DECLARE @str_derecha VARCHAR(50) DECLARE @X1 DECIMAL(9,2) DECLARE @Y1 DECIMAL(9,2) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @X2 DECIMAL(9,2) DECLARE @Y2 DECIMAL(9,2) SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_izquierda = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_izquierda) SET @X1 = CAST(LEFT(@str_izquierda, @k-1) AS decimal(9,2)) SET @Y1 = CAST(RIGHT(@str_izquierda, LEN(@str_izquierda)-@k) AS decimal(9,2)) set @str_derecha = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_izquierda)-2) SELECT @k = CHARINDEX(' ', @str_obj) SET @X2 = CAST(LEFT(@str_derecha, @k-1) AS decimal(9,2)) SET @Y2 = CAST(RIGHT(@str_derecha, LEN(@str_derecha)-@k) AS decimal(9,2)) UPDATE Ejes SET X1=@X1, y1=@y1, X2=@X2, Y2=@Y2 WHERE Geoname = @geoname FETCH NEXT FROM RS INTO @geoname, @obj END CLOSE RS DEALLOCATE RS END END")
                cursor.execute("ALTER TABLE Ejes ENABLE TRIGGER Actualizo_Ejes")
                conn.commit()
            except:
                conn.rollback()
            pass
        if version_instalada1<=5 and version_instalada2<=0 and version_instalada3<=17:
            try:
                cursor.execute("ALTER TABLE Nodos ADD giro FLOAT")
                cursor.execute("ALTER TABLE NodosOk ADD giro FLOAT")
                cursor.execute("ALTER TABLE Nodos_Borrados ADD giro FLOAT")
                cursor.execute("ALTER TABLE Postes ADD giro FLOAT")
                cursor.execute("ALTER TABLE PostesOk ADD giro FLOAT")
                cursor.execute("UPDATE Nodos SET giro=0")
                cursor.execute("UPDATE NodosOk SET giro=0")
                cursor.execute("UPDATE Postes SET giro=0")
                cursor.execute("UPDATE PostesOk SET giro=0")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=0 and version_instalada3<=18:
            try:
                cursor.execute("CREATE TABLE [Proyectos]([nombre] [varchar](15) NOT NULL, [descripcion] [varchar](100) NULL, [fecha] [date] NULL, CONSTRAINT [PK_Proyectos_1] PRIMARY KEY CLUSTERED ([nombre] ASC) ON [PRIMARY]) ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
                #QMessageBox.warning(None, 'EnerGis 5', "Debe corregirse la tabla Proyectos para poder actualizar la versión")
                #return
            try:
                cursor.execute("CREATE TABLE [Cotas]([id] [int] IDENTITY(1,1) NOT NULL, [proyecto] [varchar](15) NOT NULL, [etiqueta] [varchar](50) NULL, [obj] [geometry] NOT NULL, CONSTRAINT [PK_Cotas] PRIMARY KEY CLUSTERED ([id] ASC) ON [PRIMARY] ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("ALTER TABLE [Cotas]  WITH CHECK ADD  CONSTRAINT [FK_Cotas_Proyectos] FOREIGN KEY([proyecto]) REFERENCES [Proyectos] ([nombre]) ON DELETE CASCADE")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("ALTER TABLE [Cotas] CHECK CONSTRAINT [FK_Cotas_Proyectos]")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=0 and version_instalada3<=22:
            try:
                cursor.execute("DROP TABLE Transformadores_Parametros")
                cursor.execute("CREATE TABLE [Transformadores_Parametros]([Id_Trafo] [int] NOT NULL,[R1] [float] NULL,[X1] [float] NULL,[P01] [real] NULL,[Tap1] [real] NULL, CONSTRAINT [aaaaaTransformadores_Parametros_PK] PRIMARY KEY CLUSTERED ([Id_Trafo] ASC) ON [PRIMARY]) ON [PRIMARY]")
                cursor.execute("ALTER TABLE [Transformadores_Parametros] ADD  DEFAULT (0) FOR [Id_Trafo]")
                cursor.execute("ALTER TABLE [Transformadores_Parametros] ADD  DEFAULT (0) FOR [R1]")
                cursor.execute("ALTER TABLE [Transformadores_Parametros] ADD  DEFAULT (0) FOR [X1]")
                cursor.execute("ALTER TABLE [Transformadores_Parametros] ADD  DEFAULT (0) FOR [P01]")
                cursor.execute("ALTER TABLE [Transformadores_Parametros] ADD  DEFAULT (0) FOR [Tap1]")
                cursor.execute("ALTER TABLE [Transformadores_Parametros]  WITH NOCHECK ADD  CONSTRAINT [Transformadores_Parametro_FK00] FOREIGN KEY([Id_Trafo]) REFERENCES [Transformadores] ([Id_trafo]) ON UPDATE CASCADE ON DELETE CASCADE")
                cursor.execute("INSERT INTO Transformadores_Parametros SELECT Transformadores.Id_trafo, 0.01 AS R1, 0.05 AS X1, 18.276*POWER(Potencia,0.689) AS P01, 100 AS Tap1 FROM Transformadores WHERE Id_Trafo NOT IN (SELECT Id_Trafo FROM Transformadores_Parametros)")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE FUNCTION SplitString (@String NVARCHAR(MAX), @Delimiter CHAR(1)) RETURNS @Result TABLE (Item NVARCHAR(100)) AS BEGIN DECLARE @Pos INT DECLARE @Item NVARCHAR(100) WHILE CHARINDEX(@Delimiter, @String) > 0 BEGIN SET @Pos = CHARINDEX(@Delimiter, @String) SET @Item = SUBSTRING(@String, 1, @Pos - 1) INSERT INTO @Result (Item) VALUES (@Item) SET @String = SUBSTRING(@String, @Pos + 1, LEN(@String) - @Pos) END INSERT INTO @Result (Item) VALUES (@String) RETURN END")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("DROP TABLE Cargas")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TABLE [Cargas]([Id_Usuario] [int] NOT NULL,[EtF] [float] NULL,[dias] [float] NULL,[P] [float] NULL,[Q] [float] NULL,[Fe] [float] NULL,[Carga00] [float] NULL,[Carga01] [float] NULL,[Carga02] [float] NULL,[Carga03] [float] NULL,[Carga04] [float] NULL,[Carga05] [float] NULL,[Carga06] [float] NULL,[Carga07] [float] NULL,[Carga08] [float] NULL,[Carga09] [float] NULL,[Carga10] [float] NULL,[Carga11] [float] NULL,[Carga12] [float] NULL,[Carga13] [float] NULL,[Carga14] [float] NULL,[Carga15] [float] NULL,[Carga16] [float] NULL,[Carga17] [float] NULL,[Carga18] [float] NULL,[Carga19] [float] NULL,[Carga20] [float] NULL,[Carga21] [float] NULL,[Carga22] [float] NULL,[Carga23] [float] NULL, CONSTRAINT [aaaaaCargas_PK] PRIMARY KEY NONCLUSTERED ([Id_Usuario] ASC) ON [PRIMARY]) ON [PRIMARY]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Id_Nodo] DEFAULT ((0)) FOR [Id_Usuario]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load1] DEFAULT ((0)) FOR [P]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load2] DEFAULT ((0)) FOR [Q]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load00] DEFAULT ((0)) FOR [Carga00]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load01] DEFAULT ((0)) FOR [Carga01]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load02] DEFAULT ((0)) FOR [Carga02]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load03] DEFAULT ((0)) FOR [Carga03]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load04] DEFAULT ((0)) FOR [Carga04]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load05] DEFAULT ((0)) FOR [Carga05]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load06] DEFAULT ((0)) FOR [Carga06]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load07] DEFAULT ((0)) FOR [Carga07]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load08] DEFAULT ((0)) FOR [Carga08]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load09] DEFAULT ((0)) FOR [Carga09]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load10] DEFAULT ((0)) FOR [Carga10]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load11] DEFAULT ((0)) FOR [Carga11]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load12] DEFAULT ((0)) FOR [Carga12]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load13] DEFAULT ((0)) FOR [Carga13]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load14] DEFAULT ((0)) FOR [Carga14]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load15] DEFAULT ((0)) FOR [Carga15]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load16] DEFAULT ((0)) FOR [Carga16]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load17] DEFAULT ((0)) FOR [Carga17]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load18] DEFAULT ((0)) FOR [Carga18]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load19] DEFAULT ((0)) FOR [Carga19]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load20] DEFAULT ((0)) FOR [Carga20]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load21] DEFAULT ((0)) FOR [Carga21]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load22] DEFAULT ((0)) FOR [Carga22]")
                cursor.execute("ALTER TABLE [Cargas] ADD  CONSTRAINT [DF__Cargas__Load23] DEFAULT ((0)) FOR [Carga23]")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TABLE [Cargas_Nodos]([geoname] [int] NOT NULL,[P] [float] NULL,[Q] [float] NULL,[Fe] [float] NULL, CONSTRAINT [PK_Cargas_Nodos] PRIMARY KEY CLUSTERED ([geoname] ASC) ON [PRIMARY]) ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE PROCEDURE [Crear_Cargas] @USUARIOS VARCHAR(MAX), @FC FLOAT, @FP FLOAT, @DESDE DATE, @HASTA DATE AS BEGIN SET NOCOUNT ON IF @USUARIOS ='0' BEGIN TRUNCATE TABLE Cargas INSERT INTO Cargas SELECT PT.id_usuario,EtF,dias,P,Q,1 AS Fe,[0] AS Carga00,[1] AS Carga01,[2] AS Carga02,[3] AS Carga03,[4] AS Carga04,[5] AS Carga05,[6] AS Carga06, [7] AS Carga07,[8] AS Carga08,[9] AS Carga09,[10] AS Carga10,[11] AS Carga11,[12] AS Carga12, [13] AS Carga13,[14] AS Carga14,[15] AS Carga15,[16] AS Carga16,[17] AS Carga17,[18] AS Carga18, [19] AS Carga19,[20] AS Carga20,[21] AS Carga21,[22] AS Carga22,[23] AS Carga23 FROM (SELECT Usuarios.id_usuario, Curvas_ki.Hora, Curvas_ki.ki FROM Usuarios INNER JOIN Curvas_ki ON Usuarios.tarifa = Curvas_ki.Tarifa) AS ki PIVOT (SUM(ki) FOR Hora IN ([0],[1],[2],[3],[4],[5],[6],[7],[8],[9],[10],[11],[12],[13],[14],[15],[16],[17],[18],[19],[20],[21],[22],[23])) AS PT INNER JOIN (SELECT id_usuario, SUM(EtF) AS EtF, DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) AS Dias, SUM(EtF) / DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) / 24 / @FC AS P, SUM(EtF) * TAN(ACOS(@FP)) / DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) / 24 / @FC AS Q FROM Energia_Facturada WHERE (Desde >= @DESDE) AND (Hasta <= @HASTA) GROUP BY id_usuario) P ON PT.id_usuario=P.id_usuario END DELETE FROM Cargas WHERE id_usuario IN (SELECT Item AS Valor FROM SplitString(@USUARIOS, ',')) INSERT INTO Cargas SELECT PT.id_usuario,EtF,dias,P,Q,1 AS Fe,[0] AS Carga00,[1] AS Carga01,[2] AS Carga02,[3] AS Carga03,[4] AS Carga04,[5] AS Carga05,[6] AS Carga06, [7] AS Carga07,[8] AS Carga08,[9] AS Carga09,[10] AS Carga10,[11] AS Carga11,[12] AS Carga12, [13] AS Carga13,[14] AS Carga14,[15] AS Carga15,[16] AS Carga16,[17] AS Carga17,[18] AS Carga18, [19] AS Carga19,[20] AS Carga20,[21] AS Carga21,[22] AS Carga22,[23] AS Carga23 FROM (SELECT Usuarios.id_usuario, Curvas_ki.Hora, Curvas_ki.ki FROM Usuarios INNER JOIN Curvas_ki ON Usuarios.tarifa = Curvas_ki.Tarifa) AS ki PIVOT (SUM(ki) FOR Hora IN ([0],[1],[2],[3],[4],[5],[6],[7],[8],[9],[10],[11],[12],[13],[14],[15],[16],[17],[18],[19],[20],[21],[22],[23])) AS PT INNER JOIN (SELECT id_usuario, SUM(EtF) AS EtF, DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) AS Dias, SUM(EtF) / DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) / 24 / @FC AS P, SUM(EtF) * TAN(ACOS(@FP)) / DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) / 24 / @FC AS Q FROM Energia_Facturada WHERE (Desde >= @DESDE) AND (Hasta <= @HASTA) GROUP BY id_usuario) P ON PT.id_usuario=P.id_usuario WHERE PT.id_usuario IN (SELECT Item AS Valor FROM SplitString(@USUARIOS, ',')) END")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=0 and version_instalada3<=28:
            try:
                cursor.execute("ALTER TABLE Elementos_Lineas ADD uso SMALLINT")
                cursor.execute("UPDATE Elementos_Lineas SET uso=1")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=0 and version_instalada3<=29:
            try:
                cursor.execute("CREATE TABLE Anotaciones([geoname] [int] NOT NULL, [proyecto] [varchar](50) NOT NULL, [etiqueta] [varchar](50) NOT NULL, [obj] [geometry] NOT NULL, CONSTRAINT [PK_Anotaciones] PRIMARY KEY CLUSTERED ([geoname] ASC) ON [PRIMARY]) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=0 and version_instalada3<=31:
            try:
                cursor.execute("CREATE PROCEDURE [Mover_Anotacion] @ANOTACION INT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(17,10) DECLARE @Y DECIMAL(17,10) DECLARE @LINEA INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=obj FROM Anotaciones WHERE Geoname = @ANOTACION SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POINT (','') SET @str_obj = REPLACE(@str_obj, ')','') SELECT @i = CHARINDEX(' ', @str_obj) SET @X = LEFT(@str_obj, @i-1) + @DX SET @Y = RIGHT(@str_obj, LEN(@str_obj)-@i) + @DY SET @str_obj = 'POINT (' + CAST(@X AS VARCHAR) + ' ' +  CAST(@Y AS VARCHAR) + ')' UPDATE Anotaciones SET obj=geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname=@ANOTACION END")
                cursor.execute("CREATE PROCEDURE [Mover_Cota] @COTA INT, @VERTICE SMALLINT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @X1 DECIMAL(9,2) DECLARE @Y1 DECIMAL(9,2) DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_par VARCHAR(MAX) DECLARE @str_final VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @SRID SMALLINT DECLARE @v SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj= Cotas.obj FROM Cotas WHERE Cotas.id = @COTA SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SET @str_final='LINESTRING (' SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=1 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @X1=@X SET @Y1=@Y SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) set @str_par = @str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2))IF @VERTICE<>1 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) SET @str_final = @str_final + ')' UPDATE Cotas SET obj=geometry::STGeomFromText(@str_final, @SRID) WHERE id = @COTA END")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=0 and version_instalada3<=32:
            try:
                cursor.execute("CREATE TABLE [Energias_DPE]([Id_Usuario] [int] NOT NULL,[Periodo] [varchar](6) NOT NULL,[Tipo_Periodo] [varchar](1) NULL,[Tarifa] [varchar](15) NULL,[Contrato_Especial] [varchar](1) NULL,[E] [float] NULL,[Ep] [float] NULL,[Efp] [float] NULL,[Er] [float] NULL,[Ev] [float] NULL,[Pp] [float] NULL,[Pfp] [float] NULL,[Pcp] [float] NULL,[Pcfp] [float] NULL, CONSTRAINT [PK_Energias_DPE] PRIMARY KEY CLUSTERED ([Id_Usuario] ASC,[Periodo] ASC) ON [PRIMARY]) ON [PRIMARY]")
                cursor.execute("ALTER TRIGGER [Borro_Nodos] ON [Nodos] AFTER DELETE AS BEGIN SET NOCOUNT ON DECLARE @geoname INT DECLARE @nombre VARCHAR(50) DECLARE @elmt SMALLINT DECLARE @tension INT DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, nombre, elmt, tension FROM DELETED OPEN RS FETCH NEXT FROM RS INTO @geoname, @nombre, @elmt, @tension WHILE (@@FETCH_STATUS = 0) BEGIN IF @tension>=0 BEGIN DELETE FROM Lineas WHERE Desde=@geoname OR Hasta=@geoname IF @elmt = 6 BEGIN DELETE FROM Suministros WHERE id_nodo = @geoname END IF @elmt = 4 BEGIN UPDATE Transformadores SET id_ct='', usado=1 WHERE id_ct = @nombre END UPDATE mNodos SET geoname=0,estado=0,navegado=0,cant_lineas=0,linea1=0,linea2=0,linea3=0,linea4=0,linea5=0,linea6=0,linea7=0,linea8=0,linea9=0,linea10=0,linea11=0,linea12=0,linea13=0,linea14=0,linea15=0,linea16=0,linea17=0,linea18=0,linea19=0,linea20=0,linea21=0,linea22=0,linea23=0,linea24=0,linea25=0,linea26=0,linea27=0,linea28=0,linea29=0,linea30=0,linea31=0,linea32=0,fases=0,tension=0,aux2=0,aux3=0,aux4=0,aux5=07,aux6=0,aux7=0,aux8=0,alim=0 WHERE geoname = @geoname INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'BORRO_NODO', NOMBRE + ';' + (CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[XCOORD])) +';'+ CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[YCOORD]))) FROM DELETED WHERE GEONAME = @geoname INSERT INTO Nodos_Borrados SELECT * FROM DELETED WHERE GEONAME = @geoname END FETCH NEXT FROM RS INTO @geoname, @nombre, @elmt, @tension END CLOSE RS DEALLOCATE RS END")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=0 and version_instalada3<=41:
            try:
                cursor.execute("ALTER TRIGGER [Actualizo_Lineas] ON [Lineas] AFTER UPDATE AS BEGIN SET NOCOUNT ON; DECLARE @geoname INT IF UPDATE(obj) BEGIN  DECLARE @obj GEOMETRY DECLARE @quiebres VARCHAR(255) DECLARE @SRID SMALLINT DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(6,2) DECLARE @ddy DECIMAL(6,2) SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @xant = @X SET @yant = @Y SET @str_quiebres = '' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END UPDATE Lineas SET longitud=obj.STLength(), quiebres=@str_quiebres WHERE Geoname = @geoname INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT @geoname, GETDATE(),'ACTUALIZO_LINEA', @quiebres FROM INSERTED FETCH NEXT FROM RS INTO @geoname, @obj END CLOSE RS DEALLOCATE RS END IF UPDATE(fase) BEGIN DECLARE @fases SMALLINT DECLARE @desde INT DECLARE @hasta INT DECLARE @fases_desde SMALLINT DECLARE @fases_hasta SMALLINT DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, desde, hasta, CAST(fase AS SMALLINT) FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @desde, @hasta, @fases WHILE (@@FETCH_STATUS = 0) BEGIN UPDATE mLineas SET fases=@fases WHERE geoname=@geoname SELECT @fases_desde=MAX(CAST(fase AS SMALLINT)) FROM Lineas WHERE desde=@desde OR hasta=@desde UPDATE mNodos SET fases=@fases_desde WHERE geoname = @desde SELECT @fases_hasta=MAX(CAST(fase AS SMALLINT)) FROM Lineas WHERE desde=@hasta OR hasta=@hasta UPDATE mNodos SET fases=@fases_hasta WHERE geoname = @hasta INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT @geoname, GETDATE(),'ACTUALIZO_LINEA', @fases FROM INSERTED FETCH NEXT FROM RS INTO @geoname, @desde, @hasta, @fases END CLOSE RS DEALLOCATE RS END END")
                cursor.execute("ALTER TABLE Transformadores ADD aislacion VARCHAR(25)")
                cursor.execute("ALTER TABLE Transformadores ADD peso FLOAT")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=0 and version_instalada3<=46:
            try:
                cursor.execute("CREATE PROCEDURE Normalizar_Postes AS BEGIN DECLARE @geoname INT DECLARE @geoname_linea INT DECLARE @tension INT DECLARE @obj GEOMETRY SET NOCOUNT ON; DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj, tension FROM Postes OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj, @tension WHILE (@@FETCH_STATUS = 0) BEGIN SELECT TOP (1) @geoname_linea = Geoname FROM Lineas WHERE tension=@tension ORDER BY obj.STDistance(@obj) IF NOT @geoname_linea IS NULL BEGIN DELETE FROM Lineas_Postes WHERE id_poste = @geoname INSERT INTO Lineas_Postes (id_linea, id_poste) VALUES (@geoname_linea, @geoname) END FETCH NEXT FROM RS INTO @geoname, @obj, @tension END CLOSE RS DEALLOCATE RS END")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=1 and version_instalada3<=0:
            try:
                cursor.execute("DROP TABLE Cargas")
                cursor.execute("CREATE TABLE [Cargas]([Id_Usuario] [int] NOT NULL,[EtF] [float] NULL,[dias] [float] NULL,[P] [float] NULL,[Q] [float] NULL,[Fe] [float] NULL,[Carga00] [float] NULL,[Carga01] [float] NULL,[Carga02] [float] NULL,[Carga03] [float] NULL,[Carga04] [float] NULL,[Carga05] [float] NULL,[Carga06] [float] NULL,[Carga07] [float] NULL,[Carga08] [float] NULL,[Carga09] [float] NULL,[Carga10] [float] NULL,[Carga11] [float] NULL,[Carga12] [float] NULL,[Carga13] [float] NULL,[Carga14] [float] NULL,[Carga15] [float] NULL,[Carga16] [float] NULL,[Carga17] [float] NULL,[Carga18] [float] NULL,[Carga19] [float] NULL,[Carga20] [float] NULL,[Carga21] [float] NULL,[Carga22] [float] NULL,[Carga23] [float] NULL, CONSTRAINT [aaaaaCargas_PK] PRIMARY KEY NONCLUSTERED ([Id_Usuario] ASC) ON [PRIMARY]) ON [PRIMARY]")
                cursor.execute("CREATE FUNCTION [SplitString] (@String NVARCHAR(MAX), @Delimiter CHAR(1)) RETURNS @Result TABLE (Item NVARCHAR(100)) AS BEGIN DECLARE @Pos INT DECLARE @Item NVARCHAR(100) WHILE CHARINDEX(@Delimiter, @String) > 0 BEGIN SET @Pos = CHARINDEX(@Delimiter, @String) SET @Item = SUBSTRING(@String, 1, @Pos - 1) INSERT INTO @Result (Item) VALUES (@Item) SET @String = SUBSTRING(@String, @Pos + 1, LEN(@String) - @Pos) END INSERT INTO @Result (Item) VALUES (@String) RETURN END")
                cursor.execute("CREATE PROCEDURE [Crear_Cargas] @USUARIOS VARCHAR(15), @FC FLOAT, @FP FLOAT, @DESDE DATE, @HASTA DATE AS BEGIN SET NOCOUNT ON IF @USUARIOS ='0' BEGIN TRUNCATE TABLE Cargas INSERT INTO Cargas SELECT PT.id_usuario,EtF,dias,P,Q,1 AS Fe,[0] AS Carga00,[1] AS Carga01,[2] AS Carga02,[3] AS Carga03,[4] AS Carga04,[5] AS Carga05,[6] AS Carga06, [7] AS Carga07,[8] AS Carga08,[9] AS Carga09,[10] AS Carga10,[11] AS Carga11,[12] AS Carga12, [13] AS Carga13,[14] AS Carga14,[15] AS Carga15,[16] AS Carga16,[17] AS Carga17,[18] AS Carga18, [19] AS Carga19,[20] AS Carga20,[21] AS Carga21,[22] AS Carga22,[23] AS Carga23 FROM (SELECT Usuarios.id_usuario, Curvas_ki.Hora, Curvas_ki.ki FROM Usuarios INNER JOIN Curvas_ki ON Usuarios.tarifa = Curvas_ki.Tarifa) AS ki PIVOT (SUM(ki) FOR Hora IN ([0],[1],[2],[3],[4],[5],[6],[7],[8],[9],[10],[11],[12],[13],[14],[15],[16],[17],[18],[19],[20],[21],[22],[23])) AS PT INNER JOIN (SELECT id_usuario, SUM(EtF) AS EtF, DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) AS Dias, SUM(EtF) / DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) / 24 / @FC AS P, SUM(EtF) * TAN(ACOS(@FP)) / DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) / 24 / @FC AS Q FROM Energia_Facturada WHERE (Desde >= @DESDE) AND (Hasta <= @HASTA) GROUP BY id_usuario) P ON PT.id_usuario=P.id_usuario END DELETE FROM Cargas WHERE id_usuario IN (SELECT Item AS Valor FROM SplitString(@USUARIOS, ',')) INSERT INTO Cargas SELECT PT.id_usuario,EtF,dias,P,Q,1 AS Fe,[0] AS Carga00,[1] AS Carga01,[2] AS Carga02,[3] AS Carga03,[4] AS Carga04,[5] AS Carga05,[6] AS Carga06, [7] AS Carga07,[8] AS Carga08,[9] AS Carga09,[10] AS Carga10,[11] AS Carga11,[12] AS Carga12, [13] AS Carga13,[14] AS Carga14,[15] AS Carga15,[16] AS Carga16,[17] AS Carga17,[18] AS Carga18, [19] AS Carga19,[20] AS Carga20,[21] AS Carga21,[22] AS Carga22,[23] AS Carga23 FROM (SELECT Usuarios.id_usuario, Curvas_ki.Hora, Curvas_ki.ki FROM Usuarios INNER JOIN Curvas_ki ON Usuarios.tarifa = Curvas_ki.Tarifa) AS ki PIVOT (SUM(ki) FOR Hora IN ([0],[1],[2],[3],[4],[5],[6],[7],[8],[9],[10],[11],[12],[13],[14],[15],[16],[17],[18],[19],[20],[21],[22],[23])) AS PT INNER JOIN (SELECT id_usuario, SUM(EtF) AS EtF, DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) AS Dias, SUM(EtF) / DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) / 24 / @FC AS P, SUM(EtF) * TAN(ACOS(@FP)) / DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) / 24 / @FC AS Q FROM Energia_Facturada WHERE (Desde >= @DESDE) AND (Hasta <= @HASTA) GROUP BY id_usuario) P ON PT.id_usuario=P.id_usuario WHERE PT.id_usuario IN (SELECT Item AS Valor FROM SplitString(@USUARIOS, ',')) END")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=1 and version_instalada3<=1:
            try:
                cursor.execute("ALTER PROCEDURE [Crear_Cargas] @USUARIOS VARCHAR(MAX), @FC FLOAT, @FP FLOAT, @DESDE DATE, @HASTA DATE AS BEGIN SET NOCOUNT ON IF @USUARIOS ='0' BEGIN TRUNCATE TABLE Cargas INSERT INTO Cargas SELECT PT.id_usuario,EtF,dias,P,Q,1 AS Fe,[0] AS Carga00,[1] AS Carga01,[2] AS Carga02,[3] AS Carga03,[4] AS Carga04,[5] AS Carga05,[6] AS Carga06, [7] AS Carga07,[8] AS Carga08,[9] AS Carga09,[10] AS Carga10,[11] AS Carga11,[12] AS Carga12, [13] AS Carga13,[14] AS Carga14,[15] AS Carga15,[16] AS Carga16,[17] AS Carga17,[18] AS Carga18, [19] AS Carga19,[20] AS Carga20,[21] AS Carga21,[22] AS Carga22,[23] AS Carga23 FROM (SELECT Usuarios.id_usuario, Curvas_ki.Hora, Curvas_ki.ki FROM Usuarios INNER JOIN Curvas_ki ON Usuarios.tarifa = Curvas_ki.Tarifa) AS ki PIVOT (SUM(ki) FOR Hora IN ([0],[1],[2],[3],[4],[5],[6],[7],[8],[9],[10],[11],[12],[13],[14],[15],[16],[17],[18],[19],[20],[21],[22],[23])) AS PT INNER JOIN (SELECT id_usuario, SUM(EtF) AS EtF, DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) AS Dias, SUM(EtF) / DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) / 24 / @FC AS P, SUM(EtF) * TAN(ACOS(@FP)) / DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) / 24 / @FC AS Q FROM Energia_Facturada WHERE (Desde >= @DESDE) AND (Hasta <= @HASTA) GROUP BY id_usuario) P ON PT.id_usuario=P.id_usuario END DELETE FROM Cargas WHERE id_usuario IN (SELECT Item AS Valor FROM SplitString(@USUARIOS, ',')) INSERT INTO Cargas SELECT PT.id_usuario,EtF,dias,P,Q,1 AS Fe,[0] AS Carga00,[1] AS Carga01,[2] AS Carga02,[3] AS Carga03,[4] AS Carga04,[5] AS Carga05,[6] AS Carga06, [7] AS Carga07,[8] AS Carga08,[9] AS Carga09,[10] AS Carga10,[11] AS Carga11,[12] AS Carga12, [13] AS Carga13,[14] AS Carga14,[15] AS Carga15,[16] AS Carga16,[17] AS Carga17,[18] AS Carga18, [19] AS Carga19,[20] AS Carga20,[21] AS Carga21,[22] AS Carga22,[23] AS Carga23 FROM (SELECT Usuarios.id_usuario, Curvas_ki.Hora, Curvas_ki.ki FROM Usuarios INNER JOIN Curvas_ki ON Usuarios.tarifa = Curvas_ki.Tarifa) AS ki PIVOT (SUM(ki) FOR Hora IN ([0],[1],[2],[3],[4],[5],[6],[7],[8],[9],[10],[11],[12],[13],[14],[15],[16],[17],[18],[19],[20],[21],[22],[23])) AS PT INNER JOIN (SELECT id_usuario, SUM(EtF) AS EtF, DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) AS Dias, SUM(EtF) / DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) / 24 / @FC AS P, SUM(EtF) * TAN(ACOS(@FP)) / DATEDIFF(DAY, MIN(Desde), MAX(Hasta)) / 24 / @FC AS Q FROM Energia_Facturada WHERE (Desde >= @DESDE) AND (Hasta <= @HASTA) GROUP BY id_usuario) P ON PT.id_usuario=P.id_usuario WHERE PT.id_usuario IN (SELECT Item AS Valor FROM SplitString(@USUARIOS, ',')) END")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=2 and version_instalada3<=0:
            try:
                cursor.execute("CREATE VIEW mapSuministros AS SELECT Usuarios.id_usuario, Usuarios.nombre, Usuarios.tarifa, Usuarios.calle, Usuarios.altura, Usuarios.zona, Nodos.Tension, Nodos.obj FROM Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro WHERE Usuarios.ES = 1")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=2 and version_instalada3<=2:
            try:
                cursor.execute("DROP TABLE Alimentadores")
                conn.commit()
                cursor.execute("CREATE TABLE Alimentadores (Id int NOT NULL, Id_Alim varchar (20) NOT NULL, Tension int NOT NULL, cd varchar (15) NULL, ssee varchar (15) NULL, fc float NULL, fu float NULL, fp float NULL, CONSTRAINT PK_Alimentadores PRIMARY KEY CLUSTERED (Id ASC, Id_Alim ASC, Tension ASC) ON [PRIMARY]) ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=4 and version_instalada3<=5:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id_suministro FROM Suministros_Ubicaciones")
                cursor.close()
            except:
                try:
                    cursor.execute("DROP TABLE Suministros_Ubicaciones")
                    conn.commit()
                except:
                    conn.rollback()
            try:
                cursor.execute("CREATE TABLE [Suministros_Ubicaciones]([id_suministro] [varchar](50) NULL, [Lat] [float] NULL, [Lon] [float] NULL) ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=4 and version_instalada3<=12:
            try:
                cursor.execute("CREATE TABLE [Selecciones]([id_usuario_sistema] [int] NOT NULL,[elemento] [smallint] NOT NULL,[geoname] [int] NOT NULL ) ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
        if version_instalada1<=5 and version_instalada2<=4 and version_instalada3<=13:
            try:
                cursor.execute("DELETE FROM Alimentadores")
                conn.commit()
            except:
                conn.rollback()

        if version_instalada1<=5 and version_instalada2<=5 and version_instalada3<=2:
            try:
                cursor.execute("CREATE TABLE Nodos_Transformador (geoname int NOT NULL, Id int NOT NULL, CONSTRAINT [PK_Nodos_Transformador] PRIMARY KEY CLUSTERED ([geoname] ASC) ON [PRIMARY]) ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TABLE Lineas_Transformador (geoname int NOT NULL, Id int NOT NULL, CONSTRAINT [PK_Lineas_Transformador] PRIMARY KEY CLUSTERED ([geoname] ASC) ON [PRIMARY]) ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
            try:
                cursor.execute("CREATE TABLE Transformacion(id_usuario_sistema int NOT NULL, desde int NOT NULL, hasta int NOT NULL) ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
        try:
            cursor.execute("UPDATE Configuracion SET Valor='" + self.version + "' WHERE Variable='Version'")
            conn.commit()
            QMessageBox.information(None, 'EnerGis 5', "Se actualizó la DB a la versión " + self.version)
        except:
            conn.rollback()
        #-------------------------------------------------------------------------------------------------

    def resumen_sistema(self):
        from .frm_resumen_sistema import frmResumenSistema
        self.dialogo = frmResumenSistema(self.conn)
        self.dialogo.show()

    def crear_red(self):
        conn = self.conn
        cursor = conn.cursor()
        try:
            cursor.execute("crear_red")
            conn.commit()
        except:
            conn.rollback()
            QMessageBox.warning(None, 'EnerGis 5', "No se pudo crear la Red !")

    def red_a_estado_normal(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE nodos SET estado=elmt WHERE (elmt=2 OR elmt=3) AND estado<>elmt")
            self.conn.commit()
        except:
            self.conn.rollback()
        self.crear_red
        QMessageBox.information(None, 'EnerGis 5', "Red en Estado Normal")

    def establecer_estado_normal(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE nodos SET elmt=estado WHERE (elmt=2 OR elmt=3) AND estado<>elmt")
            self.conn.commit()
        except:
            self.conn.rollback()
        QMessageBox.information(None, 'EnerGis 5', "Se estableció la Configuración de Red como Estado Normal")

    def ver_elementos_estado_anormal(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 'Nodos' AS Elemento, 'El elemento no está en estado Normal' AS Dedcripcion, Geoname, Nombre FROM nodos WHERE elmt IN (2,3) AND elmt<>estado")
        #convierto el cursor en array
        elementos = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()
        if len(elementos)==0:
            QMessageBox.information(None, 'EnerGis 5', "Todos los Elementos de Maniobra están en Posición Normal")
            return
        from .frm_lista import frmLista
        self.dialogo = frmLista(self.iface.mapCanvas(), encabezado, elementos)
        self.dialogo.setWindowTitle('Resultados de la Verificación : ' + str(len(elementos)) + ' elementos')
        self.dialogo.show()

    def actualizar_zonas(self):
        #----------------------------------------------------------------------------
        progress = QProgressDialog("Procesando...", "Cancelar", 0, 100)
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE A SET d1=o1, d2=o2, d3=o3 FROM (SELECT Areas.nombre AS o1, Areas.descripcion AS o2, Areas.Localidad AS o3, Nodos.Zona AS d1, Nodos.subzona AS d2, Nodos.localidad AS d3 FROM Nodos INNER JOIN Areas ON Areas.obj.STContains(Nodos.obj) = 1) A")
            self.conn.commit()
        except:
            self.conn.rollback()
        #----------------------------------------------------------------------------
        progress.setValue(50)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE A SET d=o FROM (SELECT Areas.nombre AS o, Lineas.Zona AS d FROM Lineas INNER JOIN Areas ON Areas.obj.STIntersects(Lineas.obj.STBuffer(0.001)) = 1) A")
            self.conn.commit()
        except:
            self.conn.rollback()
        #----------------------------------------------------------------------------
        progress.setValue(100)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        QMessageBox.information(None, 'EnerGis 5', "Zonas Asignadas")

    def actualizar_postes_lineas(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("EXEC Normalizar_Postes")
            self.conn.commit()
        except:
            self.conn.rollback()

    def actualizar_alimentadores(self):
        import clr
        from System import Int64
        reply = QMessageBox.question(None, 'EnerGis', 'Desea actualizar alimentadores ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        #----------------------------------------------------------------------------
        progress = QProgressDialog("Procesando...", "Cancelar", 0, 100)
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE mLineas SET alim=0 WHERE alim IS NULL")
            self.conn.commit()
        except:
            self.conn.rollback()
        #----------------------------------------------------------------------------
        progress.setValue(10)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM Alimentadores WHERE Id_Alim NOT IN (SELECT Val1 FROM Nodos WHERE Nodos.Tension>0 AND elmt=8)")
            cursor.execute("INSERT INTO Alimentadores (Id, Id_Alim,Tension,Cd,SSEE,fc,fu,fp) SELECT DISTINCT Aux AS Id, LEFT(Val1, 15) AS Id_Alim, Tension, Descripcion as cd, Val4 as SSEE, 0 AS fc, 0 AS fu, 1 AS fp FROM Nodos WHERE Tension > 1000 AND Elmt = 8 AND (LEFT(Val1, 15) NOT IN (SELECT Id_Alim FROM Alimentadores))")
            cursor.execute("INSERT INTO Alimentadores (Id, Id_Alim,Tension,Cd,SSEE,fc,fu,fp) SELECT DISTINCT Nodos.Aux AS Id, LEFT(Nodos.Val1, 15) AS Id_Alim, Nodos.Tension, Nodos_2.Val4 AS cd, Nodos_2.Descripcion AS SSEE, 0 as fc, 0 as fu, 1 as fp FROM Nodos INNER JOIN Nodos_Transformador ON Nodos.Geoname = Nodos_Transformador.Geoname INNER JOIN Nodos AS Nodos_1 ON Nodos_Transformador.Id = Nodos_1.Geoname INNER JOIN Nodos AS Nodos_2 ON Nodos_1.Alimentador = Nodos_2.Val1 WHERE Nodos.Tension > 0 AND Nodos.Tension < 1000 AND Nodos.Elmt = 8 AND Nodos_2.Elmt = 8 AND LEFT(Nodos.Val1,15) NOT IN (SELECT Id_Alim FROM Alimentadores)")
            cursor.execute("INSERT INTO Alimentadores (Id, Id_Alim,Tension,Cd,SSEE,fc,fu,fp) SELECT DISTINCT Aux, LEFT(Val1,15) AS Id_Alim, Tension,'CD' AS Cd,'SSEE' AS SSEE, 0 AS fc, 0 AS fu, 1 AS fp FROM Nodos WHERE Nodos.Tension>0 AND elmt=8 AND LEFT(Val1,15) NOT IN (SELECT Id_Alim FROM Alimentadores)")
            cursor.execute("UPDATE Alimentadores SET SSEE='SSEE' WHERE SSEE IS NULL")
            cursor.execute("UPDATE Alimentadores SET cd='CD' WHERE cd IS NULL")
            cursor.commit()
        except:
            cursor.rollback()
            QMessageBox.warning(None, 'EnerGis 5', "No se pudieron actualizar Alimentadores !")
        #----------------------------------------------------------------------------
        progress.setValue(20)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        cursor.execute("SELECT aux, geoname FROM mNodos WHERE estado=1")
        fuentes = cursor.fetchall()
        cursor.close()
        #----------------------------------------------------------------------------
        # Cargar el ensamblado
        clr.AddReference(os.path.join(basepath, 'NavRed7.dll'))
        from EnerGis5.NavRed7 import NavRed
        #----------------------------------------------------------------------------
        progress.setValue(30)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        # Instanciar la clase NavRed
        navred_instance = NavRed()
        for fuente in fuentes:
            #----------------------------------------------------------------------------
            progress.setValue(30 + int(50/len(fuentes)))
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            # Preparar los valores de entrada
            fuentenavegada = Int64(fuente[0])
            # Llamar a la función
            resultado = navred_instance.Navegar_a_los_extremos(self.amnodos,self.amlineas,fuentenavegada)
            if resultado[0]!="Ok":
                QMessageBox.critical(None, 'EnerGis 5', resultado[0])
                return
        #----------------------------------------------------------------------------
        progress.setValue(80)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        cursor.execute("SELECT Id, Id_Alim,Tension FROM Alimentadores")
        alimentadores = cursor.fetchall()
        cursor.close()
        str_nodos="-1"
        alimentadores_nodos = [list(fila) for fila in alimentadores]
        for fila in alimentadores_nodos:
            fila.append('-1')
        for n in range(self.amnodos.GetLength(0)):
            #----------------------------------------------------------------------------
            progress.setValue(80 + int(5/self.amnodos.GetLength(0)))
            if progress.wasCanceled():
                return
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            if self.amnodos.GetValue(n,46)==0:
                str_nodos=str_nodos + "," + str(self.amnodos.GetValue(n,1))
            elif self.amnodos.GetValue(n,40) != self.amnodos.GetValue(n,46):
                #en la posicion a de alimentadores pongo el nodo
                for i in range(len(alimentadores_nodos)):
                    if alimentadores_nodos[i][0] == self.amnodos.GetValue(n,46):
                        alimentadores_nodos[i][3] = alimentadores_nodos[i][3] + ',' + str(self.amnodos.GetValue(n,1))
                        break
        str_lineas="-1"
        alimentadores_lineas = [list(fila) for fila in alimentadores]
        for fila in alimentadores_lineas:
            fila.append('-1')
        for l in range(self.amlineas.GetLength(0)):
            #----------------------------------------------------------------------------
            progress.setValue(85 + int(5/self.amlineas.GetLength(0)))
            if progress.wasCanceled():
                return
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            if self.amlineas.GetValue(l,13)==0:
                str_lineas=str_lineas + "," + str(self.amlineas.GetValue(l,1))
            elif self.amlineas.GetValue(l,8) != self.amlineas.GetValue(l,13):
                #en la posicion a de alimentadores pongo el nodo
                for i in range(len(alimentadores_lineas)):
                    if alimentadores[i][0] == self.amlineas.GetValue(l,13):
                        alimentadores_lineas[i][3] = alimentadores_lineas[i][3] + ',' + str(self.amlineas.GetValue(l,1))
                        break
        #----------------------------------------------------------------------------
        progress.setValue(90)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        for i in range(len(alimentadores_nodos)):
            id_alimentador=alimentadores_nodos[i][0]
            alimentador=alimentadores_nodos[i][1]
            tension=alimentadores_nodos[i][2]
            cursor = self.conn.cursor()
            try:
                cursor.execute("UPDATE mNodos SET alim=" + str(id_alimentador) + " WHERE tension=" + str(tension) + " AND geoname IN (" + alimentadores_nodos[i][3] + ")")
                cursor.execute("UPDATE Nodos SET Alimentador='" + alimentador + "' WHERE tension=" + str(tension) + " AND geoname IN (" + alimentadores_nodos[i][3] + ")")
                self.conn.commit()
            except:
                self.conn.rollback()
        for i in range(len(alimentadores_lineas)):
            id_alimentador=alimentadores_nodos[i][0]
            alimentador=alimentadores_nodos[i][1]
            tension=alimentadores_nodos[i][2]
            cursor = self.conn.cursor()
            try:
                cursor.execute("UPDATE mLineas SET alim=" + str(id_alimentador) + " WHERE tension=" + str(tension) + " AND geoname IN (" + alimentadores_lineas[i][3] + ")")
                cursor.execute("UPDATE Lineas SET Alimentador='" + alimentador + "' WHERE tension=" + str(tension) + " AND geoname IN (" + alimentadores_lineas[i][3] + ")")
                self.conn.commit()
            except:
                self.conn.rollback()
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE Nodos SET Alimentador='#NA' WHERE geoname IN (" + str_nodos + ")")
            cursor.execute("UPDATE Lineas SET Alimentador='#NA' WHERE geoname IN (" + str_lineas + ")")
            cursor.execute("UPDATE Nodos SET Alimentador='#NA' WHERE Alimentador IS NULL")
            cursor.execute("UPDATE Lineas SET Alimentador='#NA' WHERE Alimentador IS NULL")
            self.conn.commit()
        except:
            self.conn.rollback()
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Lineas':
                lyr.triggerRepaint()
        #----------------------------------------------------------------------------
        progress.setValue(100)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        QMessageBox.information(None, 'EnerGis 5', "Alimentadores Actualizados")

    def transformadores_almacen(self):
        from .frm_trafos_almacen import frmTrafosAlmacen
        self.dialogo = frmTrafosAlmacen(self.tipo_usuario, self.conn)
        self.dialogo.show()

    def centros_transformacion(self):
        from .frm_trafos_almacen import frmTrafosAlmacen
        self.dialogo = frmTrafosAlmacen(self.tipo_usuario, self.conn)
        self.dialogo.show()

    def importar_access(self):
        dialog = QFileDialog()
        oFileName = dialog.getOpenFileName(None, "Archivo de EnerGis 4", "", "EnerGis files (*.uen)")
        database_path=oFileName[0]
        # Ruta a tu archivo de base de datos Access
        if not database_path:
            return
        reply = QMessageBox.question(None, 'EnerGis', 'Se borrarán todos los datos del modelo actual, desea continuar ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        from .mod_importacion import importar_access
        importar_access(self, self.conn, database_path)

    def res_811(self):
        from .mod_exportacion import exportar_811
        exportar_811(self, self.conn, self.srid)

    def exportar_usuarios_oceba(self):
        from .mod_exportacion import exportar_usuarios
        exportar_usuarios(self, self.conn, self.srid)

    def cts_oceba(self):
        from .mod_exportacion import exportar_cts
        exportar_cts(self, self.conn, self.srid)

    def cadena1(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        from .mod_exportacion import exportar_cadena1
        exportar_cadena1(self, self.conn, self.tipo_navegacion)

    def cadena2(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        from .mod_exportacion import exportar_cadena2
        exportar_cadena2(self, self.conn, self.tipo_navegacion)

    def exportar_qfield(self):
        if os.path.isdir('c:/gis/energis5/QField/')==False:
            os.mkdir('c:/gis/energis5/QField/')
        #project = QgsProject.instance()
        #project.write("c:/gis/energis5/QField/" + self.nombre_modelo + ".gpkg")
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            #lyr.crs()
            if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos Proyectos':
                filtro_original = lyr.subsetString()
                new_filter = filtro_original + ' and "estado"!=\'0\' and "estado"!=\'6\''
                lyr.setSubsetString(new_filter)
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/QField/" + lyr.name() + ".gpkg", "utf-8", QgsCoordinateReferenceSystem(4326), "GPKG")
                lyr.setSubsetString(filtro_original)
                #Creo la capa Suministros
                duplicate_layer = QgsVectorLayer(lyr.source(), lyr.name().replace("Nodos","Suministros"), lyr.providerType())
                # Obtener los parámetros del proveedor de datos
                provider_params = duplicate_layer.dataProvider().dataSourceUri()
                provider_params = provider_params.replace('mapNodos','mapSuministros')
                duplicate_layer.setDataSource(provider_params, duplicate_layer.name(), "mssql")
                provider_params = duplicate_layer.dataProvider().dataSourceUri()
                #QgsProject.instance().addMapLayer(duplicate_layer)
                QgsVectorFileWriter.writeAsVectorFormat(duplicate_layer, "c:/gis/energis5/QField/" + duplicate_layer.name() + ".gpkg", "utf-8", QgsCoordinateReferenceSystem(4326), "GPKG")
                #QgsProject.instance().removeMapLayer(duplicate_layer.id())
            if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/QField/" + lyr.name() + ".gpkg", "utf-8", QgsCoordinateReferenceSystem(4326), "GPKG")
            if lyr.name()[:6] == 'Postes' and lyr.name()!='Postes Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/QField/" + lyr.name() + ".gpkg", "utf-8", QgsCoordinateReferenceSystem(4326), "GPKG")
        QMessageBox.information(None, 'EnerGis 5', "Exportado")

    def exportar_mapinfo(self):
        if os.path.isdir('c:/gis/energis5/MapInfo/')==False:
            os.mkdir('c:/gis/energis5/MapInfo/')

        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/MapInfo/" + lyr.name() + ".tab", "utf-8", QgsCoordinateReferenceSystem(4326), "MapInfo File")
            if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/MapInfo/" + lyr.name() + ".tab", "utf-8", QgsCoordinateReferenceSystem(4326), "MapInfo File")
            if lyr.name()[:6] == 'Postes' and lyr.name()!='Postes Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/MapInfo/" + lyr.name() + ".tab", "utf-8", QgsCoordinateReferenceSystem(4326), "MapInfo File")
        QMessageBox.information(None, 'EnerGis 5', "Exportado")

    def exportar_esri(self):
        if os.path.isdir('c:/gis/energis5/ESRI/')==False:
            os.mkdir('c:/gis/energis5/ESRI/')
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/ESRI/" + lyr.name() + ".shp", "utf-8", QgsCoordinateReferenceSystem(4326), "ESRI Shapefile")
            if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/ESRI/" + lyr.name() + ".shp", "utf-8", QgsCoordinateReferenceSystem(4326), "ESRI Shapefile")
            if lyr.name()[:6] == 'Postes' and lyr.name()!='Postes Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/ESRI/" + lyr.name() + ".shp", "utf-8", QgsCoordinateReferenceSystem(4326), "ESRI Shapefile")
        QMessageBox.information(None, 'EnerGis 5', "Exportado")

    def exportar_kml(self):
        str_nodos = '0'
        str_lineas = '0'
        str_postes = '0'
        ftrs_nodos=[]
        ftrs_lineas=[]
        ftrs_postes=[]
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Proyecto':
                for ftr in lyr.selectedFeatures():
                    ftrs_nodos.append(ftr)
                    str_nodos = str_nodos + ',' + str(ftr.id())
            if lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Proyecto':
                for ftr in lyr.selectedFeatures():
                    ftrs_lineas.append(ftr)
                    str_lineas = str_lineas + ',' + str(ftr.id())
            if lyr.name()[:6] == 'Postes' and lyr.name() != 'Postes_Proyecto':
                for ftr in lyr.selectedFeatures():
                    ftrs_postes.append(ftr)
                    str_postes = str_postes + ',' + str(ftr.id())
        from .frm_exportar_kml import frmExportarKml
        self.dialogo = frmExportarKml(self.conn, self.srid, str_nodos, str_lineas, str_postes, ftrs_nodos, ftrs_lineas, ftrs_postes)
        self.dialogo.show()

    def exportar_demitec(self):
        from .mod_exportacion import exportar_demitec
        exportar_demitec(self, self.conn, self.srid, self.nombre_modelo)

    def exportar_dpe(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        from .mod_exportacion import exportar_gis_dpe
        exportar_gis_dpe(self, self.conn, self.srid)

    def exportar_google(self):
        from .mod_exportacion import exportar_google
        exportar_google(self, self.mapCanvas, self.conn, self.srid, self.nombre_modelo)

    def exportar_txt(self):
        from .mod_exportacion import exportar_txt
        exportar_txt(self, self.mapCanvas, self.conn, self.srid, self.nombre_modelo)

    def exportar_tab(self):
        if os.path.isdir('c:/gis/energis5/MapInfo/')==False:
            os.mkdir('c:/gis/energis5/MapInfo/')
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                #QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/MapInfo/" + self.nombre_modelo.lower() + lyr.name().replace('Nodos ','_no_') + ".tab", "", lyr.crs(), "MapInfo File", symbologyExport=QgsVectorFileWriter.FeatureSymbology)
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/MapInfo/" + self.nombre_modelo + ' ' + lyr.name() + ".tab", "", lyr.crs(), "MapInfo File")
            if lyr.name()[:6] == 'Lineas':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/MapInfo/" + self.nombre_modelo + ' ' + lyr.name() + ".tab", "", lyr.crs(), "MapInfo File")
            if lyr.name()[:6] == 'Postes':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/MapInfo/" + self.nombre_modelo + ' ' + lyr.name() + ".tab", "", lyr.crs(), "MapInfo File")
        QMessageBox.information(None, 'EnerGis 5', "Exportado")

    def h_verificar_red(self):
        if self.tipo_navegacion==0:
            from .mod_navegacion_ant import nodos_por_salida
            from .mod_navegacion_ant import nodos_por_transformador
        else:
            import clr
            from System import Int64
        self.conectar_db()
        self.red_verificada=False
        #----------------------------------------------------------------------------
        progress = QProgressDialog("Procesando...", "Cancelar", 0, 100)
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE A SET d1=o1, d2=o2 FROM (SELECT Nodos.Val1 AS d1, CTs.potencia AS o1, Nodos.Val2 AS d2, CTs.conexionado AS o2 FROM Nodos INNER JOIN (SELECT Ct.Id_ct, SUM(Transformadores.Potencia) AS potencia, MIN(Transformadores.Conexionado) AS conexionado FROM Ct INNER JOIN Transformadores ON Ct.Id_ct = Transformadores.Id_ct GROUP BY Ct.Id_ct) AS CTs ON Nodos.Nombre = CTs.Id_ct WHERE (Nodos.Elmt = 4))A WHERE d1<>o1 OR d2=o2")
            self.conn.commit()
        except:
            self.conn.rollback()
        #Verificar Red
        str_sql= "SELECT DISTINCT 'Lineas' AS Elemento,'lineas con iguales nodo desde/hasta' AS Problema,Max(A.Geoname) AS Geoname,'Linea' AS Nombre FROM (SELECT Geoname,Desde,Hasta FROM Lineas WHERE Lineas.Tension>0 UNION SELECT Geoname,Hasta,Desde FROM Lineas WHERE Lineas.Tension>0) AS A GROUP BY A.Desde, A.Hasta HAVING Count(A.Geoname)>1"
        str_sql= str_sql + " UNION SELECT 'Lineas' AS Elemento,'lineas con longitud menor a cero' AS Problema,Geoname,'Linea' AS Nombre FROM Lineas WHERE Lineas.Tension>0 AND Lineas.Tension>0 AND Longitud<=0"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores sin nombre' AS Problema,Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND (Elmt = 2 OR Elmt = 3) AND ((Nombre) Is null OR Nombre = '')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores con nombre repetido' AS Problema, MIN(Geoname) AS Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND Nodos.Tension>0 AND (Elmt = 2 OR Elmt = 3) GROUP BY Nombre HAVING Count(Nodos.Nombre)>1"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'CTs con nombre repetido' AS Problema, MIN(Geoname) AS Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND Elmt = 4 GROUP BY Nombre HAVING Count(Nodos.Geoname)>1"
        #str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'salida de alimentador con nombre repetido' AS Problema, MIN(Geoname) AS Geoname, Val1 FROM Nodos WHERE Nodos.Tension>0 AND Nodos.Tension>0 AND Elmt = 8 GROUP BY Val1 HAVING Count(Nodos.Geoname)>1"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'salidas de alimentador sin código de alimentador' AS Problema,Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND Elmt = 8 AND ((Val1) Is null OR Val1 = '')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'fuentes con errores de tensión' AS Problema,Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND Elmt = 1 AND Val1 IS NULL"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'fuentes con mas de una línea' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND Nodos.estado=1 AND cant_lineas>1"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores con mas de dos líneas' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND (Nodos.estado=2 OR Nodos.estado=3) AND cant_lineas>2"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'CTs con mas de dos líneas' AS Problema,Nodos.Geoname, Nodos.Nombre as Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND Nodos.estado=4 AND cant_lineas>2"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'CTs con usuarios y sin máquina' AS Problema,Nodos.Geoname, Nodos.Nombre FROM (Nodos INNER JOIN ((Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s) ON Nodos.Geoname = Suministros_Trafos.Geoname_t) LEFT JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct WHERE Nodos.Tension>0 AND Nodos.elmt = 4 AND Usuarios.[ES] = 1 AND Transformadores.Id_trafo IS NULL GROUP BY Nodos.Geoname, Nodos.Nombre HAVING Count(Usuarios.id_usuario)>0"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'transformadores con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Transformadores INNER JOIN Nodos ON Transformadores.Id_ct = Nodos.Nombre INNER JOIN mNodos ON Nodos.Geoname = mNodos.Geoname WHERE ((mNodos.fases IN (1,2,3) AND Transformadores.Conexionado <> 'M') OR (mNodos.fases IN ('12','23','13') AND Transformadores.Conexionado NOT IN ('M','B'))) AND Nodos.Elmt=4 GROUP BY nodos.Geoname, nodos.Nombre"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'usuarios con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo WHERE Nodos.Tension>0 AND Usuarios.fase='123' GROUP BY nodos.Geoname, nodos.Nombre HAVING MIN(fase) IN ('1','2','3','12','23','13')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'nodos con inconsistencias de tarifas' AS Problema,A.Geoname, A.Nombre FROM (SELECT Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro GROUP BY Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension) AS A GROUP BY A.Geoname, A.Nombre HAVING Count(A.Nivel_Tension)>1"
        str_sql= str_sql + " UNION SELECT DISTINCT 'Nodos' AS Elemento,'nodos con inconsistencias de tarifas' AS Problema,Nodos.Geoname, Usuarios.tarifa AS Nombre FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE (((Nodos.Tension)>1000) AND ((Tarifas.Nivel_Tension)='BT')) OR (((Nodos.Tension)<1000) AND ((Tarifas.Nivel_Tension)='MT'))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'usuarios con tarifas erroneas' AS Problema,Nodos.Geoname, CAST(Usuarios.id_usuario AS varchar) + '->'+ Usuarios.Tarifa AS Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo WHERE Nodos.Tension>0 AND (((Usuarios.[ES])=1) AND ((Usuarios.tarifa) IS NULL)) OR (((Usuarios.tarifa) Not In (SELECT tarifa FROM tarifas)))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'alimentadores sin nombre' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos WHERE Nodos.Tension>0 AND Elmt = 8 AND (Val1='' OR Val1 IS NULL)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'cambios de tension sin trafos' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta WHERE (Nodos.Tension>0 AND Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Tension>0 AND Nodos.Elmt=5 AND Lineas.Tension>0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'cambios de tension sin trafos' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE (Nodos.Tension>0 AND Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Tension>0 AND Nodos.Elmt=5 AND Lineas.Tension>0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'nodos con inconsistencia de fases' AS Problema,nodos.geoname, Nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta INNER JOIN mNodos ON Nodos.Geoname = mNodos.geoname WHERE Nodos.Tension>0 AND (LEN(mNodos.fases)<>LEN(Lineas.Fase) AND mNodos.fases<>Lineas.Fase AND mNodos.fases<>123 AND Lineas.Fase<>123) AND (LEN(mNodos.fases)=2 AND CHARINDEX(Lineas.Fase, mNodos.fases, 0)=0 OR LEN(Lineas.Fase)=2 AND CHARINDEX(CONVERT(VARCHAR,mNodos.Fases), Lineas.fase, 0)=0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'nodos con inconsistencia de fases' AS Problema,nodos.geoname, Nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta INNER JOIN mNodos ON Nodos.Geoname = mNodos.geoname WHERE Nodos.Tension>0 AND (LEN(mNodos.fases)<>LEN(Lineas.Fase) AND mNodos.fases<>Lineas.Fase AND mNodos.fases<>123 AND Lineas.Fase<>123) AND (LEN(mNodos.fases)=2 AND CHARINDEX(Lineas.Fase, mNodos.fases, 0)=0 OR LEN(Lineas.Fase)=2 AND CHARINDEX(CONVERT(VARCHAR,mNodos.Fases), Lineas.fase, 0)=0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores sin tipo' AS Problema, Nodos.geoname, Nodos.Nombre FROM Nodos WHERE Tension>0 AND (elmt=2 OR elmt=3) AND (Val1='' OR Val1 IS NULL)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores con varias fases' AS Problema, A.geoname, A.Nombre  FROM (SELECT Nodos.Geoname, Nodos.Nombre, Lineas.Fase FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE Nodos.elmt IN (2,3) UNION SELECT Nodos.Geoname, Nodos.Nombre, Lineas.Fase FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta WHERE Nodos.elmt IN (2,3)) AS A GROUP BY A.Geoname, A.Nombre HAVING (((Count(A.Fase))>1))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'transformadores con error de tensión' AS Problema, Nodos.geoname, Nodos.Nombre FROM Transformadores INNER JOIN Nodos ON Transformadores.Id_ct = Nodos.Nombre WHERE (((Transformadores.[Tension_1]) Not In (132000,66000,33000,19000,13200,7620,6600,400,231)) AND ((Nodos.Elmt)=4)) OR (((Transformadores.[Tension_2]) Not In (132000,66000,33000,19000,13200,7620,6600,400,231)) AND ((Nodos.Elmt)=4))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'transformadores con error de conexionado' AS Problema, Nodos.geoname, Nodos.Nombre FROM Nodos INNER JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct WHERE (Transformadores.Conexionado IN ('Yy0', 'Yd5', 'Yd11', 'Dy5', 'Dy11')) AND (Transformadores.Tipo <> 3) AND (Nodos.Elmt = 4) AND (Nodos.Tension > 0) OR (Transformadores.Conexionado = 'B') AND (Transformadores.Tipo <> 2) AND (Nodos.Elmt = 4) AND (Nodos.Tension > 0) OR (Transformadores.Conexionado = 'M') AND (Transformadores.Tipo <> 1) AND (Nodos.Elmt = 4) AND (Nodos.Tension > 0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'transformadores con error de fases' AS Problema, Nodos.geoname, Nodos.Nombre FROM (SELECT ct.id_ct, count(id) as cant FROM ct inner join transformadores on ct.id_ct=transformadores.id_ct group by ct.id_ct)  AS C INNER JOIN (((SELECT Nodos.Geoname, Lineas.Fase FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE Nodos.elmt=4 UNION SELECT Nodos.Geoname, Lineas.Fase FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta WHERE Nodos.elmt =4)  AS A INNER JOIN Nodos ON A.Geoname = Nodos.Geoname) INNER JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct) ON C.id_ct = Transformadores.Id_ct WHERE (((A.Fase)<>'123') AND ((Transformadores.Tipo)=3)) OR (((A.Fase)='123') AND ((Transformadores.Tipo)=2)) OR (((A.Fase) Not In ('1','2','3')) AND ((Transformadores.Tipo)=1) AND ((C.cant)=1))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'fecha de alta de ct faltante' AS Problema, Nodos.geoname, Nodos.Nombre FROM Nodos INNER JOIN Ct ON Nodos.Nombre=Ct.id_ct WHERE elmt=4 AND Fecha_Alta IS NULL"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'estado de ct inconsistente' AS Problema, Nodos.geoname, Nodos.Nombre FROM Nodos INNER JOIN Ct ON Nodos.Nombre=Ct.id_ct WHERE elmt=4 AND Conservacion IS NULL"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'cts sin salidas' AS Problema, Nodos.geoname, Nodos.Nombre FROM Suministros_Trafos INNER JOIN (Nodos INNER JOIN Ct ON Nodos.Nombre = Ct.id_ct) ON Suministros_Trafos.Geoname_t = Nodos.Geoname WHERE (((Nodos.[elmt])=4) AND (([casis]+[casies]+[cases]+[casees])=0))"
        str_sql= str_sql + " UNION SELECT 'Lineas' AS Elemento,'estados de lineas' AS Problema, Lineas.geoname, '' AS Nombre FROM Lineas WHERE Tension>0 AND Conservacion IS NULL"
        str_sql= str_sql + " UNION SELECT 'Lineas' AS Elemento,'longitud de lineas' AS Problema, Lineas.geoname, '' AS Nombre FROM Lineas WHERE Tension>0 AND Longitud=0 OR Longitud IS NULL"
        str_sql= str_sql + " UNION SELECT 'Lineas' AS Elemento,'linea sin unidad constructiva' AS Problema, Lineas.geoname, '' AS Nombre FROM Lineas WHERE Tension>0 AND (UUCC IS NULL OR UUCC='' OR UUCC='SD')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'nodo sin unidad constructiva' AS Problema, Nodos.geoname, Nodos.Nombre FROM Nodos WHERE Tension>0 AND elmt IN (2, 3, 4, 7, 9) AND (UUCC IS NULL OR UUCC='' OR UUCC='SD')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'usuario prosumidor sin datos' AS Problema, Suministros.id_nodo AS geoname, Usuarios.nombre FROM Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro WHERE LEN(Prosumidor)<21 AND LEN(Prosumidor)>1"
        cursor = self.conn.cursor()
        cursor.execute(str_sql)
        elementos = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()
        if len(elementos)!=0:
            from .frm_lista import frmLista
            self.dialogo = frmLista(self.iface.mapCanvas(), encabezado, elementos)
            self.dialogo.setWindowTitle('Resultados Verificación : ' + str(len(elementos)) + ' errores')
            self.dialogo.show()
            return
        #----------------------------------------------------------------------------
        progress.setValue(20)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        self.descargo_red()
        #----------------------------------------------------------------------------
        progress.setValue(30)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM Alimentadores WHERE Id_Alim NOT IN (SELECT Val1 FROM Nodos WHERE Nodos.Tension>0 AND elmt=8)")
            cursor.execute("INSERT INTO Alimentadores (Id, Id_Alim,Tension,Cd,SSEE) SELECT DISTINCT Aux, LEFT(Val1,15) AS Id_Alim, Tension,'0' AS Cd,'0' AS SSEE FROM Nodos WHERE Nodos.Tension>0 AND elmt=8 AND LEFT(Val1,15) NOT IN (SELECT Id_Alim FROM Alimentadores)")
            cursor.execute("UPDATE Alimentadores SET ssee='0' WHERE ssee IS NULL")
            cursor.execute("UPDATE Alimentadores SET cd='0' WHERE cd IS NULL")
            cursor.commit()
        except:
            cursor.rollback()
            QMessageBox.warning(None, 'EnerGis 5', "No se pudieron crear Alimentadores !")
        #----------------------------------------------------------------------------
        progress.setValue(40)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        if self.tipo_navegacion==0:
            nodos_por_transformador(self, self.conn)
            nodos_por_salida(self, self.conn)
            self.red_verificada=True
        else:
            cursor = self.conn.cursor()
            cursor.execute("SELECT aux, geoname FROM mNodos WHERE estado=1")
            fuentes = cursor.fetchall()
            cursor.close()
            #----------------------------------------------------------------------------
            # Cargar el ensamblado
            clr.AddReference(os.path.join(basepath, 'NavRed7.dll'))
            from EnerGis5.NavRed7 import NavRed

            # Instanciar la clase NavRed
            navred_instance = NavRed()
            for fuente in fuentes:
                #----------------------------------------------------------------------------
                progress.setValue(40 + int(59/len(fuentes)))
                QApplication.processEvents()
                if progress.wasCanceled():
                    return
                #----------------------------------------------------------------------------
                # Preparar los valores de entrada
                fuentenavegada = Int64(fuente[0])
                # Llamar a la función
                resultado = navred_instance.Navegar_compilar_red(self.monodos,self.amnodos,self.amlineas,fuentenavegada)
                if resultado[0]!="Ok":
                    QMessageBox.critical(None, 'EnerGis 5', resultado[0])
                    #----------------------------------------------------------------------------
                    progress.setValue(100)
                    #----------------------------------------------------------------------------
                    return
            self.red_verificada=True
            trafos_nodos=['-1']*self.amnodos.GetLength(0)
            trafos_lineas=['-1']*self.amlineas.GetLength(0)
            trafos_suministros=['-1']*self.amnodos.GetLength(0)

            for n in range(self.amnodos.GetLength(0)):
                if self.amnodos.GetValue(n,44)!=0:
                    trafos_nodos[self.amnodos.GetValue(n,44)]=trafos_nodos[self.amnodos.GetValue(n,44)] + ',' + str(self.amnodos.GetValue(n,1))
                    if self.amnodos.GetValue(n,2)==6:
                        trafos_suministros[self.amnodos.GetValue(n,44)]=trafos_suministros[self.amnodos.GetValue(n,44)] + ',' + str(self.amnodos.GetValue(n,1))

            for n in range(self.amlineas.GetLength(0)):
                if self.amlineas.GetValue(n,11)!=0:
                    try:
                        trafos_lineas[self.amlineas.GetValue(n,11)]=trafos_lineas[self.amlineas.GetValue(n,11)] + ',' + str(self.amlineas.GetValue(n,1))
                    except:
                        pass

            try:
                cursor = self.conn.cursor()
                cursor.execute("TRUNCATE TABLE Suministros_Trafos")
                cursor.execute("TRUNCATE TABLE Nodos_Transformador")
                cursor.execute("TRUNCATE TABLE Lineas_Transformador")
                self.conn.commit()
            except:
                QMessageBox.critical(None, 'EnerGis 5', 'No se pueden borrar las tablas de elementos de Trafos')
                self.conn.rollback()

            cursor = self.conn.cursor()
            cursor.fast_executemany = True

            datos_s = []
            for t in range(len(trafos_suministros)):
                # Separamos por coma y limpiamos espacios
                ids_separados = trafos_suministros[t].split(',')
                for id_individual in ids_separados:
                    # Filtramos los '-1' o valores vacíos
                    if id_individual != '-1' and id_individual != '':
                        try:
                            # Ahora sí, convertimos cada uno a entero
                            val_s = int(id_individual)
                            val_t = int(self.amnodos.GetValue(t, 1))
                            datos_s.append((val_s, val_t))
                        except:
                            pass

            datos_n = []
            for t in range(len(trafos_nodos)):
                # Separamos por coma y limpiamos espacios
                ids_separados = trafos_nodos[t].split(',')
                for id_individual in ids_separados:
                    # Filtramos los '-1' o valores vacíos
                    if id_individual != '-1' and id_individual != '':
                        try:
                            # Ahora sí, convertimos cada uno a entero
                            val_n = int(id_individual)
                            val_id = int(self.amnodos.GetValue(t, 1))
                            datos_n.append((val_n, val_id))
                        except:
                            pass

            datos_l = []
            for t in range(len(trafos_lineas)):
                # Separamos por coma y limpiamos espacios
                ids_separados = trafos_lineas[t].split(',')
                for id_individual in ids_separados:
                    # Filtramos los '-1' o valores vacíos
                    if id_individual != '-1' and id_individual != '':
                        try:
                            # Ahora sí, convertimos cada uno a entero
                            val_l = int(id_individual)
                            val_id = int(self.amnodos.GetValue(t, 1))
                            datos_l.append((val_l, val_id))
                        except:
                            pass
            #Definición de tareas para iterar y no repetir código
            tareas = [
                ("INSERT INTO Suministros_Trafos (geoname_s, geoname_t) VALUES (?, ?)", datos_s, "Suministros"),
                ("INSERT INTO Nodos_Transformador (geoname, id) VALUES (?, ?)", datos_n, "Nodos"),
                ("INSERT INTO Lineas_Transformador (geoname, id) VALUES (?, ?)", datos_l, "Lineas")
            ]

            # Ejecución controlada
            for query, datos, nombre in tareas:
                if datos: # Solo ejecutamos si hay datos
                    try:
                        cursor.executemany(query, datos)
                        self.conn.commit()
                    except Exception as e:
                        self.conn.rollback()
                        QMessageBox.critical(None, 'EnerGis 5', f"Error cargando {nombre}: {str(e)}")

            """for n in range(len(trafos_suministros)):
                if trafos_suministros[n]!='-1':
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute("INSERT INTO Suministros_Trafos SELECT geoname, " + str(self.amnodos.GetValue(n,1)) + " FROM Nodos WHERE Tension>0 AND geoname IN (" + str(trafos_suministros[n]) + ")")
                        self.conn.commit()
                    except:
                        QMessageBox.critical(None, 'EnerGis 5', 'No se puede insertar en la tabla Suministros_Trafos')
                        self.conn.rollback()

            for n in range(len(trafos_nodos)):
                if trafos_nodos[n]!='-1':
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute("INSERT INTO Nodos_Transformador SELECT geoname, " + str(self.amnodos.GetValue(n,1)) + " FROM Nodos WHERE Tension>0 AND geoname IN (" + str(trafos_nodos[n]) + ")")
                        self.conn.commit()
                    except:
                        QMessageBox.critical(None, 'EnerGis 5', 'No se puede insertar en la tabla Nodos_Transformador')
                        self.conn.rollback()

            for n in range(len(trafos_lineas)):
                if trafos_lineas[n]!='-1':
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute("INSERT INTO Lineas_Transformador SELECT geoname, " + str(self.amlineas.GetValue(n,1)) + " FROM Lineas WHERE Tension>0 AND geoname IN (" + str(trafos_lineas[n]) + ")")
                        self.conn.commit()
                    except:
                        QMessageBox.critical(None, 'EnerGis 5', 'No se puede insertar en la tabla Lineas_Transformador')
                        self.conn.rollback()
            """

        #----------------------------------------------------------------------------
        progress.setValue(100)
        #----------------------------------------------------------------------------
        QMessageBox.information(None, 'EnerGis 5', "Red Verificada !")

    def descargo_red(self):
        if self.tipo_navegacion==0:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
            #convierto el cursor en array
            self.mnodos = tuple(cursor)
            cursor.close()
            listanodos = [list(nodo) for nodo in self.mnodos]
            jnodos = json.dumps(listanodos)
            with open(os.path.join(tempfile.gettempdir(), "jnodos"), "w") as a:
                a.write(jnodos)
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
            #convierto el cursor en array
            self.mlineas = tuple(cursor)
            cursor.close()
            listalineas = [list(linea) for linea in self.mlineas]
            jlineas = json.dumps(listalineas)
            with open(os.path.join(tempfile.gettempdir(), "jlineas"), "w") as a:
                a.write(jlineas)
        else:
            import clr
            clr.AddReference("mscorlib")
            clr.AddReference("System")
            from System import Int64, Array
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
            #convierto el cursor en array
            self.mnodos = tuple(cursor)
            cursor.close()
            listanodos = [list(nodo) for nodo in self.mnodos]
            jnodos = json.dumps(listanodos)
            with open(os.path.join(tempfile.gettempdir(), "jnodos"), "w") as a:
                a.write(jnodos)
            #----------------------------------------------------------------------------
            cursor = self.conn.cursor()
            try:
                cursor.execute("UPDATE mLineas SET alim=0 WHERE alim IS NULL")
                self.conn.commit()
            except:
                self.conn.rollback()
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
            #convierto el cursor en array
            self.mlineas = tuple(cursor)
            cursor.close()
            listalineas = [list(linea) for linea in self.mlineas]
            jlineas = json.dumps(listalineas)
            with open(os.path.join(tempfile.gettempdir(), "jlineas"), "w") as a:
                a.write(jlineas)
            #----------------------------------------------------------------------------
            # Crear arreglos
            self.monodos = Array.CreateInstance(Int64, len(self.mnodos))
            if len(self.mnodos)>0:
                self.amnodos = Array.CreateInstance(Int64, len(self.mnodos), len(self.mnodos[0]))
            else:
                self.amnodos = Array.CreateInstance(Int64, 0, 44)
            if len(self.mlineas)>0:
                self.amlineas = Array.CreateInstance(Int64, len(self.mlineas), len(self.mlineas[0]))
            else:
                self.amlineas = Array.CreateInstance(Int64, 0, 12)
            # Copiar valores a mnodos
            for i in range(len(self.mnodos)):
                for j in range(len(self.mnodos[0])):
                    self.amnodos[i, j] = self.mnodos[i][j]
            # Copiar valores a mlineas
            for i in range(len(self.mlineas)):
                for j in range(len(self.mlineas[0])):
                    self.amlineas[i, j] = self.mlineas[i][j]

    def h_elementos_seleccionados(self):
        from .frm_seleccion import frmSeleccion
        self.dialogo = frmSeleccion(self.iface.mapCanvas())
        self.dialogo.show()

    def h_navegar_a_la_fuente(self):
        ftrs = []
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                for ftr in lyr.selectedFeatures():
                    ftrs.append(ftr)
        if len(ftrs) != 1:
            QMessageBox.information(None, 'EnerGis 5', 'Debe seleccionar un nodo')
            return
        id = ftrs[0].id()
        if self.tipo_navegacion==0:
            from .herr_navegar_fuente_ant import herrNavegarFuente
            herrNavegarFuente(self.iface.mapCanvas(), self.conn, id)
        else:
            self.descargo_red()
            from .herr_navegar_fuente import herrNavegarFuente
            herrNavegarFuente(self.iface.mapCanvas(), id, self.amnodos, self.amlineas)

    def h_navegar_extremos(self):
        ftrs = []
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                #QMessageBox.information(None, 'EnerGis 5', str(lyr.name()))
                for ftr in lyr.selectedFeatures():
                    #QMessageBox.information(None, 'EnerGis 5', str(ftr.id()))
                    ftrs.append(ftr)
        if len(ftrs) != 1:
            QMessageBox.warning(None, 'EnerGis 5', 'Debe seleccionar un nodo')
            return
        id=ftrs[0].id()
        if self.tipo_navegacion==0:
            from .herr_navegar_extremos_ant import herrNavegarExtremos
            herrNavegarExtremos(self.iface.mapCanvas(), self.conn, id)
        else:
            self.descargo_red()
            from .herr_navegar_extremos import herrNavegarExtremos
            herrNavegarExtremos(self.iface.mapCanvas(), id, self.amnodos, self.amlineas)

    def h_desconectados(self):
        if self.tipo_navegacion==0:
            from .herr_desconectados import herrDesconectados
            herrDesconectados(self.iface.mapCanvas(), self.conn)
        else:
            self.descargo_red()
            import clr
            from System import Int64
            #----------------------------------------------------------------------------
            progress = QProgressDialog("Procesando...", "Cancelar", 0, 100)
            progress.setWindowTitle("Progreso")
            progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
            progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
            progress.setValue(0)  # Inicia el progreso en 0
            #----------------------------------------------------------------------------
            progress.setValue(10)
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            cursor = self.conn.cursor()
            cursor.execute("SELECT aux, geoname FROM mNodos WHERE estado=1")
            fuentes = cursor.fetchall()
            cursor.close()
            #----------------------------------------------------------------------------
            # Cargar el ensamblado
            clr.AddReference(os.path.join(basepath, 'NavRed7.dll'))
            from EnerGis5.NavRed7 import NavRed
            #----------------------------------------------------------------------------
            progress.setValue(55)
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            # Instanciar la clase NavRed
            navred_instance = NavRed()
            for fuente in fuentes:
                #----------------------------------------------------------------------------
                progress.setValue(10 + int(80/len(fuentes)))
                if progress.wasCanceled():
                    return
                QApplication.processEvents()
                #----------------------------------------------------------------------------
                # Preparar los valores de entrada
                fuentenavegada = Int64(fuente[0])
                # Llamar a la función
                resultado = navred_instance.Navegar_compilar_red(self.monodos,self.amnodos,self.amlineas,fuentenavegada)
                if resultado[0]!="Ok":
                    QMessageBox.critical(None, 'EnerGis 5', resultado[0])
                    #----------------------------------------------------------------------------
                    progress.setValue(100)
                    #----------------------------------------------------------------------------
                    return
            #----------------------------------------------------------------------------
            progress.setValue(90)
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            self.seleccion_n = [[]]
            self.seleccion_l = [[]]
            n = self.iface.mapCanvas().layerCount()
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.type() == QgsMapLayerType.VectorLayer:
                    lyr.removeSelection()
            for n in range(self.amnodos.GetLength(0)):
                if self.amnodos.GetValue(n,3) == 0 and self.amnodos.GetValue(n,1) != 0:
                    self.seleccion_n.append([self.amnodos.GetValue(n,1),self.amnodos.GetValue(n,38),self.amnodos.GetValue(n,2)])
            for l in range(self.amlineas.GetLength(0)):
                if self.amlineas.GetValue(l,4) == 0 and self.amlineas.GetValue(l,1) != 0:
                    self.seleccion_l.append([self.amlineas.GetValue(l,1),self.amlineas.GetValue(l,5),self.amlineas.GetValue(l,6)])
            #----------------------------------------------------------------------------
            progress.setValue(100)
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            from .frm_elementos_navegados import frmElementosNavegados
            self.dialogo = frmElementosNavegados(self.mapCanvas, self.seleccion_n, self.seleccion_l)
            self.dialogo.show()

    def h_aislados(self):
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer:
                lyr.removeSelection()
        self.descargo_red()
        self.seleccion_n = []
        for n in range (0, len(self.mnodos)):
            if self.mnodos[n][1]!=0 and self.mnodos[n][4] == 0:
                self.seleccion_n.append(self.mnodos[n][1])
        str_mensaje = 'No hay Nodos Aislados'
        if len(self.seleccion_n)!=0:
            str_mensaje = str(len(self.seleccion_n)) + ' Aislados'
        QMessageBox.information(None, 'EnerGis 5', str_mensaje)

        if len(self.seleccion_n)==0:
            return
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(self.seleccion_n)
        self.h_elementos_seleccionados()

    def h_loops(self):
        if self.tipo_navegacion==0:
            from .mod_navegacion_ant import buscar_loops
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
            #convierto el cursor en array
            self.mnodos = tuple(cursor)
            cursor.close()
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
            #convierto el cursor en array
            self.mlineas = tuple(cursor)
            cursor.close()
            n = self.iface.mapCanvas().layerCount()
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                    lyr.removeSelection()
            #--------------------------------------------
            buscar_loops(self, self.mnodos, self.mlineas)
            #--------------------------------------------
        else:
            from .mod_navegacion import buscar_loops
            n = self.iface.mapCanvas().layerCount()
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.type() == QgsMapLayerType.VectorLayer:
                    lyr.removeSelection()
            #--------------------------------------------
            buscar_loops(self, self.mnodos, self.mlineas)
            #--------------------------------------------
        self.seleccion_n = []
        for n in range(0, len(self.mnodos)):
            if self.mnodos[n][45] == 1:
                self.seleccion_n.append(self.mnodos[n][1])
        self.seleccion_l = []
        for n in range (0, len(self.mlineas)):
            if self.mlineas[n][12] == 1:
                self.seleccion_l.append(self.mlineas[n][1])
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText('Análisis de la Red')
        msg.setInformativeText('Búsqueda de Loops')
        msg.setWindowTitle('EnerGis 5')
        msg.setDetailedText(str(len(self.seleccion_l)) + ' lineas marcadas')
        msg.exec_()
        if len(self.seleccion_l)==0:
            return
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(self.seleccion_n)
            if lyr.name()[:6] == 'Lineas':
                lyr.select(self.seleccion_l)
        self.h_elementos_seleccionados()

    def h_buscar(self):
        from .frm_buscar import frmBuscar
        self.dialogo = frmBuscar(self.iface.mapCanvas(), self.conn)
        self.dialogo.show()

    def h_buscar_direccion(self):
        from .frm_buscar_direccion import frmBuscarDireccion
        self.dialogo = frmBuscarDireccion(self.iface.mapCanvas(), self.conn)
        self.dialogo.show()

    def h_usuarios_nuevos(self):
        self.dock_widget2.setVisible(True)
        self.actualizar_grilla_usuarios()

    def h_electrodependientes(self):
        b_estado=False
        for action in self.actions:
            if str(action.text())=='Usuarios Electrodependientes':
                b_estado = action.isChecked()
        b_existe = False
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyrCRS = lyr.crs().authid()
            if lyr.name() == 'Electrodependientes':
                b_existe = True
                self.electrodependientes = lyr
                if not self.electrodependientes.isEditable():
                    self.electrodependientes.startEditing()
                    for f in lyr.getFeatures():
                        lyr.deleteFeature(f.id())
                    self.electrodependientes.commitChanges()
        if b_estado==True:
            if b_existe == False:
                electrodependientes=[]
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT Usuarios.id_usuario, Usuarios.Nombre, Usuarios.Calle, Usuarios.Altura, Nodos.XCoord, Nodos.YCoord FROM Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE Usuarios.electrodependiente='S'")
                    #convierto el cursor en array
                    electrodependientes = tuple(cursor)
                    cursor.close()
                except:
                    pass
                self.electrodependientes = QgsVectorLayer("Point?crs=" + lyrCRS, "Electrodependientes", "memory")
                self.electrodependientes.renderer().symbol().setOpacity(1)
                self.electrodependientes.renderer().symbol().symbolLayer(0).setShape(QgsSimpleMarkerSymbolLayerBase.CrossFill)
                self.electrodependientes.renderer().symbol().symbolLayer(0).setSize(4)
                self.electrodependientes.renderer().symbol().symbolLayer(0).setColor(QColor("red"))
                prov = self.electrodependientes.dataProvider()
                fields = QgsFields()
                fields.append(QgsField("id_usuario", QVariant.String))
                fields.append(QgsField("nombre", QVariant.String))
                fields.append(QgsField("calle", QVariant.String))
                fields.append(QgsField("altura", QVariant.String))
                prov.addAttributes(fields)
                self.electrodependientes.updateFields()
                features = []
                for eld in electrodependientes:
                    pt =  QgsPoint(eld[4], eld[5])
                    ftr = QgsFeature()
                    ftr.setFields(fields)
                    ftr.setGeometry(pt)
                    ftr.setAttributes([eld[0], eld[1], eld[2], eld[3]])
                    features.append(ftr)
                prov.addFeatures(features)
                self.electrodependientes.updateExtents()
                QgsProject.instance().addMapLayer(self.electrodependientes, False)
                # Obtener el nodo raíz del árbol de capas
                root = QgsProject.instance().layerTreeRoot()
                nodo = QgsLayerTreeLayer(self.electrodependientes)
                nodo.setItemVisibilityChecked(True)
                root.insertChildNode(0, nodo)
                self.electrodependientes.triggerRepaint()
        else:
            try:
                QgsProject.instance().removeMapLayer(self.electrodependientes.id())
            except:
                pass

    def h_reclamos(self):
        b_estado=False
        for action in self.actions:
            if str(action.text())=='Reclamos':
                b_estado = action.isChecked()
        b_existe = False
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyrCRS = lyr.crs().authid()
            if lyr.name() == 'Reclamos':
                b_existe = True
                self.reclamos = lyr
                if not self.reclamos.isEditable():
                    self.reclamos.startEditing()
                    for f in lyr.getFeatures():
                        lyr.deleteFeature(f.id())
                    self.reclamos.commitChanges()
        if b_estado==True:
            if b_existe == False:
                from .frm_elegir_fechas import frmElegirFechas
                dialogo = frmElegirFechas()
                dialogo.exec()
                self.fecha_desde = dialogo.fecha_desde
                self.fecha_hasta = dialogo.fecha_hasta
                dialogo.close()
                str_sql=''
                if self.fecha_desde!=None:
                    str_sql = str_sql + " AND fecha>='" + str(self.fecha_desde)[:19].replace('-','') + "'"
                if self.fecha_hasta!=None:
                    str_sql = str_sql + " AND fecha<='" + str(self.fecha_hasta)[:19].replace('-','') + "'"
                reclamos=[]
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT TOP 2000 id AS Reclamo, CAST(fecha AS DATE) AS Fecha, id_usuario, Usuarios.Nombre, Direccion, XCoord, YCoord FROM Usuarios INNER JOIN VW_GISRECLAMOS ON Usuarios.id_usuario = VW_GISRECLAMOS.usuario INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE XCoord>0 AND YCoord>0" + str_sql )
                    #convierto el cursor en array
                    reclamos = tuple(cursor)
                    cursor.close()
                except:
                    pass
                self.reclamos = QgsVectorLayer("Point?crs=" + lyrCRS, "Reclamos", "memory")
                self.reclamos.renderer().symbol().setOpacity(1)
                self.reclamos.renderer().symbol().symbolLayer(0).setShape(QgsSimpleMarkerSymbolLayerBase.Star)
                self.reclamos.renderer().symbol().symbolLayer(0).setSize(4)
                self.reclamos.renderer().symbol().symbolLayer(0).setColor(QColor("red"))
                prov = self.reclamos.dataProvider()
                fields = QgsFields()
                fields.append(QgsField("id_reclamo", QVariant.Int))
                fields.append(QgsField("fecha", QVariant.Date))
                fields.append(QgsField("id_usuario", QVariant.String))
                fields.append(QgsField("nombre", QVariant.String))
                fields.append(QgsField("direccion", QVariant.String))
                prov.addAttributes(fields)
                self.reclamos.updateFields()
                features = []
                for reclamo in reclamos:
                    pt =  QgsPoint(reclamo[5], reclamo[6])
                    ftr = QgsFeature()
                    ftr.setFields(fields)
                    ftr.setGeometry(pt)
                    ftr.setAttributes([reclamo[0], reclamo[1], reclamo[2], reclamo[3], reclamo[4]])
                    features.append(ftr)
                prov.addFeatures(features)
                self.reclamos.updateExtents()
                QgsProject.instance().addMapLayer(self.reclamos, False)
                # Obtener el nodo raíz del árbol de capas
                root = QgsProject.instance().layerTreeRoot()
                nodo = QgsLayerTreeLayer(self.reclamos)
                nodo.setItemVisibilityChecked(True)
                root.insertChildNode(0, nodo)
                self.reclamos.triggerRepaint()
        else:
            try:
                QgsProject.instance().removeMapLayer(self.reclamos.id())
            except:
                pass

    def h_datos_seleccion(self):
        from .frm_datos_seleccion import frmDatosSeleccion
        self.dialogo = frmDatosSeleccion(self.id_usuario_sistema, self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.dialogo.show()

    def h_seleccion(self):
        #QMessageBox.information(None, 'Navegacion', str(self.tipo_navegacion))
        self.conectar_db()
        if self.tipo_navegacion==0:
            from .herr_seleccion_ant import herrSeleccion
            tool = herrSeleccion(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.iface, self.conn, self.mnodos, self.mlineas, self.tension, self.red_verificada)
        else:
            from .herr_seleccion import herrSeleccion
            tool = herrSeleccion(self.proyecto, self.id_usuario_sistema, self.tipo_usuario, self.iface.mapCanvas(), self.iface, self.conn, self.amnodos, self.amlineas, self.monodos, self.tension, self.red_verificada)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion.png'))
        seleccion_px.setMask(seleccion_px.mask())
        seleccion_cursor = QtGui.QCursor(seleccion_px)
        self.iface.mapCanvas().setCursor(seleccion_cursor)

    def h_seleccionar_ejes(self):
        from .herr_seleccion_ejes import herrSeleccionEjes
        tool = herrSeleccionEjes(self.tipo_usuario, self.iface.mapCanvas(), self.iface, self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion_ejes.png'))
        seleccion_px.setMask(seleccion_px.mask())
        seleccion_cursor = QtGui.QCursor(seleccion_px)
        self.iface.mapCanvas().setCursor(seleccion_cursor)

    def h_seleccion_aleatoria(self):
        from .herr_seleccion_aleatoria import herrSeleccionAleatoria
        tool = herrSeleccionAleatoria(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion_aleatoria.png'))
        seleccion_px.setMask(seleccion_px.mask())
        seleccion_cursor = QtGui.QCursor(seleccion_px)
        self.iface.mapCanvas().setCursor(seleccion_cursor)

    def h_seleccion_circular(self):
        from .herr_seleccion_circular import herrSeleccionCircular
        tool = herrSeleccionCircular(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion_circular.png'))
        seleccion_px.setMask(seleccion_px.mask())
        seleccion_cursor = QtGui.QCursor(seleccion_px)
        self.iface.mapCanvas().setCursor(seleccion_cursor)

    def h_seleccionar_elementos(self):
        from .frm_seleccionar_elementos import frmSeleccionarElementos
        self.dialogo = frmSeleccionarElementos(self.iface.mapCanvas(), self.conn)
        self.dialogo.setWindowFlags(self.dialogo.windowFlags() & Qt.CustomizeWindowHint)
        self.dialogo.setWindowFlags(self.dialogo.windowFlags() & ~Qt.WindowMinMaxButtonsHint)
        self.dialogo.show()

    def h_nodo(self):
        from .herr_nodo import herrNodo
        self.tension = self.cmbTension.currentText()
        tool = herrNodo(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.iface.mapCanvas().setCursor(curNodo)

    def h_anotacion(self):
        from .herr_anotacion import herrAnotacion
        tool = herrAnotacion(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.iface.mapCanvas().setCursor(curNodo)

    def h_girar(self):
        self.ftrs_nodos = []
        self.ftrs_postes = []
        self.angulo = 0
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_nodos.append(ftr.id())
            if lyr.name()[:6] == 'Postes':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_postes.append(ftr.id())
        if len(self.ftrs_nodos) > 0 or len(self.ftrs_postes) > 0:
            from .frm_girar import frmGirar
            self.dialogo = frmGirar(self.mapCanvas, self.conn, self.ftrs_nodos, self.ftrs_postes)
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & Qt.CustomizeWindowHint)
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & ~Qt.WindowMinMaxButtonsHint)
            self.dialogo.show()

    def h_linea(self):
        from .herr_linea import herrLinea
        self.tension = self.cmbTension.currentText()
        #QMessageBox.information(None, 'h_linea', str(tension))
        tool = herrLinea(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.iface.mapCanvas().setCursor(curLinea)

    def h_eje(self):
        from .herr_eje import herrEje
        tool = herrEje(self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punEje = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punEje.setMask(punEje.mask())
        curEje = QtGui.QCursor(punEje)
        self.iface.mapCanvas().setCursor(curEje)

    def h_agregar_vertice(self):
        from .herr_agregar_vertice import herrAgregarVertice
        tool = herrAgregarVertice(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.iface.mapCanvas().setCursor(curNodo)

    def h_quitar_vertice(self):
        from .herr_quitar_vertice import herrQuitarVertice
        tool = herrQuitarVertice(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.iface.mapCanvas().setCursor(curNodo)

    def h_poste(self):
        from .herr_poste import herrPoste
        self.tension = self.cmbTension.currentText()
        tool = herrPoste(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punPoste = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punPoste.setMask(punPoste.mask())
        curPoste = QtGui.QCursor(punPoste)
        self.iface.mapCanvas().setCursor(curPoste)

    def h_mover(self):
        from .herr_mover import herrMover
        tool = herrMover(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punMover = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_mover.png'))
        punMover.setMask(punMover.mask())
        curMover = QtGui.QCursor(punMover)
        self.iface.mapCanvas().setCursor(curMover)

    def h_rotar(self):
        from .herr_rotar import herrRotar
        tool = herrRotar(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punRotar = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_rotar.png'))
        punRotar.setMask(punRotar.mask())
        curRotar = QtGui.QCursor(punRotar)
        self.iface.mapCanvas().setCursor(curRotar)

    def h_mover_ejes(self):
        from .herr_mover_ejes import herrMoverEjes
        tool = herrMoverEjes(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punMover = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_mover.png'))
        punMover.setMask(punMover.mask())
        curMover = QtGui.QCursor(punMover)
        self.iface.mapCanvas().setCursor(curMover)

    def h_rotar_ejes(self):
        from .herr_rotar_ejes import herrRotarEjes
        tool = herrRotarEjes(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punRotar = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_rotar.png'))
        punRotar.setMask(punRotar.mask())
        curRotar = QtGui.QCursor(punRotar)
        self.iface.mapCanvas().setCursor(curRotar)

    def h_conectar(self):
        from .herr_conectar import herrConectar
        tool = herrConectar(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punConectar = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_conectar.png'))
        punConectar.setMask(punConectar.mask())
        curConectar = QtGui.QCursor(punConectar)
        self.iface.mapCanvas().setCursor(curConectar)

    def h_area(self):
        from .herr_area import herrArea
        tool = herrArea(self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.iface.mapCanvas().setCursor(curLinea)

    def h_parcela(self):
        from .herr_parcela import herrParcela
        tool = herrParcela(self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.iface.mapCanvas().setCursor(curLinea)

    def h_borrar(self):
        if self.tipo_usuario==4:
            return
        ftrs_nodos = []
        ftrs_lineas = []
        ftrs_postes = []
        ftrs_areas = []
        ftrs_parcelas = []
        ftrs_anotaciones = []
        capas = []
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        str_nodos = '0'
        str_lineas = '0'
        str_postes = '0'
        str_areas = '0'
        str_parcelas = '0'
        str_anotaciones = '0'
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                for ftr in lyr.selectedFeatures():
                    ftrs_nodos.append(ftr.id())
                    str_nodos = str_nodos + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name()[:6] == 'Lineas':
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
            if lyr.name() == 'Anotaciones':
                for ftr in lyr.selectedFeatures():
                    ftrs_parcelas.append(ftr.id())
                    str_anotaciones = str_anotaciones + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
        if self.tipo_usuario!=4 and len(ftrs_nodos) + len(ftrs_lineas) + len(ftrs_postes) + len(ftrs_areas) + len(ftrs_parcelas) + len(ftrs_anotaciones) > 0:
            if len(capas)==1:
                reply = QMessageBox.question(None, 'EnerGis', 'Desea borrar los elementos seleccionados ?', QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
                layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.name()[:6] == 'Lineas':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Lineas WHERE Geoname IN (" + str_lineas + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.warning(None, 'EnerGis 5', "No se pudieron borrar Lineas ! - (" + str_lineas + ")")
                        lyr.triggerRepaint()
                    elif lyr.name()[:5] == 'Nodos':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Nodos WHERE Geoname IN (" + str_nodos + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.warning(None, 'EnerGis 5', "No se pudieron borrar Nodos ! - (" + str_nodos + ")")
                        lyr.triggerRepaint()
                    elif lyr.name()[:6] == 'Postes':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Postes WHERE Geoname IN (" + str_postes + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.warning(None, 'EnerGis 5', "No se pudieron borrar Postes ! - (" + str_postes + ")")
                        lyr.triggerRepaint()
                    elif lyr.name() == 'Areas':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Areas WHERE Geoname IN (" + str_areas + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.warning(None, 'EnerGis 5', "No se pudieron borrar Areas !")
                        lyr.triggerRepaint()
                    elif lyr.name() == 'Parcelas':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Parcelas WHERE Geoname IN (" + str_parcelas + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.warning(None, 'EnerGis 5', "No se pudieron borrar Parcelas !")
                        lyr.triggerRepaint()
                    elif lyr.name() == 'Anotaciones':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Anotaciones WHERE Geoname IN (" + str_anotaciones + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.warning(None, 'EnerGis 5', "No se pudieron borrar Anotaciones !")
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
                layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.name()[:6] == 'Lineas':
                        for capa in capas:
                            if capa==lyr.name():
                                str_tension = lyr.name() [7 - len(lyr.name()):]
                                if str_tension.strip() == 'Proyectos':
                                    str_tension='0'
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Lineas WHERE Tension=" + str_tension + " AND Geoname IN (" + str_lineas + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.warning(None, 'EnerGis 5', "No se pudieron borrar Lineas !")
                                lyr.triggerRepaint()
                    elif lyr.name()[:5] == 'Nodos':
                        for capa in capas:
                            if capa==lyr.name():
                                str_tension = lyr.name() [6 - len(lyr.name()):]
                                if str_tension.strip() == 'Proyectos':
                                    str_tension='0'
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Nodos WHERE Tension=" + str_tension + " AND Geoname IN (" + str_nodos + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.warning(None, 'EnerGis 5', "No se pudieron borrar Nodos !")
                                lyr.triggerRepaint()
                    elif lyr.name()[:6] == 'Postes':
                        for capa in capas:
                            if capa==lyr.name():
                                str_tension = lyr.name() [7 - len(lyr.name()):]
                                if str_tension.strip() == 'Proyectos':
                                    str_tension='0'
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Postes WHERE Tension=" + str_tension + " AND Geoname IN (" + str_postes + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.warning(None, 'EnerGis 5', "No se pudieron borrar Postes !")
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
                                    QMessageBox.warning(None, 'EnerGis 5', "No se pudieron borrar Areas !")
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
                                    QMessageBox.warning(None, 'EnerGis 5', "No se pudieron borrar Parcelas !")
                                lyr.triggerRepaint()
                    elif lyr.name() == 'Anotaciones':
                        for capa in capas:
                            if capa=='Anotaciones':
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Anotaciones WHERE Geoname IN (" + str_anotaciones + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.warning(None, 'EnerGis 5', "No se pudieron borrar Anotaciones !")
                                lyr.triggerRepaint()
                    else:
                        #lyr.triggerRepaint()
                        pass
            return

    def ejecutar_sql(self):
        from .frm_sql import frmSql
        self.dialogo = frmSql(self.iface.mapCanvas, self.conn)
        self.dialogo.show()

    def seguridad(self):
        from .frm_seguridad import frmSeguridad
        self.dialogo = frmSeguridad(self.str_conexion_seguridad)
        self.dialogo.show()

    def h_datos_eje(self):
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        ftrs_ejes = []
        for lyr in layers:
            if lyr.name() == 'Ejes de Calle':
                for ftr in lyr.selectedFeatures():
                    ftrs_ejes.append(ftr)
        if len(ftrs_ejes) > 0:
            from .frm_datos_ejes import frmDatosEjes
            self.dialogo = frmDatosEjes(self.tipo_usuario, self.conn, ftrs_ejes)
            self.dialogo.show()

    def h_borrar_ejes(self):
        ftrs_ejes = []
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        str_ejes = '0'
        for lyr in layers:
            if lyr.name() == 'Ejes de Calle':
                for ftr in lyr.selectedFeatures():
                    ftrs_ejes.append(ftr.id())
                    str_ejes = str_ejes + ',' + str(ftr.id())
        if len(ftrs_ejes) > 0:
            reply = QMessageBox.question(None, 'EnerGis', 'Desea borrar los ejes seleccionados ?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Ejes de Calle':
                    cursor = self.conn.cursor()
                    try:
                        cursor.execute("DELETE FROM Ejes WHERE Geoname IN (" + str_ejes + ")")
                        self.conn.commit()
                    except:
                        self.conn.rollback()
                        QMessageBox.warning(None, 'EnerGis 5', "No se pudieron borrar Ejes !")
                    lyr.triggerRepaint()

    def h_zoom(self):
        from .herr_zoom import herrZoom
        tool = herrZoom(self.iface.mapCanvas(), 'Zoom')
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punZoom = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_zoom.png'))
        punZoom.setMask(punZoom.mask())
        curZoom = QtGui.QCursor(punZoom)
        self.iface.mapCanvas().setCursor(curZoom)

    def h_Pan(self):
        from .herr_zoom import herrZoom
        tool = herrZoom(self.iface.mapCanvas(), 'Pan')
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punZoom = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_pan.png'))
        punZoom.setMask(punZoom.mask())
        curZoom = QtGui.QCursor(punZoom)
        self.iface.mapCanvas().setCursor(curZoom)

    def h_crear_proyecto(self):
        text, ok = QInputDialog.getText(None, 'Ingreso de Datos', 'Nombre del Proyecto:')
        if ok:
            nuevo_proyecto = str(text)
        else:
            return
        if nuevo_proyecto=='':
            return
        for i in range (0, self.cmbProyecto.count()):
            if self.cmbProyecto.itemText(i) == nuevo_proyecto:
                QMessageBox.critical(None, 'EnerGis 5', 'Ya existe un proyecto con ese nombre')
                return
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO Proyectos (nombre, descripcion, fecha) VALUES ('" + nuevo_proyecto + "', '', GETDATE())")
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 5', "No se pudo agregar el Proyecto !")
        QMessageBox.information(None, 'EnerGis 5', 'Proyecto Creado')
        self.cmbProyecto.addItem(nuevo_proyecto)
        self.cmbProyecto.setCurrentIndex(self.cmbProyecto.count() - 1)
        self.proyecto = ''

    def elijo_proyecto(self):
        if self.cmbProyecto.currentText()=='<Proyecto>':
            for action in self.actions:
                if str(action.text())=='Modificar Proyecto':
                    action.setEnabled(False)
        else:
            for action in self.actions:
                if str(action.text())=='Modificar Proyecto':
                    action.setEnabled(True)

    def h_borrar_proyecto(self):
        reply = QMessageBox.question(None, 'EnerGis', 'Desea eliminar definitivamente el proyecto ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        self.borro_proyecto()

    def borro_proyecto(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM proyectos WHERE nombre='" + self.cmbProyecto.currentText() + "'")
            cursor.execute("DELETE FROM Nodos WHERE Tension=0 AND Alimentador='" + self.cmbProyecto.currentText() + "'")
            cursor.execute("DELETE FROM Lineas WHERE Tension=0 AND Alimentador='" + self.cmbProyecto.currentText() + "'")
            cursor.execute("DELETE FROM Postes WHERE Tension=0 AND Descripcion = '" + self.cmbProyecto.currentText() + "'")
            cursor.execute("DELETE FROM Anotaciones WHERE Proyecto = '" + self.cmbProyecto.currentText() + "'")
            self.conn.commit()
        except:
            self.conn.rollback()
        self.cmbProyecto.removeItem(self.cmbProyecto.currentIndex())
        QMessageBox.information(None, 'EnerGis 5', "Proyecto Borrado !")
        self.proyecto = ''
        self.cmbProyecto.setCurrentIndex(0)
        for action in self.actions:
            if str(action.text())=='Modificar Proyecto':
                action.setChecked(True)
            if str(action.text())=='Nuevo Proyecto':
                action.setEnabled(True)
            if str(action.text())=='Incorporar Proyecto':
                action.setEnabled(False)
            if str(action.text())=='Borrar Proyecto':
                action.setEnabled(False)
            if str(action.text())=='Agregar Cota':
                action.setEnabled(False)
            if str(action.text())=='Borrar última Cota':
                action.setEnabled(False)
            if str(action.text())=='Borrar Cotas':
                action.setEnabled(False)
        self.cmbProyecto.setEnabled(True)
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            lyr.triggerRepaint()

    def h_editar_proyecto(self):
        b_estado=False
        #QMessageBox.information(None, 'EnerGis 5', '"Alimentador" = ' + "''")
        self.h_seleccion()
        if self.cmbProyecto.currentText()=='<Proyecto>':
            for action in self.actions:
                if str(action.text())=='Modificar Proyecto':
                    QMessageBox.information(None, 'EnerGis 5', 'Debe elegir un proyecto')
                    action.setChecked(False)
                if str(action.text())=='Nuevo Proyecto':
                    action.setEnabled(True)
                if str(action.text())=='Incorporar Proyecto':
                    action.setEnabled(False)
                if str(action.text())=='Borrar Proyecto':
                    action.setEnabled(False)
                if str(action.text())=='Agregar Cota':
                    action.setEnabled(False)
                if str(action.text())=='Borrar última Cota':
                    action.setEnabled(False)
                if str(action.text())=='Borrar Cotas':
                    action.setEnabled(False)
            return
        for action in self.actions:
            if str(action.text())=='Modificar Proyecto':
                b_estado = action.isChecked()
        self.cmbProyecto.setEnabled(True)
        if b_estado==True:
            self.proyecto = self.cmbProyecto.currentText()
            self.h_seleccion()
            for action in self.actions:
                if str(action.text())=='Nuevo Proyecto':
                    action.setEnabled(False)
                if str(action.text())=='Incorporar Proyecto':
                    action.setEnabled(True)
                if str(action.text())=='Borrar Proyecto':
                    action.setEnabled(True)
                if str(action.text())=='Agregar Cota':
                    action.setEnabled(True)
                if str(action.text())=='Borrar última Cota':
                    action.setEnabled(True)
                if str(action.text())=='Borrar Cotas':
                    action.setEnabled(True)
            self.cmbProyecto.setEnabled(False)
            n = self.iface.mapCanvas().layerCount()
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Postes Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'" + self.proyecto + "'")
                    lyr.triggerRepaint()
                    try:
                        geom = next(lyr.getFeatures()).geometry()
                        box = geom.buffer(25,1).boundingBox()
                        self.mapCanvas.setExtent(box)
                        self.mapCanvas.refresh()
                    except:
                        pass
                if lyr.name() == 'Lineas Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'" + self.proyecto + "'")
                    lyr.triggerRepaint()
                if lyr.name() == 'Anotaciones':
                    lyr.setSubsetString('"Proyecto" = ' + "'" + self.proyecto + "'")
                    lyr.triggerRepaint()
                if lyr.name() == 'Nodos Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'" + self.proyecto + "'")
                    lyr.triggerRepaint()
                    try:
                        geom = next(lyr.getFeatures()).geometry()
                        box = geom.buffer(25,1).boundingBox()
                        self.mapCanvas.setExtent(box)
                        self.mapCanvas.refresh()
                    except:
                        pass
                if lyr.name() == 'Cotas':
                    lyr.setSubsetString('"proyecto" = ' + "'" + self.proyecto + "'")
                    lyr.triggerRepaint()
        else:
            self.proyecto = ''
            self.h_seleccion()
            for action in self.actions:
                if str(action.text())=='Nuevo Proyecto':
                    action.setEnabled(True)
                if str(action.text())=='Incorporar Proyecto':
                    action.setEnabled(False)
                if str(action.text())=='Borrar Proyecto':
                    action.setEnabled(False)
                if str(action.text())=='Agregar Cota':
                    action.setEnabled(False)
                if str(action.text())=='Borrar última Cota':
                    action.setEnabled(False)
                if str(action.text())=='Borrar Cotas':
                    action.setEnabled(False)
            n = self.iface.mapCanvas().layerCount()
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Nodos Proyectos' or lyr.name() == 'Lineas Proyectos' or lyr.name() == 'Postes Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'@@'")
                    lyr.triggerRepaint()
                if lyr.name() == 'Anotaciones':
                    lyr.setSubsetString('"proyecto" = ' + "''")
                if lyr.name() == 'Cotas':
                    lyr.setSubsetString('"proyecto" = ' + "'@@'")
                    lyr.triggerRepaint()
            self.cmbProyecto.setCurrentIndex(0)

    def h_incorporar_proyecto(self):
        reply = QMessageBox.question(None, 'EnerGis', 'Desea incorporar el proyecto al modelo ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        try:
            str_expediente='1111/2001'
            texto, ok = QInputDialog.getText(
                None,
                "Ingresar expediente",
                "Número de Expediente:",
                text=str_expediente
            )
            if ok:  # Usuario apretó Aceptar
                str_expediente = texto
            cursor = self.conn.cursor()
            cursor.execute("UPDATE Nodos SET Tension=CAST(subzona AS INT),subzona='' WHERE Tension=0 AND Alimentador='" + self.proyecto + "'")
            cursor.execute("UPDATE Lineas SET Tension=CAST(exp AS INT),Exp='" + str_expediente + "' WHERE Tension=0 AND Alimentador='" + self.proyecto + "'")
            cursor.execute("UPDATE Postes SET Tension=CAST(profundidad AS INT) WHERE Tension=0 AND Descripcion='" + self.proyecto + "'")
            #reply = QMessageBox.question(None, 'EnerGis', 'Desea copiar las Anotaciones del proyecto al Modelo ?', QMessageBox.Yes, QMessageBox.No)
            #if reply == QMessageBox.Yes:
            #    cursor.execute("UPDATE Anotacione<s SET Proyecto='' WHERE Proyecto='" + self.proyecto + "'")
            #    for lyr in layers:
            #        if lyr.name() == 'Anotaciones':
            #            lyr.setSubsetString('"Proyecto" = ' + "''")
            self.conn.commit()
            QMessageBox.information(None, 'EnerGis 5', "Proyecto Incorporado !")
            self.borro_proyecto()
            self.crear_red
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 5', "No se pudo incorporar el Proyecto !")

    def h_cotas(self):
        from .herr_cota import herrCota
        tool = herrCota(self.proyecto, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punCota = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punCota.setMask(punCota.mask())
        curCota = QtGui.QCursor(punCota)
        self.iface.mapCanvas().setCursor(curCota)

    def h_borrar_ultima_cota(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM Cotas WHERE proyecto='" + self.proyecto + "' AND id IN (SELECT TOP 1 id FROM Cotas WHERE proyecto='" + self.proyecto + "' ORDER BY id DESC)")
            self.conn.commit()
        except:
            self.conn.rollback()
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name() == 'Cotas':
                lyr.triggerRepaint()

    def h_borrar_cotas(self):
        reply = QMessageBox.question(None, 'EnerGis 5', 'Desea borrar todas las cotas ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM Cotas WHERE proyecto='" + self.proyecto + "'")
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 5', "No se pudo Borrar !")
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name() == 'Cotas':
                lyr.triggerRepaint()

    def analisis_carga(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        #Hay que hacer una SQL y listar en excel los trafos con sus potencias y demandas por los usuarios

    def calculo_cargas(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        if self.tipo_usuario==4:
            return
        if self.tipo_navegacion==0:
            from .frm_calculo_cargas_ant import frmCalculoCargas
            self.dialogo = frmCalculoCargas(self.conn, 2)
            self.dialogo.show()
        else:
            from .frm_calculo_cargas import frmCalculoCargas
            self.dialogo = frmCalculoCargas(self.conn, 2)
            self.dialogo.show()

    def momentos_electricos(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        ftrs = []
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                for ftr in lyr.selectedFeatures():
                    ftrs.append(ftr)
        if len(ftrs) != 1:
            QMessageBox.information(None, 'EnerGis 5', 'Debe seleccionar un nodo')
            return
        id = ftrs[0].id()
        from .frm_momentos_electricos import frmMomentosElectricos
        dialogo = frmMomentosElectricos(self.conn, id)
        dialogo.exec()
        dialogo.close()

    def h_flujo(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        if self.tipo_usuario==4:
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE Transformadores SET Potencia=5 WHERE Potencia IS NULL")
            cursor.execute("UPDATE A SET d1=o1, d2=o2, d3=o3, d4=o4 FROM (SELECT * FROM (SELECT Nombre, Val1 AS d1, Val2 AS d2, Val3 AS d3, Val4 AS d4 FROM Nodos WHERE (Elmt = 4)) AS D INNER JOIN (SELECT Id_ct, MAX(Potencia) AS o1, MAX(Conexionado) AS o2, MAX(Tension_1) AS o3, MAX(Tension_2) AS o4 FROM Transformadores GROUP BY Id_ct) AS O ON D.Nombre = O.Id_ct) A")
            cursor.execute("UPDATE Transformadores_Parametros SET P01=18.276*[Potencia]^0.689 WHERE P01 IS NULL")
            cursor.execute("UPDATE Transformadores_Parametros SET P01=18.276*[Potencia]^0.689 WHERE P01 = 0")
            #creo los transformadores_parametros que falten
            cursor.execute("INSERT INTO Transformadores_Parametros SELECT Transformadores.Id_trafo, 0.01 AS R1, 0.05 AS X1, POWER (18.276 * [Potencia], 0.689) AS P01, 100 AS Tap1 FROM Transformadores WHERE Id_Trafo NOT IN (SELECT Id_Trafo FROM Transformadores_Parametros)")
            self.conn.commit()
        except:
            self.conn.rollback()

        if self.tipo_navegacion==0:
            QMessageBox.information(None, 'EnerGis 5', "Para utilizar el flujo de cargas faltan instalar componentes.\n Verifique en Menú > Administrador > Actualizar a .NET")
            return

        from .frm_flujo_potencias import frmFlujoPotencias
        dialogo = frmFlujoPotencias(self.id_usuario_sistema, self.conn, -1, self.amnodos, self.amlineas, self.monodos)
        dialogo.exec()
        dialogo.close()

    def h_flujo_desequilibrado(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        if self.tipo_usuario==4:
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE Transformadores SET Potencia=5 WHERE Potencia IS NULL")
            cursor.execute("UPDATE A SET d1=o1, d2=o2, d3=o3, d4=o4 FROM (SELECT * FROM (SELECT Nombre, Val1 AS d1, Val2 AS d2, Val3 AS d3, Val4 AS d4 FROM Nodos WHERE (Elmt = 4)) AS D INNER JOIN (SELECT Id_ct, MAX(Potencia) AS o1, MAX(Conexionado) AS o2, MAX(Tension_1) AS o3, MAX(Tension_2) AS o4 FROM Transformadores GROUP BY Id_ct) AS O ON D.Nombre = O.Id_ct) A")
            cursor.execute("UPDATE Transformadores_Parametros SET P01=18.276*[Potencia]^0.689 WHERE P01 IS NULL")
            cursor.execute("UPDATE Transformadores_Parametros SET P01=18.276*[Potencia]^0.689 WHERE P01 = 0")
            #creo los transformadores_parametros que falten
            cursor.execute("INSERT INTO Transformadores_Parametros SELECT Transformadores.Id_trafo, 0.01 AS R1, 0.05 AS X1, POWER (18.276 * [Potencia], 0.689) AS P01, 100 AS Tap1 FROM Transformadores WHERE Id_Trafo NOT IN (SELECT Id_Trafo FROM Transformadores_Parametros)")
            self.conn.commit()
        except:
            self.conn.rollback()

        if self.tipo_navegacion==0:
            QMessageBox.information(None, 'EnerGis 5', "Para utilizar el flujo de cargas faltan instalar componentes.\n Verifique en Menú > Administrador > Actualizar a .NET")
            return

        from .frm_flujo_potencias_trifasico import frmFlujoPotencias
        dialogo = frmFlujoPotencias(self.id_usuario_sistema, self.conn, -1, self.amnodos, self.amlineas, self.monodos)
        dialogo.exec()
        dialogo.close()

    def h_cortocircuito(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        if self.tipo_usuario==4:
            return

        if self.tipo_navegacion==0:
            QMessageBox.information(None, 'EnerGis 5', "Para utilizar el cálculo de cortocircuito faltan instalar componentes.\n Verifique en Menú > Administrador > Actualizar a .NET")
            return

        from .frm_cortocircuito import frmCortocircuito
        dialogo = frmCortocircuito(self.id_usuario_sistema, self.conn, -1, self.amnodos, self.amlineas, self.monodos)
        dialogo.exec()
        dialogo.close()

    def actualizar_usuarios(self):
        self.conn.autocommit = False
        cursor = self.conn.cursor()
        try:
            cursor.execute("TRUNCATE TABLE Suministros_Nuevos")
            cursor.execute("INSERT INTO Suministros_Nuevos (id_suministro) SELECT usuarios.id_suministro FROM suministros RIGHT JOIN usuarios ON suministros.id_suministro = usuarios.id_suministro WHERE usuarios.ES=1 AND suministros.id_suministro IS NULL GROUP BY usuarios.id_suministro HAVING usuarios.id_suministro IS NOT NULL")
            self.conn.commit()
        except:
            self.conn.rollback()
        self.actualizar_grilla_usuarios()

    def aproximar_usuarios(self):
        seleccion=''
        self.sql="SELECT Min(Nodos.Geoname) AS geoname, Usuarios.calle + ' ' + Usuarios.altura AS direccion, VW_CCDATOSCOMERCIALES.Ruta AS Ruta FROM (Nodos INNER JOIN (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) ON Nodos.Geoname = Suministros.id_nodo) LEFT JOIN VW_CCDATOSCOMERCIALES ON Usuarios.id_usuario = VW_CCDATOSCOMERCIALES.Id_Usuario WHERE Usuarios.calle LIKE '%" + self.txtCalle.text() + "%' GROUP BY VW_CCDATOSCOMERCIALES.Ruta, Usuarios.calle, Usuarios.altura ORDER BY VW_CCDATOSCOMERCIALES.Ruta, Usuarios.calle, Usuarios.altura"
        from .frm_elegir import frmElegir
        dialogo = frmElegir(self.mapCanvas, self.conn, self.sql)
        dialogo.exec()
        if dialogo.seleccionado != '':
            seleccion = dialogo.seleccionado
            #QMessageBox.information(None, 'EnerGis 5', self.suministro)
            #QMessageBox.information(None, 'EnerGis 5', seleccion)
            if self.suministro!='':
                cursor = self.conn.cursor()
                try:
                    cursor.execute("DELETE FROM Suministros WHERE id_suministro='" + self.suministro + "'")
                    cursor.execute("INSERT INTO Suministros (id_nodo,id_suministro) VALUES ( " + seleccion + ",'" + self.suministro + "')")
                    self.conn.commit()
                except:
                    self.conn.rollback()
                self.actualizar_usuarios()
        dialogo.close()

    def actualizar_grilla_usuarios(self):
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        cursor.execute("SELECT Usuarios.Calle, Usuarios.Altura, VW_CCDATOSCOMERCIALES.Ruta, Suministros_Nuevos.id_suministro FROM (Suministros_Nuevos INNER JOIN Usuarios ON Suministros_Nuevos.id_suministro = Usuarios.id_suministro) LEFT JOIN VW_CCDATOSCOMERCIALES ON Usuarios.id_usuario = VW_CCDATOSCOMERCIALES.Id_Usuario ORDER BY VW_CCDATOSCOMERCIALES.Ruta, Usuarios.Calle, Usuarios.Altura")
        #convierto el cursor en array
        recordset = tuple(cursor)
        self.tblUsuariosNuevos.setRowCount(len(recordset))
        self.dock_widget2.setWindowTitle(str(len(recordset)) +" Usuarios Nuevos")
        self.tblUsuariosNuevos.setColumnCount(4)
        self.tblUsuariosNuevos.setHorizontalHeaderLabels(["calle", "numero", "ruta", "suministro"])
        self.tblUsuariosNuevos.setColumnWidth(0, 120)
        self.tblUsuariosNuevos.setColumnWidth(1, 60)
        self.tblUsuariosNuevos.setColumnWidth(2, 50)
        self.tblUsuariosNuevos.setColumnWidth(3, 60)
        self.tblUsuariosNuevos.setRowCount(len(recordset))
        for i in range (0, len(recordset)):
            self.tblUsuariosNuevos.setItem(i, 0, QTableWidgetItem(recordset[i][0]))
            self.tblUsuariosNuevos.setItem(i, 1, QTableWidgetItem(recordset[i][1]))
            self.tblUsuariosNuevos.setItem(i, 2, QTableWidgetItem(str(recordset[i][2])))
            self.tblUsuariosNuevos.setItem(i, 3, QTableWidgetItem(recordset[i][3]))

    def elijo_suministro(self):
        self.suministro = self.tblUsuariosNuevos.item(self.tblUsuariosNuevos.currentRow(),3).text()
        tension = int(self.cmbTension.currentText())
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        cursor.execute("SELECT Usuarios.id_usuario, Usuarios.nombre, Usuarios.calle, Usuarios.altura, Usuarios.altura_ex, Tarifas.Nivel_Tension FROM Usuarios INNER JOIN Suministros_Nuevos ON Usuarios.id_suministro = Suministros_Nuevos.id_suministro LEFT OUTER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa WHERE Suministros_Nuevos.id_suministro ='" + self.suministro + "'")
        #convierto el cursor en array
        recordset = tuple(cursor)
        if len(recordset)==0:
            return
        self.txtUsuario.setText(str(recordset[0][0]))
        self.txtNombre.setText(str(recordset[0][1]).strip())
        self.txtCalle.setText(str(recordset[0][2]).strip())
        self.txtNumero.setText(str(recordset[0][3].strip()) + ' - ' + str(recordset[0][4]).strip())
        nivel_tension='BT'
        if recordset[0][4]!=None:
            nivel_tension = recordset[0][4]
        if nivel_tension=='MT' and tension < 1000:
            QMessageBox.information(None, 'EnerGis 5', 'La tarifa es de un Nivel de Tensión distinto al seleccionado (' + self.cmbTension.currentText() + ')')
        if nivel_tension=='BT' and tension >= 1000:
            QMessageBox.information(None, 'EnerGis 5', 'La tarifa es de un Nivel de Tensión distinto al seleccionado (' + self.cmbTension.currentText() + ')')
        #activo la herramienta para pegarlo en el mapa
        if self.tipo_usuario==4:
            return
        from .herr_suministro import herrSuministro
        tool = herrSuministro(self, self.iface.mapCanvas(), self.conn, tension, self.suministro)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_suministro.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.iface.mapCanvas().setCursor(curNodo)

    def elijo_item(self):
        #QMessageBox.information(None, 'EnerGis 5', self.tblResultado.selectedItems()[0].text())
        #QMessageBox.information(None, 'EnerGis 5', self.tblResultado.selectedItems()[3].text())
        geom = QgsGeometry.fromWkt(self.tblResultado.selectedItems()[3].text())
        box = geom.buffer(25,1).boundingBox()
        self.mapCanvas.setExtent(box)
        self.mapCanvas.refresh()

    def m_separar_suministros(self):
        if self.suministro==None:
            QMessageBox.information(None, 'EnerGis 5', 'Elija un suministro para separar')
            return
        reply = QMessageBox.question(None, 'EnerGis 5', 'Desea separar a los usuarios del suministro ' + self.suministro + '?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.conn.autocommit = False
            cursor = self.conn.cursor()
            try:
                cursor.execute("UPDATE Usuarios SET id_suministro=id_usuario WHERE id_suministro='" + self.suministro + "'")
                self.conn.commit()
            except:
                self.conn.rollback()

    def m_suministros_sin_usuarios(self):
        cursor = self.conn.cursor()
        self.conn.autocommit = True
        cursor.execute("SELECT Nodos.Geoname, Nodos.Tension FROM ((Nodos LEFT JOIN Lineas AS Lineas_1 ON Nodos.Geoname = Lineas_1.Hasta) LEFT JOIN (Suministros LEFT JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo) LEFT JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE Nodos.Elmt = 6 GROUP BY Nodos.Geoname, Nodos.Tension, Nodos.Elmt HAVING (COUNT(Lineas_1.Geoname) + COUNT(Lineas.Geoname) = 1) AND (COUNT(Usuarios.id_usuario) = 0) OR (COUNT(Lineas_1.Geoname) + COUNT(Lineas.Geoname) = 0) AND (COUNT(Usuarios.id_usuario) = 0)")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer:
                lyr.removeSelection()
        seleccion_n = []
        for n in range(0, len(recordset)):
            seleccion_n.append(recordset[n][0])
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(seleccion_n)
        from .frm_seleccion import frmSeleccion
        dialogo = frmSeleccion(self.mapCanvas)
        for m in range (0, len(seleccion_n)):
            dialogo.liwNodos.addItem(QListWidgetItem(str(seleccion_n[m])))
        dialogo.show()

    def m_suministros_con_coordenadas_externas(self):
        from .mod_usuarios_nuevos import suministros_con_coordenadas_externas
        suministros_con_coordenadas_externas(self.mapCanvas, self.conn, self.srid)

    def m_suministros_con_ejes_de_calle(self):
        from .mod_usuarios_nuevos import suministros_con_ejes_de_calle
        suministros_con_ejes_de_calle(self.mapCanvas, self.conn, self.srid)

    def m_suministros_por_catastro(self):
        from .mod_usuarios_nuevos import suministros_por_catastro
        suministros_por_catastro(self.mapCanvas, self.conn, self.srid)

    def m_conectar_suministros_aislados(self):
        from .mod_usuarios_nuevos import conectar_suministros_aislados
        conectar_suministros_aislados(self.mapCanvas, self.conn, self.srid)
