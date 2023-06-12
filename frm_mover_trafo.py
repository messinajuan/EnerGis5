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
from PyQt5 import QtCore
from PyQt5.QtCore import QDate, QDateTime
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_mover_trafo.ui'))

class frmMoverTrafo(DialogType, DialogBase):

    def __init__(self, conn, id, ct):
        super().__init__()
        self.setupUi(self)
        #self.setFixedSize(self.size())
        self.conn = conn
        self.id = id
        self.ct = ct

        self.cmbOrigen.addItem('Compras')
        self.cmbOrigen.addItem('Almacén')
        self.cmbOrigen.addItem('Reparación')
        self.cmbOrigen.addItem('Campo')
        self.cmbDestino.addItem('Baja Definitiva')
        self.cmbDestino.addItem('Almacén')
        self.cmbDestino.addItem('Reparación')
        self.cmbDestino.addItem('Campo')

        self.arrAlmacenes = []

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT id_almacen, nombre FROM Almacenes")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        for row in rows:
            self.arrAlmacenes.append(row)
            self.cmbAlmacen.addItem(str(row[1]))

        self.cmbAlmacen.setVisible(False)

        self.fecha_movimiento = QDate.currentDate()
        self.hora_movimiento = QDateTime.currentDateTime().toString("HH:mm:ss")

        self.datFecha.setDate(self.fecha_movimiento)
        self.tipo=0
        #1      Movimiento de alta
        #2      Movimiento relacionado al CT
        self.desde=0
        self.hasta=0
        #0	Baja Definitiva
        #1	Almacén
        #2	Reparación
        #3	Campo

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

        cnn = self.conn
        cursor = cnn.cursor()

        if self.ct != "": #movimientos en CT
            if self.id == 0: #busco un trafo en almacen
                self.cmbOrigen.setCurrentIndex(1)
                self.cmbDestino.setCurrentIndex(3)
                self.cmbOrigen.setEnabled(False)
                self.cmbDestino.setEnabled(False)
                self.sql = "SELECT id_trafo, potencia, marca, n_chapa, tension_1, tension_2, conexionado FROM Transformadores WHERE id_ct='' OR id_ct IS NULL ORDER BY MARCA, N_CHAPA"
                self.tipo=2
                self.desde=1
                self.hasta=3
            else: #mando el trafo a almacen
                self.cmbOrigen.setCurrentIndex(3)
                self.cmbDestino.setCurrentIndex(1)
                self.cmbOrigen.setEnabled(False)
                self.cmbDestino.setEnabled(False)
                self.cmbAlmacen.setVisible(True)
                self.sql = "SELECT id_trafo, potencia, marca, n_chapa, tension_1, tension_2, conexionado FROM Transformadores WHERE id_ct='" + self.ct + "'"
                self.tipo=2
                self.desde=3
                self.hasta=1
        else: #FALTA PROGRAMAR
            return
            pass

        cursor.execute(self.sql)
        elementos = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()
        self.lleno_grilla(encabezado, elementos)
        pass

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.seleccionado = ""
            self.close()

    def lleno_grilla(self, encabezado, elementos):
        self.tblListado.setRowCount(0)
        if len(elementos) > 0:
            self.tblListado.setRowCount(len(elementos))
            self.tblListado.setColumnCount(len(elementos[0]))
        for i in range (0, len(elementos)):
            for j in range (len(elementos[0])):
                item = QTableWidgetItem(str(elementos[i][j]))
                self.tblListado.setItem(i,j,item)
        self.tblListado.setHorizontalHeaderLabels(encabezado)

    def aceptar(self):
        cnn = self.conn
        self.id = self.tblListado.item(self.tblListado.currentRow(),0).text()
        if self.id=='':
            return

        id_almacen=0
        for i in range (0, len(self.arrAlmacenes)):
            if self.cmbAlmacen.currentText()==self.arrAlmacenes[i][1]:
                id_almacen=self.arrAlmacenes[i][0]

        reply = QMessageBox.question(None, 'EnerGis 5', '¿ Mover el trafo ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                cursor = cnn.cursor()
                cursor.execute("INSERT INTO Movimiento_Transformadores (id_trafo,fecha,tipo_mov,mov_desde,mov_hasta,motivo_mov,observaciones,id_almacen) VALUES (" + self.id + ",'" + str(self.datFecha.date().toPyDate()).replace('-','') + " " + self.hora_movimiento + "'," + str(self.tipo) + "," + str(self.desde) + "," + str(self.hasta) + ",'" + self.txtMotivo.text() + "','" + self.txtObservaciones.toPlainText() + "'," + str(id_almacen) + ")")
                if self.hasta == 1:
                    cursor.execute("UPDATE Transformadores SET usado=1, id_ct='' WHERE id_trafo=" + self.id)
                if self.hasta == 3:
                    cursor.execute("UPDATE Transformadores SET usado=3, id_ct='" + self.ct + "' WHERE id_trafo=" + self.id)
                cnn.commit()
                QMessageBox.information(None, 'EnerGis 5', "El Transformador se movió con éxito !")
            except:
                #QMessageBox.information(None, 'EnerGis 5', "INSERT INTO Movimiento_Transformadores (id_trafo,fecha,tipo_mov,mov_desde,mov_hasta,motivo_mov,observaciones,id_almacen) VALUES (" + self.id + ",'" + str(self.datFecha.date().toPyDate()).replace('-','') + " " + self.hora_movimiento + "'," + str(self.tipo) + "," + str(self.desde) + "," + str(self.hasta) + ",'" + self.txtMotivo.text() + "','" + self.txtObservaciones.toPlainText() + "'," + str(id_almacen) + ")")
                cnn.rollback()
                QMessageBox.information(None, 'EnerGis 5', "No se pudo mover !")
                return

        self.close()
        pass

    def salir(self):
        self.seleccionado = ""
        self.close()
        pass
