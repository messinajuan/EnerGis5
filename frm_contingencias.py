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
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QMessageBox
#from PyQt5 import QtCore
from PyQt5.QtCore import QDate
from PyQt5 import uic
from datetime import datetime

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_contingencias.ui'))

class frmContingencias (DialogType, DialogBase):

    def __init__(self, conn, mapCanvas):
        super().__init__()
        self.setupUi(self)
        self.mapCanvas=mapCanvas

        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self.setFixedSize(self.size())
        #self.mapCanvas = mapCanvas
        self.conn = conn

        self.txtResponsable.setText("SD")

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT * FROM Causas")
        #convierto el cursor en array
        self.causas = tuple(cursor)
        cursor.close()
        for i in range (0, len(self.causas)):
            self.cmbCausa.addItem(self.causas[i][2])

        self.cmbTipo.addItem('Aparato Maniobra MT')
        self.cmbTipo.addItem('Centro Transformación')
        self.cmbTipo.addItem('Aparato Maniobra BT')
        self.cmbTipo.addItem('Usuario')

        self.datFecha.setDate(QDate.currentDate())

        self.cmbTipoOperacion.addItem('Apertura')
        self.cmbTipoOperacion.addItem('Cierre')

        self.cmbTipoZona.addItem('Aerea')
        self.cmbTipoZona.addItem('Subterránea')

        self.cmbZona.addItem('Rural')
        self.cmbZona.addItem('Urbana')

        self.cmbListar.addItem('Fecha')
        self.cmbListar.addItem('Contingencia')
        self.cmbListar.addItem('Elemento')

        self.cmbTiempo.addItem('Bueno')
        self.cmbTiempo.addItem('Bueno - Ventoso')
        self.cmbTiempo.addItem('Lluvioso')
        self.cmbTiempo.addItem('Nublado - Posible lluvia')
        self.cmbTiempo.addItem('Tormenta Eléctrica')
        self.cmbTiempo.addItem('Ventoso')
        self.cmbTiempo.addItem('Ventoso - Lluvia')
        self.cmbTiempo.addItem('Ventoso - Lluvia - Descargas')

        self.seleccionado = -1

        cursor = cnn.cursor()
        cursor.execute("SELECT ult_cont FROM log_ope")
        ult_cont = tuple(cursor)
        cursor.close()
        self.ult_contingencia = ult_cont[0][0] + 1
        self.lblContingencia.setText(str(self.ult_contingencia))

        self.cmbListar.activated.connect(self.listar)
        self.cmdBuscar.clicked.connect(self.buscar)
        self.cmbTipoOperacion.activated.connect(self.cambiar_tipo_operacion)
        self.cmbCausa.activated.connect(self.cambiar_causa)

        self.cmdNuevaContingencia.clicked.connect(self.nueva_contingencia)
        self.cmdNuevoEvento.clicked.connect(self.nuevo_evento)
        self.cmdImportar.clicked.connect(self.importar)

        self.cmdEditar.clicked.connect(self.editar)
        self.cmdBorrar.clicked.connect(self.borrar)
        self.cmdGrabar.clicked.connect(self.grabar)
        self.cmdCancelar.clicked.connect(self.cancelar)

        self.cmdVerificar.clicked.connect(self.verificar)
        self.cmdSalir.clicked.connect(self.salir)

        self.tblLista.itemClicked.connect(self.elijo_elemento)

        self.frame.setEnabled(False)
        self.cmbListar.setCurrentIndex(0)
        self.listar()

    def listar(self):
        cnn = self.conn
        cursor = cnn.cursor()
        self.txtABuscar.setText("")
        if self.cmbListar.currentText()=='Fecha':
            cursor = cnn.cursor()
            cursor.execute("SELECT id, fechahora AS Fecha, CASE WHEN Importo_Operaciones.tipo=-1 THEN 'Apertura' ELSE 'Cierre' END AS Operacion, Contingencia, Tipo_Elemento, nombre AS Elemento, Motivo AS Causa, Elemento_Falla, Zona_Falla, Tipo_Zona_Falla, Est_Tiempo, Responsable, Observaciones FROM Importo_Operaciones INNER JOIN Causas ON Importo_Operaciones.Causa = Causas.Id_Causa WHERE validada=1 AND incorporada=0 ORDER BY fechahora, Importo_Operaciones.tipo, tipo_elemento, nombre")
            elementos = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            self.lleno_grilla(encabezado, elementos)

            #0:id
            #1:fecha
            #2:operacion
            #3:contingencia
            #4:Tipo_Elemento
            #5:nombreElemento
            #6:Causa
            #7:Elemento_Falla
            #8:Zona_Falla
            #9:Tipo_Zona_Falla
            #10:Est_Tiempo
            #11:Responsable
            #12:Observaciones

            #self.treEventos.clear()
            #if len(elementos) > 0:
            #    self.treEventos.setColumnCount(len(elementos[0]))
            #    self.treEventos.setHeaderLabels(encabezado)
            #    #primera clave
            #    fecha = '19000101'
            #    contingencia = 0
            #    nombre = ''
            #    items = []
            #    for i in range (0, len(elementos)):
            #        #QMessageBox.information(None, 'EnerGis 5', str(elementos[i][1])[:10].replace('-',''))
            #        dfecha = str(elementos[i][1])[:10].replace('-','')
            #        if dfecha!=fecha:
            #            fecha = str(elementos[i][1])[:10].replace('-','')
            #            contingencia = 0
            #            nombre = ''
            #            item_fecha = QTreeWidgetItem(fecha)
            #        else:
            #            if elementos[i][3]!=contingencia:
            #                contingencia=elementos[i][3]
            #                nombre = ''
            #                item_contingencia = QTreeWidgetItem([str(elementos[i][3])])
            #                item_fecha.addChild(item_contingencia)
            #            else:
            #                if elementos[i][5]!=nombre:
            #                    nombre=elementos[i][5]
            #                    item_nombre = QTreeWidgetItem([str(elementos[i][5])])
            #                    item_contingencia.addChild(item_nombre)
            #                else:
            #                    child = QTreeWidgetItem([elementos[i][2], elementos[i][4], elementos[i][6], elementos[i][7], elementos[i][8], elementos[i][10], elementos[i][11], elementos[i][12], elementos[i][0]])
            #                    item_nombre.addChild(child)

            #        items.append(item_fecha)
            #    self.treEventos.insertTopLevelItems(0, items)

        if self.cmbListar.currentText()=='Contingencia':
            cursor = cnn.cursor()
            cursor.execute("SELECT id, Contingencia, CASE WHEN Importo_Operaciones.tipo=-1 THEN 'Apertura' ELSE 'Cierre' END AS Operacion, fechahora AS Fecha, Tipo_Elemento, nombre AS Elemento, Motivo AS Causa, Elemento_Falla, Zona_Falla, Tipo_Zona_Falla, Est_Tiempo, Responsable, Observaciones FROM Importo_Operaciones INNER JOIN Causas ON Importo_Operaciones.Causa = Causas.Id_Causa WHERE validada=1 AND incorporada=0 ORDER BY contingencia, fechahora, Importo_Operaciones.tipo, tipo_elemento, nombre")
            elementos = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            self.lleno_grilla(encabezado, elementos)

        if self.cmbListar.currentText()=='Elemento':
            cursor = cnn.cursor()
            cursor.execute("SELECT id, Tipo_Elemento, nombre AS Elemento, CASE WHEN Importo_Operaciones.tipo=-1 THEN 'Apertura' ELSE 'Cierre' END AS Operacion, Contingencia, fechahora AS Fecha, Motivo AS Causa, Elemento_Falla, Zona_Falla, Tipo_Zona_Falla, Est_Tiempo, Responsable, Observaciones FROM Importo_Operaciones INNER JOIN Causas ON Importo_Operaciones.Causa = Causas.Id_Causa WHERE validada=1 AND incorporada=0 ORDER BY tipo_elemento, nombre, Importo_Operaciones.tipo")
            elementos = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            self.lleno_grilla(encabezado, elementos)
        pass

    def buscar(self):
        cnn = self.conn
        cursor = cnn.cursor()
        if self.cmbListar.currentText()=='Fecha':
            cursor = cnn.cursor()
            cursor.execute("SELECT id, fechahora AS Fecha, CASE WHEN Importo_Operaciones.tipo=-1 THEN 'Apertura' ELSE 'Cierre' END AS Operacion, Contingencia, Tipo_Elemento, nombre AS Elemento, Motivo AS Causa, Elemento_Falla, Zona_Falla, Tipo_Zona_Falla, Est_Tiempo, Responsable, Observaciones FROM Importo_Operaciones INNER JOIN Causas ON Importo_Operaciones.Causa = Causas.Id_Causa WHERE validada=1 AND incorporada=0 AND nombre LIKE '%" + self.txtABuscar.text() + "%' ORDER BY fechahora, Importo_Operaciones.tipo, tipo_elemento, nombre")
            elementos = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            self.lleno_grilla(encabezado, elementos)

            #0:id
            #1:fecha
            #2:operacion
            #3:contingencia
            #4:Tipo_Elemento
            #5:nombreElemento
            #6:Causa
            #7:Elemento_Falla
            #8:Zona_Falla
            #9:Tipo_Zona_Falla
            #10:Est_Tiempo
            #11:Responsable
            #12:Observaciones

            #self.treEventos.clear()
            #if len(elementos) > 0:
            #    self.treEventos.setColumnCount(len(elementos[0]))
            #    self.treEventos.setHeaderLabels(encabezado)
            #    #primera clave
            #    fecha = '19000101'
            #    contingencia = 0
            #    nombre = ''
            #    items = []
            #    for i in range (0, len(elementos)):
            #        #QMessageBox.information(None, 'EnerGis 5', str(elementos[i][1])[:10].replace('-',''))
            #        dfecha = str(elementos[i][1])[:10].replace('-','')
            #        if dfecha!=fecha:
            #            fecha = str(elementos[i][1])[:10].replace('-','')
            #            contingencia = 0
            #            nombre = ''
            #            item_fecha = QTreeWidgetItem(fecha)
            #        else:
            #            if elementos[i][3]!=contingencia:
            #                contingencia=elementos[i][3]
            #                nombre = ''
            #                item_contingencia = QTreeWidgetItem([str(elementos[i][3])])
            #                item_fecha.addChild(item_contingencia)
            #            else:
            #                if elementos[i][5]!=nombre:
            #                    nombre=elementos[i][5]
            #                    item_nombre = QTreeWidgetItem([str(elementos[i][5])])
            #                    item_contingencia.addChild(item_nombre)
            #                else:
            #                    child = QTreeWidgetItem([elementos[i][2], elementos[i][4], elementos[i][6], elementos[i][7], elementos[i][8], elementos[i][10], elementos[i][11], elementos[i][12], elementos[i][0]])
            #                    item_nombre.addChild(child)

            #        items.append(item_fecha)
            #    self.treEventos.insertTopLevelItems(0, items)

        if self.cmbListar.currentText()=='Contingencia':
            cursor = cnn.cursor()
            cursor.execute("SELECT id, Contingencia, CASE WHEN Importo_Operaciones.tipo=-1 THEN 'Apertura' ELSE 'Cierre' END AS Operacion, fechahora AS Fecha, Tipo_Elemento, nombre AS Elemento, Motivo AS Causa, Elemento_Falla, Zona_Falla, Tipo_Zona_Falla, Est_Tiempo, Responsable, Observaciones FROM Importo_Operaciones INNER JOIN Causas ON Importo_Operaciones.Causa = Causas.Id_Causa WHERE validada=1 AND incorporada=0 AND nombre LIKE '%" + self.txtABuscar.text() + "%' ORDER BY contingencia, fechahora, Importo_Operaciones.tipo, tipo_elemento, nombre")
            elementos = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            self.lleno_grilla(encabezado, elementos)

        if self.cmbListar.currentText()=='Elemento':
            cursor = cnn.cursor()
            cursor.execute("SELECT id, Tipo_Elemento, nombre AS Elemento, CASE WHEN Importo_Operaciones.tipo=-1 THEN 'Apertura' ELSE 'Cierre' END AS Operacion, Contingencia, fechahora AS Fecha, Motivo AS Causa, Elemento_Falla, Zona_Falla, Tipo_Zona_Falla, Est_Tiempo, Responsable, Observaciones FROM Importo_Operaciones INNER JOIN Causas ON Importo_Operaciones.Causa = Causas.Id_Causa WHERE validada=1 AND incorporada=0 AND nombre LIKE '%" + self.txtABuscar.text() + "%' ORDER BY tipo_elemento, nombre, Importo_Operaciones.tipo")
            elementos = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            self.lleno_grilla(encabezado, elementos)
        pass

    def elijo_elemento(self):
        self.seleccionado = self.tblLista.currentRow()
        self.lblEvento.setText(self.tblLista.item(self.seleccionado,0).text())
        for i in range (0, self.tblLista.columnCount()):
            #i = self.tblLista.currentColumn()
            valor = self.tblLista.item(self.seleccionado,i).text()
            if self.tblLista.horizontalHeaderItem(i).text() == 'Contingencia':
                self.id_contingencia = valor
                self.lblContingencia.setText(str(self.id_contingencia))
            if self.tblLista.horizontalHeaderItem(i).text() == 'Tipo_Elemento':
                self.cmbTipo.setCurrentText(valor)
            if self.tblLista.horizontalHeaderItem(i).text() == 'Elemento':
                self.txtNombre.setText(valor)
            if self.tblLista.horizontalHeaderItem(i).text() == 'Operacion':
                self.cmbTipoOperacion.setCurrentText(valor)
            if self.tblLista.horizontalHeaderItem(i).text() == 'Fecha':
                date = datetime.strptime(valor, '%Y-%m-%d %H:%M:%S')
                self.datFecha.setDate(date)
                self.timHora.setTime(date.time())
            if self.tblLista.horizontalHeaderItem(i).text() == 'Causa':
                self.cmbCausa.setCurrentText(valor)

            self.id_causa = self.cmbCausa.currentIndex()
            self.setear_elemento_falla()

            if self.tblLista.horizontalHeaderItem(i).text() == 'Elemento_Falla':
                for j in range (0, len(self.tipo_instalacion)):
                    if str(self.tipo_instalacion[j][0]) == str(valor):
                        self.cmbTipoInstalacion.setCurrentIndex(j)

            if self.tblLista.horizontalHeaderItem(i).text() == 'Zona_Falla':
                self.cmbZona.setCurrentText(valor)
            if self.tblLista.horizontalHeaderItem(i).text() == 'Tipo_Zona_Falla':
                self.cmbTipoZona.setCurrentText(valor)
            if self.tblLista.horizontalHeaderItem(i).text() == 'Est_Tiempo':
                self.cmbTiempo.setCurrentText(valor)
            if self.tblLista.horizontalHeaderItem(i).text() == 'Responsable':
                self.txtResponsable.setText(valor)
            if self.tblLista.horizontalHeaderItem(i).text() == 'Observaciones':
                self.txtObservaciones.setText(valor)


        self.cmdEditar.setEnabled(True)
        self.cmdBorrar.setEnabled(True)
        self.cmdGrabar.setEnabled(False)
        self.cmdCancelar.setEnabled(False)
        pass

    def cambiar_tipo_operacion(self):
        self.id_causa = self.cmbCausa.currentIndex()
        self.setear_elemento_falla()

    def cambiar_causa(self):
        self.id_causa = self.cmbCausa.currentIndex()
        self.setear_elemento_falla()

    def setear_elemento_falla(self):
        tipo_falla = self.causas[self.id_causa][5]

        if self.cmbTipoOperacion.currentText()=="Apertura":
            self.tipo_instalacion = [[701,'ET AT/MT'],
            [702,'CD MT'],
            [703,'SE MT/BT'],
            [704,'LMT'],
            [705,'LBT'],
            [706,'Caja Esquinera/Buzón'],
            [707,'Acometida Domiciliaria'],
            [708,'Cliente'],
            [709,'Alumbrado']]

            self.cmbTipoInstalacion.clear()
            for i in range (0, len(self.tipo_instalacion)):
                self.cmbTipoInstalacion.addItem(self.tipo_instalacion[i][1])

            if self.cmbTipo.currentText() == "Usuario":
                self.cmbTipoInstalacion.setCurrentIndex(7)
            if self.cmbTipo.currentText() == "Aparato Maniobra BT":
                self.cmbTipoInstalacion.setCurrentIndex(4)
            if self.cmbTipo.currentText() == "Aparato Maniobra MT":
                self.cmbTipoInstalacion.setCurrentIndex(3)
            if self.cmbTipo.currentText() == "Centro Transformación":
                self.cmbTipoInstalacion.setCurrentIndex(2)

        else:
            self.tipo_instalacion = [[707903,'Acometida Domiciliaria - Cortado'],
            [707901,'Acometida Domiciliaria - Cortocircuito'],
            [707905,'Acometida Domiciliaria - Desatado'],
            [707904,'Acometida Domiciliaria - Deshilachado'],
            [707907,'Acometida Domiciliaria - Erosionado/Sulfatado'],
            [707910,'Acometida Domiciliaria - Flojo/a'],
            [707911,'Acometida Domiciliaria - Normal'],
            [707908,'Acometida Domiciliaria - Quemado'],
            [707916,'Acometida Domiciliaria - Robo'],
            [709901,'Alumbrado - Cortocircuito'],
            [709907,'Alumbrado - Erosionado/Sulfatado'],
            [709910,'Alumbrado - Flojo/a'],
            [709911,'Alumbrado - Normal'],
            [709908,'Alumbrado - Quemado'],
            [709916,'Alumbrado - Robo'],
            [709906,'Alumbrado - Roto/a'],
            [706901,'Caja Esquinera/Buzón - Cortocircuito'],
            [706911,'Caja Esquinera/Buzón - Normal'],
            [706908,'Caja Esquinera/Buzón - Quemado'],
            [706906,'Caja Esquinera/Buzón - Roto/a'],
            [702901,'CD MT - Cortocircuito'],
            [702913,'CD MT - Falla Interna'],
            [702401912,'CD MT - Interruptor MT - Abierto'],
            [702401913,'CD MT - Interruptor MT - Falla Interna'],
            [702401908,'CD MT - Interruptor MT - Quemado'],
            [702911,'CD MT - Normal'],
            [702916,'CD MT - Robo'],
            [708913,'Cliente - Falla Interna'],
            [708911,'Cliente - Normal'],
            [701901,'ET AT/MT - Cortocircuito'],
            [701913,'ET AT/MT - Falla Interna'],
            [701401912,'ET AT/MT - Interruptor MT - Abierto'],
            [701401913,'ET AT/MT - Interruptor MT - Falla Interna'],
            [701401908,'ET AT/MT - Interruptor MT - Quemado'],
            [701911,'ET AT/MT - Normal'],
            [705903,'LBT - Cortado'],
            [705901,'LBT - Cortocircuito'],
            [705905,'LBT - Desatado'],
            [705904,'LBT - Deshilachado'],
            [705911,'LBT - Normal'],
            [705908,'LBT - Quemado'],
            [705916,'LBT - Robo'],
            [705906,'LBT - Roto/a'],
            [704903,'LMT - Cortado'],
            [704901,'LMT - Cortocircuito'],
            [704905,'LMT - Desatado'],
            [704904,'LMT - Deshilachado'],
            [701401912,'LMT - Interruptor MT - Abierto'],
            [701401913,'LMT - Interruptor MT - Falla Interna'],
            [704401908,'LMT - Interruptor MT - Quemado'],
            [704403908,'LMT - Reconectador MT - Quemado'],
            [704404908,'LMT - Seccionalizador MT - Quemado'],
            [704402908,'LMT - Seccionador MT - Quemado'],
            [704413908,'LMT - Fusible MT - Quemado'],
            [704911,'LMT - Normal'],
            [704916,'LMT - Robo'],
            [704906,'LMT - Roto/a'],
            [703901,'SE MT/BT - Cortocircuito'],
            [703913,'SE MT/BT - Falla Interna'],
            [703908,'SE MT/BT - Quemado'],
            [703911,'SE MT/BT - Normal'],
            [703916,'SE MT/BT - Robo'],
            [703906,'SE MT/BT - Roto/a']]

            self.cmbTipoInstalacion.clear()
            for i in range (0, len(self.tipo_instalacion)):
                self.cmbTipoInstalacion.addItem(self.tipo_instalacion[i][1])

            if self.cmbTipo.currentText() == "Usuario":
                codigo = 708
            if self.cmbTipo.currentText() == "Aparato Maniobra BT":
                codigo = 705
            if self.cmbTipo.currentText() == "Aparato Maniobra MT":
                codigo = 704
            if self.cmbTipo.currentText() == "Centro Transformación":
                codigo = 703

            for i in range (0, len(self.cmbTipoInstalacion)):
                if str(self.tipo_instalacion[i][0])[:3] == str(codigo):
                    self.cmbTipoInstalacion.setCurrentIndex(i)

            for i in range (0, len(self.cmbTipoInstalacion)):
                if str(self.tipo_instalacion[i][0])[:3] == str(codigo) and str(self.tipo_instalacion[i][0])[-3:] == str(tipo_falla):
                    self.cmbTipoInstalacion.setCurrentIndex(i)

    def verificar(self):
        cnn = self.conn
        advertencias =[]

        #analizo que esten los elementos en el mapa
        cursor = cnn.cursor()
        cursor.execute("SELECT DISTINCT nombre FROM Importo_Operaciones where incorporada=0 AND tipo_elemento<>'Usuario' AND nombre NOT IN (SELECT nombre FROM nodos WHERE Nodos.Tension>0 AND elmt=2 OR elmt=3)")
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            linea=[]
            linea.append("Error")
            linea.append("No se encuentra en el plano el aparato: " + rs[0])
            advertencias.append (linea)

        #analizo que esten los usuarios
        cursor = cnn.cursor()
        cursor.execute("SELECT DISTINCT nombre FROM Importo_Operaciones where incorporada=0 AND tipo_elemento='Usuario' AND nombre NOT IN (SELECT id_usuario FROM usuarios)")
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            linea=[]
            linea.append("Error")
            linea.append("No se encuentra en el plano el usuario: " + str(rs[0]))
            advertencias.append (linea)

        #analizo si hay una apertura y cierre a la misma hora
        cursor = cnn.cursor()
        cursor.execute("SELECT nombre, fechahora, tipo_elemento, Count(tipo) AS cant, Min(id) AS Id FROM Importo_Operaciones GROUP BY nombre, fechahora, tipo_elemento HAVING Count(tipo)>1")
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            linea=[]
            linea.append("Advertencia")
            linea.append("El elemento " + rs[2] + ": " + rs[0] + " tiene cargados " + str(rs[3]) + " eventos para un mismo instante: " + str(rs[1]))
            advertencias.append (linea)

        #analizo si hay una apertura y cierre a la misma hora
        cursor = cnn.cursor()
        cursor.execute("SELECT nombre, count(*), SUM(tipo) FROM Importo_Operaciones where incorporada=0 AND tipo_elemento = 'Usuario' GROUP BY nombre HAVING count(*)/2<> -1*SUM(tipo)")
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            linea=[]
            linea.append("Advertencia")
            linea.append("El usuario " + str(rs[0]) + " tiene eventos faltantes")
            advertencias.append (linea)

        #analizo aperturas y cierres
        tmin = 10000
        tmax = 0
        cursor = cnn.cursor()
        cursor.execute("SELECT nombre, tipo, fechahora, tipo_elemento FROM Importo_Operaciones where incorporada=0 AND tipo_elemento<>'Usuario' ORDER BY nombre, fechahora")
        rst = tuple(cursor)
        cursor.close()
        nombre = ''
        estado = ''
        amin = ''
        amax = ''
        for rs in rst:
            if rs[0] == nombre: #es el mismo aparato
                if rs[1] == estado: #se repite
                    if estado == -1:
                        QMessageBox.information(None, 'EnerGis 5', "El aparato: " + rs[0] + " tiene 2 aperturas seguidas - " + str(rs[3]))
                    else:
                        QMessageBox.information(None, 'EnerGis 5', "El aparato: " + rs[0] + " tiene 2 cierres seguidos - " + str(rs[3]))

                        cursor = cnn.cursor()
                        QMessageBox.information(None, 'EnerGis 5', str(rs[3]))
                        cursor.execute("SELECT nombre, apertura, causa, contingencia, responsable, elemento_falla, est_tiempo, zona_falla, tipo_zona_falla, tipo_elemento FROM VW_GISCIERRESRECLAMOS WHERE nombre='" + rs[0] + "' AND cierre = '" + str(rs[3]) + "' ORDER BY cierre")
                        rst2 = tuple(cursor)
                        cursor.close()

                        if len(rst2) > 0:
                            reply = QMessageBox.question(None, 'EnerGis 5', 'Desea cargar la apertura a la fecha y hora del reclamo ?', QMessageBox.Yes, QMessageBox.No)
                            if reply == QMessageBox.Yes:
                                str_valores = "'" + rst2[0][0] + "',"
                                str_valores = str_valores + "-1,"
                                str_valores = str_valores + "'" + rst2[0][1] + "',"
                                str_valores = str_valores + rst2[0][2] + ","
                                str_valores = str_valores + str(rst2[0][3]) + ","
                                str_valores = str_valores + "'" + rst2[0][4] + "',"
                                str_valores = str_valores + "'" + rst2[0][5] + "',"
                                str_valores = str_valores + "'ape.aut.',"
                                str_valores = str_valores + rst2[0][5] + "',"
                                str_valores = str_valores + rst2[0][6] + "',"
                                str_valores = str_valores + rst2[0][7] + "',"
                                str_valores = str_valores + rst2[0][8] + "',"
                                str_valores = str_valores + "0,"
                                str_valores = str_valores + "99" + "," #codigo_usuario
                                str_valores = str_valores + "0"
                                cursor = cnn.cursor()
                                try:
                                    cursor.execute("INSERT INTO Importo_Operaciones (nombre,tipo,fechahora,causa,contingencia,responsable,est_tiempo,observaciones,elemento_falla,zona_falla,tipo_zona_falla,tipo_elemento,incorporada,usuario,validada) VALUES (" + str_valores + ")")
                                    cnn.commit()
                                except:
                                    cnn.rollback()
                                    QMessageBox.information(None, 'EnerGis 5', "No se pudieron insertar Contingencias !")
                                pass
            else: #es un nuevo aparato
                #me fijo si empieza con apertura o cierre
                estado_inicial = rs[1]
                if rs[3] == "Aparato Maniobra BT" or rs[3] == "Aparato Maniobra MT":
                    cursor = cnn.cursor()
                    #QMessageBox.information(None, 'EnerGis 5', str(rs[3]))
                    cursor.execute("SELECT elmt, estado FROM nodos WHERE Nodos.Tension>0 AND nombre='" + rs[0])
                    rst2 = tuple(cursor)
                    cursor.close()
                    if estado_inicial == 0 and rst2[0][0] == 2:
                        linea=[]
                        linea.append("Advertencia")
                        linea.append("La maniobra para el aparato NC " + rs[0] + ", comienza con un cierre. El " + str(rs[1]))
                        advertencias.append (linea)

                    if estado_inicial == -1 and rst2[0][0] == 3:
                        linea=[]
                        linea.append("Advertencia")
                        linea.append("La maniobra para el aparato NA " + rs[0] + ", comienza con una apertura. El " + str(rs[1]))
                        advertencias.append (linea)


                if rs[3] == "Transformador":
                    if estado_inicial == 0:
                        linea=[]
                        linea.append("Advertencia")
                        linea.append("La maniobra para el Ct " + rs[0] + ", comienza con un cierre. El " + str(rs[1]))
                        advertencias.append (linea)
            nombre = rs[0]
            estado = rs[1]
            if estado == estado_inicial:
                tini = rs[2]
            else:
                tfin = rs[2]
                if tini == tfin:
                    linea=[]
                    linea.append("Error")
                    linea.append("Elemento: " + nombre + ". El cierre y la apertura se suceden al mismo instante: " + str(tini))
                    advertencias.append (linea)
                else:
                    dt = (tfin - tini).seconds / 3600
                    #QMessageBox.information(None, 'EnerGis 5', str(dt))
                    if dt < tmin:
                        tmin = dt
                        amin = rs[3] + " " + rs[0]
                    if dt > tmax:
                        tmax = dt
                        amax = rs[3] + " " + rs[0]

        cursor = cnn.cursor()
        cursor.execute("SELECT Importo_Operaciones.nombre, Importo_Operaciones.fechahora FROM (Importo_Operaciones INNER JOIN (SELECT nombre, MIN(fechahora) AS fecha FROM Importo_Operaciones AS Importo_Operaciones_1 GROUP BY nombre) AS A ON (Importo_Operaciones.fechahora = A.fecha) AND (Importo_Operaciones.nombre = A.nombre)) INNER JOIN Nodos ON A.nombre = Nodos.Nombre WHERE incorporada=0 AND tipo_elemento<>'Usuario' AND ((Importo_Operaciones.tipo = - 1 AND Nodos.Elmt = 3) OR (Importo_Operaciones.tipo = 0 AND Nodos.Elmt = 2))")
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            linea=[]
            linea.append("Advertencia")
            linea.append("No coincide el estado normal del seccionador " + rs[0] + " con la maniobra. El " + str(rs[1]))
            advertencias.append (linea)

        #analizo entrada y salida de usuarios
        cursor = cnn.cursor()
        cursor.execute("SELECT nombre, tipo, fechahora FROM Importo_Operaciones where incorporada=0 AND tipo_elemento='Usuario' ORDER BY nombre, fechahora")
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            if rs[0] == nombre: #es el mismo usuario
                if estado == rs[1]: #se repite
                    if estado == -1:
                        QMessageBox.information(None, 'EnerGis 5', "El usuario: " + rs[0] + " tiene 2 salidas seguidas - " + str(rs[2]))
                    else:
                        QMessageBox.information(None, 'EnerGis 5', "El usuario: " + rs[0] + " tiene 2 entradas seguidas - " + str(rs[2]))

                        cursor = cnn.cursor()
                        QMessageBox.information(None, 'EnerGis 5', str(rs[3]))
                        cursor.execute("SELECT nombre, apertura, causa, contingencia, responsable, elemento_falla, est_tiempo, zona_falla, tipo_zona_falla, tipo_elemento FROM VW_GISCIERRESRECLAMOS WHERE tipo_elemento='Usuario' AND nombre='" + rs[0] + "' AND cierre = '" + str(rs[3]) + "' ORDER BY cierre")
                        rst2 = tuple(cursor)
                        cursor.close()

                        if len(rst2) > 0:
                            reply = QMessageBox.question(None, 'EnerGis 5', 'Desea cargar la apertura a la fecha y hora del reclamo ?', QMessageBox.Yes, QMessageBox.No)
                            if reply == QMessageBox.Yes:
                                str_valores = "'" + rst2[0][0] + "',"
                                str_valores = str_valores + "-1,"
                                str_valores = str_valores + "'" + rst2[0][1] + "',"
                                str_valores = str_valores + rst2[0][2] + ","
                                str_valores = str_valores + str(rst2[0][3]) + ","
                                str_valores = str_valores + "'" + rst2[0][4] + "',"
                                str_valores = str_valores + "'" + rst2[0][5] + "',"
                                str_valores = str_valores + "'ape.aut.',"
                                str_valores = str_valores + rst2[0][5] + "',"
                                str_valores = str_valores + rst2[0][6] + "',"
                                str_valores = str_valores + rst2[0][7] + "',"
                                str_valores = str_valores + rst2[0][8] + "',"
                                str_valores = str_valores + "0,"
                                str_valores = str_valores + "99" + "," #codigo_usuario
                                str_valores = str_valores + "0"
                                cursor = cnn.cursor()
                                try:
                                    cursor.execute("INSERT INTO Importo_Operaciones (nombre,tipo,fechahora,causa,contingencia,responsable,est_tiempo,observaciones,elemento_falla,zona_falla,tipo_zona_falla,tipo_elemento,incorporada,usuario,validada) VALUES (" + str_valores + ")")
                                    cnn.commit()
                                except:
                                    cnn.rollback()
                                    QMessageBox.information(None, 'EnerGis 5', "No se pudieron insertar Contingencias !")
                                pass
                    return

            else: #es un nuevo usuario
                #me fijo si empieza con apertura o cierre
                estado_inicial = rs[1]
                if estado_inicial == 0:
                    linea=[]
                    linea.append("Advertencia")
                    linea.append("Para el usuario: " + str(rs[0]) + " la maniobra comienza con un cierre. El " + str(rs[2]))
                    advertencias.append (linea)

            nombre = rs[0]
            estado = rs[1]
            if estado == estado_inicial:
                tini = rs[2]
            else:
                tfin = rs[2]

                dt = (tfin - tini).seconds / 3600
                if dt < tmin:
                    tmin = dt
                    amin = rs[3] + " " + rs[0]
                if dt > tmax:
                    tmax = dt
                    amax = rs[3] + " " + rs[0]

        if len(advertencias[0])> 0:
            #QMessageBox.information(None, 'EnerGis 5', str(advertencias))

            encabezado = ["Tipo", "Descripción"]

            from .frm_lista import frmLista
            self.dialogo = frmLista(self.mapCanvas, encabezado, advertencias)
            self.dialogo.setWindowTitle('Resultados Verificación')
            self.dialogo.resize(900,self.dialogo.height())
            self.dialogo.show()

            return

        QMessageBox.information(None, 'EnerGis 5', "El mayor tiempo de interrupción es de " + str(format(tmax, ".2f")) + " hs. (" + amax + ") y el mínimo es de " + str(format(tmin, ".2f")) + " hs. (" + amin + ")")
        QMessageBox.information(None, 'EnerGis 5', "Contingencias cargadas correctamente !")

    def importar(self):
        cnn = self.conn
        ult_rec = 0
        try:
            cursor = cnn.cursor()
            cursor.execute("SELECT orden_atencion, id_reclamo, nombre, tipo, causa, fechahora, responsable, est_tiempo, observaciones, elemento_falla, zona_falla, tipo_zona_falla, tipo_elemento FROM VW_GISCONTINGENCIAS ORDER BY nombre, fechahora")
            rst = tuple(cursor)
            cursor.close()
            for rs in rst:
                if rs[0] == 0:
                    ultimo_reclamo = rs[1]
                else:
                    ultimo_reclamo = rs[0]

                if ultimo_reclamo != ult_rec:
                    cnn = self.conn
                    cnn.autocommit = False
                    cursor = cnn.cursor()
                    cursor.execute("SELECT ult_cont FROM log_ope")
                    ult_cont = tuple(cursor)
                    self.ult_contingencia = ult_cont[0][0] + 1
                    cursor.execute("UPDATE ult_cont SET ult_cont =" + str(self.ult_contingencia))
                    cnn.commit()
                    ult_rec = ultimo_reclamo

                str_valores = "'" + rs[2].replace(" ","") + "',"
                str_valores = str_valores + rs[3] + ","
                str_valores = str_valores + "'" + rs[4] + "',"
                str_valores = str_valores + str(rs[5]) + ","
                str_valores = str_valores + ult_cont + ","
                str_valores = str_valores + "'" + rs[6] + "',"
                str_valores = str_valores + "'" + rs[7] + "',"
                str_valores = str_valores + "'" + rs[8] + "',"
                str_valores = str_valores + str(rs[9]) + ","
                str_valores = str_valores + "'" + rs[10] + "',"
                str_valores = str_valores + "'" + rs[12] + "',"
                str_valores = str_valores + "'" + rs[12] + "',"
                str_valores = str_valores + "0,"
                str_valores = str_valores + "99," #Codigo_Usuario
                str_valores = str_valores + "0"

                cursor = cnn.cursor()
                try:
                    cursor.execute("INSERT INTO Importo_Operaciones (nombre,tipo,fechahora,causa,contingencia,responsable,est_tiempo,observaciones,elemento_falla,zona_falla,tipo_zona_falla,tipo_elemento,incorporada,usuario,validada) VALUES (" + str_valores + ")")
                    cnn.commit()
                except:
                    cnn.rollback()
                    QMessageBox.information(None, 'EnerGis 5', "No se pudieron insertar Contingencias !")
                pass

                if rs[0] == 0:
                    cursor = cnn.cursor()
                    try:
                        cursor.execute("INSERT INTO Reclamos_Contingencias (id_contingencia,id_reclamo) VALUES (" + ult_cont + "," + str(rs[1]) + ")")
                        cnn.commit()
                    except:
                        cnn.rollback()
                        QMessageBox.information(None, 'EnerGis 5', "No se pudieron insertar Reclamos !")
                    pass
                else:
                    cursor = cnn.cursor()
                    try:
                        cursor.execute("INSERT INTO Reclamos_Contingencias SELECT " + self.ult_contingencia + " AS id_contingencia,id AS id_reclamo FROM VW_GISRECLAMOS INNER JOIN VW_GISCONTINGENCIAS ON VW_GISRECLAMOS.orden_atencion = VW_GISCONTINGENCIAS.orden_atencion WHERE VW_GISRECLAMOS.orden_atencion <> 0 AND VW_GISCONTINGENCIAS.orden_atencion = " + str(rs[0]))
                        cnn.commit()
                    except:
                        cnn.rollback()
                        QMessageBox.information(None, 'EnerGis 5', "No se pudieron insertar Reclamos !")
                    pass
                self.lblContingencia.setText(ult_cont)
        except:
            pass
    def nueva_contingencia(self):
        self.id_contingencia = self.ult_contingencia + 1
        self.lblContingencia.setText(str(self.id_contingencia))
        self.frame.setEnabled(True)
        self.cmdEditar.setEnabled(False)
        self.cmdBorrar.setEnabled(False)
        self.cmdGrabar.setEnabled(True)
        self.cmdCancelar.setEnabled(True)
        self.tblLista.setEnabled(False)

    def nuevo_evento(self):
        self.lblEvento.setText("<Automatico>")
        self.frame.setEnabled(True)
        self.cmdEditar.setEnabled(False)
        self.cmdBorrar.setEnabled(False)
        self.cmdGrabar.setEnabled(True)
        self.cmdCancelar.setEnabled(True)
        self.tblLista.setEnabled(False)

    def editar(self):
        self.frame.setEnabled(True)
        self.cmdEditar.setEnabled(False)
        self.cmdGrabar.setEnabled(True)
        self.cmdBorrar.setEnabled(False)
        self.cmdCancelar.setEnabled(True)
        self.tblLista.setEnabled(False)
        if self.seleccionado!=-1:
            self.tblLista.selectRow(self.seleccionado)

    def borrar(self):
        cnn = self.conn
        reply = QMessageBox.question(None, 'EnerGis 5', 'Desea borrar el evento ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
                return

        cursor = cnn.cursor()
        try:
            cursor.execute("DELETE FROM Importo_Operaciones WHERE id=" + str(self.lblEvento.text()))
            cnn.commit()
            QMessageBox.information(None, 'EnerGis 5', 'Borrado !')
            self.listar()
        except:
            cnn.rollback()
            QMessageBox.information(None, 'EnerGis 5', "No se pudo Borrar !")
        pass

    def cancelar(self):
        self.frame.setEnabled(False)
        self.cmdEditar.setEnabled(False)
        self.cmdBorrar.setEnabled(False)
        self.cmdGrabar.setEnabled(False)
        self.tblLista.setEnabled(True)
        if self.seleccionado!=-1:
            self.tblLista.selectRow(self.seleccionado)
        self.lblEvento.setText("<Automatico>")
        pass

    def grabar(self):
        cnn = self.conn

        reply = QMessageBox.question(None, 'EnerGis 5', 'Desea grabar ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
                return

        if self.cmbTipo.currentText() == "Aparato Maniobra MT":
            tipo_elemento = "Elem_ManiobraMT"
        if self.cmbTipo.currentText() == "Centro Transformación":
            tipo_elemento = "Transformador"
        if self.cmbTipo.currentText() == "Aparato Maniobra BT":
            tipo_elemento = "Elem_ManiobraBT"
        if self.cmbTipo.currentText() == "Usuario":
            tipo_elemento = "Usuario"
        if self.txtNombre.text() == "":
            QMessageBox.information(None, 'EnerGis 5', "Falta el código del " + self.cmbTipo.currentText())
            return
        if self.cmbCausa.currentText() == "":
            QMessageBox.information(None, 'EnerGis 5', "Causa erronea")
            return
        if self.txtResponsable.text() == "":
            QMessageBox.information(None, 'EnerGis 5', "Responsable erroneo")
            return
        if self.cmbTiempo.currentText() == "":
            QMessageBox.information(None, 'EnerGis 5', "Falta estado del Tiempo")
            return
        if self.txtObservaciones.toPlainText() == "":
            self.txtObservaciones.setText("<SD>")
        self.txtObservaciones.setText(self.txtObservaciones.toPlainText().replace(chr(9)," "))
        self.txtObservaciones.setText(self.txtObservaciones.toPlainText().replace(chr(10)," "))
        self.txtObservaciones.setText(self.txtObservaciones.toPlainText().replace(chr(13)," "))

        zona_falla = self.cmbZona.currentText()[:1]
        tipo_zona_falla = self.cmbTipoZona.currentText()[:1]

        if self.cmbTipoInstalacion.currentText() == "":
            QMessageBox.information(None, 'EnerGis 5', "Debe escoger una instalación !")
            return

        for i in range (0, len(self.tipo_instalacion)):
            if self.cmbTipoInstalacion.currentText()==self.tipo_instalacion[i][1]:
                elemento_falla=str(self.tipo_instalacion[i][0])[:3]

        if self.cmbTipoOperacion.currentText()=="Apertura":
            tipo_operacion = -1
        else:
            tipo_operacion = 0

        fechahora = str(self.datFecha.date().toPyDate()).replace('-','') + ' ' + str(self.timHora.time().toPyTime())

        for i in range (0, len(self.causas)):
            if self.cmbCausa.currentText()==self.causas[i][2]:
                causa = self.causas[i][0]

        cursor = cnn.cursor()
        if self.lblEvento.text()=="<Automatico>":
            try:
                cursor.execute("INSERT INTO Importo_Operaciones (nombre,tipo,fechahora,causa,contingencia,responsable,est_tiempo,observaciones,elemento_falla,tipo_elemento,zona_falla,tipo_zona_falla,incorporada,usuario,validada) VALUES ('" + self.txtNombre.text() + "'," + str(tipo_operacion) + ",'" + fechahora + "'," +  str(causa) + "," + str(self.id_contingencia) + ",'" + self.txtResponsable.text() + "','" + self.cmbTiempo.currentText() + "','" + self.txtObservaciones.toPlainText() + "'," + str(elemento_falla) + ",'" + tipo_elemento + "','" + zona_falla + "','" + tipo_zona_falla + "',0," + "99" + ",0)")
                cnn.commit()
                QMessageBox.information(None, 'EnerGis 5', 'Grabado !')
            except:
                cnn.rollback()
                QMessageBox.information(None, 'EnerGis 5', "No se pudo grabar en la Base de Datos !")
        else:
            try:
                cursor.execute("UPDATE Importo_Operaciones SET nombre='" + self.txtNombre.text() + "',tipo=" + str(tipo_operacion) + ",fechahora='" + fechahora + "',causa=" +  str(causa) + ",contingencia=" + str(self.id_contingencia) + ",responsable='" + self.txtResponsable.text() + "',est_tiempo='" + self.cmbTiempo.currentText() + "',observaciones='" + self.txtObservaciones.toPlainText() + "',elemento_falla=" + str(elemento_falla) + ",tipo_elemento='" + tipo_elemento + "',zona_falla='" + zona_falla + "',tipo_zona_falla = '" + tipo_zona_falla + "' WHERE id=" + self.lblEvento.text())
                cnn.commit()
                QMessageBox.information(None, 'EnerGis 5', 'Grabado !')
            except:
                cnn.rollback()
                QMessageBox.information(None, 'EnerGis 5', "No se pudo grabar en la Base de Datos !")

        self.cancelar()
        self.listar()
        if self.seleccionado!=-1:
            self.tblLista.selectRow(self.seleccionado)
        pass

    def lleno_grilla(self, encabezado, elementos):
        self.tblLista.setRowCount(0)
        if len(elementos) > 0:
            self.tblLista.setRowCount(len(elementos))
            self.tblLista.setColumnCount(len(elementos[0]))
        for i in range (0, len(elementos)):
            for j in range (len(elementos[0])):
                item = QTableWidgetItem(str(elementos[i][j]))
                self.tblLista.setItem(i,j,item)
        self.tblLista.setHorizontalHeaderLabels(encabezado)
        self.tblLista.setColumnWidth(0, 0)
        self.tblLista.setColumnWidth(1, 120)
        pass

    def salir(self):
        self.close()
        pass
