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

import os
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QListWidgetItem, QTableWidgetItem
#from PyQt5.QtWidgets import QMessageBox
from qgis.core import QgsGeometry
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_buscar.ui'))

class frmBuscar(DialogType, DialogBase):

    def __init__(self, mapCanvas, conn):
        super().__init__()
        self.setupUi(self)

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas
        self.conn = conn
        
        basepath = os.path.dirname(os.path.realpath(__file__))
        img_buscar = os.path.join(basepath,"icons", 'img_buscar.png')
        self.cmdBuscar.setIcon(QtGui.QIcon(img_buscar))
        #QMessageBox.information(None, 'EnerGis 5', 'Inicio')
        cnn = conn
        cursor = cnn.cursor()
        cursor.execute("SELECT id, Descripcion FROM Elementos_Nodos")
        #convierto el cursor en array
        elementos_nodos = tuple(cursor)
        cursor.close()

        self.liwElementos.addItem('Nodo')
        for elemento in elementos_nodos:
            #self.liwElementos.addItem(elemento[1])
            item = QListWidgetItem()
            item.setText(elemento[1])
            item.setData(QtCore.Qt.UserRole, elemento[0])
            self.liwElementos.addItem(item)

        self.liwElementos.addItem('Usuario')
        self.liwElementos.addItem('Electrodependiente')
        self.liwElementos.addItem('Prosumidor')
        self.liwElementos.addItem('Medidor')
        self.liwElementos.addItem('Poste')
        self.liwElementos.addItem('Línea')

        self.liwElementos.itemClicked.connect(self.elijo_elemento)
        self.cmdBuscar.clicked.connect(self.buscar)
        self.tblResultado.itemClicked.connect(self.elijo_item)
        
    def elijo_elemento(self):
        self.cmbCampos.clear()
        if self.liwElementos.selectedItems()[0].text() == "Suministro":
            self.cmbCampos.addItem ("Id Suministro")
            return
        if self.liwElementos.selectedItems()[0].text() == "Usuario":
            self.cmbCampos.addItem ("Id Usuario")
            self.cmbCampos.addItem ("Id Suministro")
            self.cmbCampos.addItem ("Nombre")
            return
        if self.liwElementos.selectedItems()[0].text() == "Medidor":
            self.cmbCampos.addItem ("Id Medidor")
            self.cmbCampos.addItem ("Id Usuario")
            self.cmbCampos.addItem ("Id Suministro")
            return
        if self.liwElementos.selectedItems()[0].text() == "Poste":
            self.cmbCampos.addItem ("Geoname")
            return
        if self.liwElementos.selectedItems()[0].text() == "Línea":
            self.cmbCampos.addItem ("Geoname")
            self.cmbCampos.addItem ("Conductor")
        else:
            self.cmbCampos.addItem ("Nombre")
            self.cmbCampos.addItem ("Geoname")
            self.cmbCampos.addItem ("Descripción")

    def buscar(self):
        if len(self.liwElementos.selectedItems())==0:
            return
        if self.liwElementos.selectedItems()[0].text() == "Suministro":
            if self.cmbCampos.currentText() == "Id Suministro":
                strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE Usuarios.id_suministro = '" + str(self.txtValor.text()) + "'"
                pass
            if str(self.txtValor.text())=="":
                strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname"
                pass
        else:
            if self.liwElementos.selectedItems()[0].text() == "Usuario":
                if self.cmbCampos.currentText() == "Id Usuario":
                    strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE Usuarios.id_usuario = " + str(self.txtValor.text())
                    pass
                if self.cmbCampos.currentText() == "Id Suministro":
                    strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE Usuarios.id_suministro = '" + str(self.txtValor.text()) + "'"
                    pass
                if self.cmbCampos.currentText() == "Nombre":
                    strSql = "SELECT TOP 300 Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE Usuarios.nombre LIKE '%" + str(self.txtValor.text()) + "%'"
                    pass
                if str(self.txtValor.text())=="":
                    strSql = "SELECT TOP 300 Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname"
                    pass
            else:
                if self.liwElementos.selectedItems()[0].text() == "Electrodependiente":
                    if self.cmbCampos.currentText() == "Id Usuario":
                        strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE electrodependiente='S' AND Usuarios.id_usuario = " + str(self.txtValor.text())
                        pass
                    if self.cmbCampos.currentText() == "Id Suministro":
                        strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE electrodependiente='S' AND Usuarios.id_suministro = '" + str(self.txtValor.text()) + "'"
                        pass
                    if self.cmbCampos.currentText() == "Nombre":
                        strSql = "SELECT TOP 300 Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE electrodependiente='S' AND Usuarios.nombre LIKE '%" + str(self.txtValor.text()) + "%'"
                        pass
                    if str(self.txtValor.text())=="":
                        strSql = "SELECT TOP 300 Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE electrodependiente='S'"
                        pass
                else:
                    if self.liwElementos.selectedItems()[0].text() == "Prosumidor":
                        if self.cmbCampos.currentText() == "Id Usuario":
                            strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE prosumidor<>'' AND Usuarios.id_usuario = " + str(self.txtValor.text())
                            pass
                        if self.cmbCampos.currentText() == "Id Suministro":
                            strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE prosumidor<>'' AND Usuarios.id_suministro = '" + str(self.txtValor.text()) + "'"
                            pass
                        if self.cmbCampos.currentText() == "Nombre":
                            strSql = "SELECT TOP 300 Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE prosumidor<>'' AND Usuarios.nombre LIKE '%" + str(self.txtValor.text()) + "%'"
                            pass
                        if str(self.txtValor.text())=="":
                            strSql = "SELECT TOP 300 Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE prosumidor<>''"
                            pass
                    else:
                        if self.liwElementos.selectedItems()[0].text() == "Medidor":
                            if self.cmbCampos.currentText() == "Id Medidor":
                                strSql = "SELECT Nodos.Geoname, Usuarios.Nombre, Medidores.nro_medidor AS Medidor, obj.STEnvelope().ToString() FROM (Medidores INNER JOIN Usuarios ON Medidores.id_usuario = Usuarios.id_usuario) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE Medidores.nro_medidor = '" + str(self.txtValor.text()) + "'"
                                pass
                            if self.cmbCampos.currentText() == "Id Usuario":
                                strSql = "SELECT Nodos.Geoname, Usuarios.Nombre, Medidores.nro_medidor AS Medidor, obj.STEnvelope().ToString() FROM (Medidores INNER JOIN Usuarios ON Medidores.id_usuario = Usuarios.id_usuario) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE Usuarios.id_usuario = " + str(self.txtValor.text())
                                pass
                            if self.cmbCampos.currentText() == "Id Suministro":
                                strSql = "SELECT Nodos.Geoname, Usuarios.Nombre, Medidores.nro_medidor AS Medidor, obj.STEnvelope().ToString() FROM (Medidores INNER JOIN Usuarios ON Medidores.id_usuario = Usuarios.id_usuario) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE Usuarios.id_suministro = '" + str(self.txtValor.text()) + "'"
                                pass
                            if str(self.txtValor.text())=="":
                                strSql = "SELECT Nodos.Geoname, Usuarios.Nombre, Medidores.nro_medidor AS Medidor, obj.STEnvelope().ToString() FROM (Medidores INNER JOIN Usuarios ON Medidores.id_usuario = Usuarios.id_usuario) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro"
                                pass
                        else:
                            if self.liwElementos.selectedItems()[0].text() == "Poste":
                                if self.cmbCampos.currentText() == "Geoname":
                                    strSql = "SELECT Postes.Geoname, Postes.Tipo, Postes.Aislacion, obj.STEnvelope().ToString() FROM Postes WHERE Postes.Geoname = " + str(self.txtValor.text())
                                    pass
                                if str(self.txtValor.text())=="":
                                    strSql = "SELECT Postes.Geoname, Postes.Tipo, Postes.Aislacion, obj.STEnvelope().ToString() FROM Postes"
                                    pass
                            else:
                                if self.liwElementos.selectedItems()[0].text() == "Línea":
                                    if self.cmbCampos.currentText() == "Geoname":
                                        strSql = "SELECT Lineas.Geoname, Elementos_Lineas.Descripcion, Lineas.Fase, obj.STEnvelope().ToString(), Lineas.Tension, Lineas.Alimentador FROM Elementos_Lineas INNER JOIN Lineas ON Elementos_Lineas.Id = Lineas.Elmt WHERE Lineas.Geoname = " + str(self.txtValor.text())
                                        pass
                                    if self.cmbCampos.currentText() == "Conductor":
                                        strSql = "SELECT TOP 50 Lineas.Geoname, Elementos_Lineas.Descripcion, Lineas.Fase, obj.STEnvelope().ToString(), Lineas.Tension, Lineas.Alimentador FROM Elementos_Lineas INNER JOIN Lineas ON Elementos_Lineas.Id = Lineas.Elmt WHERE Elementos_Lineas.Descripcion LIKE '%" + str(self.txtValor.text()) + "%'"
                                        pass
                                    if str(self.txtValor.text())=="":
                                        strSql = "SELECT Lineas.Geoname, Elementos_Lineas.Descripcion, Lineas.Fase, obj.STEnvelope().ToString(), Lineas.Tension, Lineas.Alimentador FROM Elementos_Lineas INNER JOIN Lineas ON Elementos_Lineas.Id = Lineas.Elmt"
                                        pass
                                else:
                                    if self.liwElementos.selectedItems()[0].text() == 'Nodo':
                                        if self.cmbCampos.currentText() == "Geoname":
                                            strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt WHERE Nodos.Geoname = " + str(self.txtValor.text())
                                            pass
                                        if self.cmbCampos.currentText() == "Nombre":
                                            strSql = "SELECT TOP 300 Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt WHERE Nodos.Nombre LIKE '%" + str(self.txtValor.text()) + "%'"
                                            pass
                                        if self.cmbCampos.currentText() == "Descripción":
                                            strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Nodos.Descripcion As Descripción, obj.STEnvelope().ToString() FROM Nodos WHERE Nodos.Tension>0 AND Nodos.Descripcion LIKE '%" + str(self.txtValor.text()) + "%'"
                                            pass
                                        if str(self.txtValor.text())=="":
                                            strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt"
                                            pass
                                    else:
                                        #busco en el ItemData
                                        item  = self.liwElementos.selectedItems()[0]
                                        itemdata = str(item.data(QtCore.Qt.UserRole))
                                        if self.cmbCampos.currentText() == "Geoname":
                                            strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt WHERE Nodos.elmt=" + itemdata + " AND Nodos.Geoname = " + str(self.txtValor.text())
                                            pass
                                        if self.cmbCampos.currentText() == "Nombre":
                                            strSql = "SELECT TOP 300 Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt WHERE Nodos.elmt=" + itemdata + " AND Nodos.Nombre LIKE '%" + str(self.txtValor.text()) + "%'"
                                            pass
                                        if self.cmbCampos.currentText() == "Descripción":
                                            strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Nodos.Descripcion As Descripción, obj.STEnvelope().ToString() FROM Nodos WHERE Nodos.Tension>0 AND Nodos.elmt=" + itemdata + " AND Nodos.Descripcion LIKE '%" + str(self.txtValor.text()) + "%'"
                                            pass
                                        if str(self.txtValor.text())=="":
                                            strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt WHERE Nodos.elmt=" + itemdata
                                            pass

        cnn = self.conn
        cursor = cnn.cursor()
        #QMessageBox.information(None, 'EnerGis 5', 'sql: ' + str(strSql))
        cursor.execute(strSql)
        #convierto el cursor en array
        encontrados = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()
        
        self.tblResultado.setRowCount(0)
        if len(encontrados) > 0:
            self.tblResultado.setRowCount(len(encontrados))
            self.tblResultado.setColumnCount(len(encontrados[0]))
        for i in range (0, len(encontrados)):
            for j in range (len(encontrados[0])):
                item = QTableWidgetItem(str(encontrados[i][j]))
                self.tblResultado.setItem(i,j,item)

        self.tblResultado.setHorizontalHeaderLabels(encabezado)
        self.tblResultado.setColumnWidth(self.tblResultado.columnCount() - 1, 0)
    
    def elijo_item(self):
        #QMessageBox.information(None, 'EnerGis 5', self.tblResultado.selectedItems()[0].text())
        geom = QgsGeometry.fromWkt(self.tblResultado.selectedItems()[3].text())
        box = geom.buffer(25,1).boundingBox()
        self.mapCanvas.setExtent(box)
        self.mapCanvas.refresh()
