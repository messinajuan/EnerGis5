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
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_suministros.ui'))

class frmSuministros(DialogType, DialogBase):
        
    def __init__(self, conn, geoname):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.geoname = geoname

        self.inicio()
        pass

    def inicio(self):
        if self.geoname != 0:

            cnn = self.conn
            cursor = cnn.cursor()
            recordset = []
            cursor.execute("SELECT Nodos.Nombre, Nodos.XCoord, Nodos.YCoord FROM Suministros_Trafos INNER JOIN Nodos ON Suministros_Trafos.Geoname_t = Nodos.Geoname WHERE Nodos.elmt=4 AND Suministros_Trafos.Geoname_s=" + str(self.geoname))
            #convierto el cursor en array
            recordset = tuple(cursor)
            cursor.close()

            if len(recordset)>0:
                self.label_9.setText('CT ' + recordset[0][0])
                self.label_7.setText(str(recordset[0][1]) + ', ' + str(recordset[0][2]))
            else:
                self.label_9.setText('Sum MT')
                self.label_7.setText('')

            pass

        self.lleno_lista1()
        self.lleno_lista2()

        self.cmdAgregar.clicked.connect(self.agregar)
        self.cmdQuitar.clicked.connect(self.quitar)
        self.cmdActualizar.clicked.connect(self.actualizar)
        self.cmdUsuarios.clicked.connect(self.usuarios)
        self.cmdSalir.clicked.connect(self.salir)
        pass
        
    def lleno_lista1(self):
        cnn = self.conn
        cursor = cnn.cursor()
        recordset = []
        cursor.execute("SELECT DISTINCT Suministros_Nuevos.id_suministro, VW_CCDATOSCOMERCIALES.Ruta, Usuarios.calle, Usuarios.altura FROM (Suministros_Nuevos LEFT JOIN Usuarios ON Suministros_Nuevos.id_suministro = Usuarios.id_suministro) LEFT JOIN VW_CCDATOSCOMERCIALES ON Usuarios.id_usuario = VW_CCDATOSCOMERCIALES.Id_Usuario ORDER BY Usuarios.calle")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        self.tbl1.setRowCount(len(recordset))
        self.tbl1.setColumnCount(4)
        self.tbl1.setHorizontalHeaderLabels(["Suministro", "Ruta", "Calle", "Número"])

        self.tbl1.setColumnWidth(0, 80)
        self.tbl1.setColumnWidth(1, 60)
        self.tbl1.setColumnWidth(2, 150)
        self.tbl1.setColumnWidth(3, 60)

        for i in range (0, len(recordset)):
            for j in range (0, 3):
                self.tbl1.setItem(i, j, QTableWidgetItem(recordset[i][j]))

        self.tbl1.clicked.connect(self.tbl1_click)
        pass

    def lleno_lista2(self):
        cnn = self.conn
        cursor = cnn.cursor()
        recordset = []
        cursor.execute("SELECT DISTINCT suministros.id_suministro, VW_CCDATOSCOMERCIALES.Ruta, Usuarios.calle, Usuarios.altura FROM (suministros INNER JOIN Usuarios ON suministros.id_suministro = Usuarios.id_suministro) LEFT JOIN VW_CCDATOSCOMERCIALES ON Usuarios.id_usuario = VW_CCDATOSCOMERCIALES.Id_Usuario WHERE id_nodo =" + str(self.geoname))
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        self.tbl2.setRowCount(len(recordset))
        self.tbl2.setColumnCount(4)
        self.tbl2.setHorizontalHeaderLabels(["Suministro", "Ruta", "Calle", "Número"])

        self.tbl2.setColumnWidth(0, 80)
        self.tbl2.setColumnWidth(1, 60)
        self.tbl2.setColumnWidth(2, 150)
        self.tbl2.setColumnWidth(3, 60)


        for i in range (0, len(recordset)):
            for j in range (0, 3):
                self.tbl2.setItem(i, j, QTableWidgetItem(recordset[i][j]))

        self.tbl2.clicked.connect(self.tbl2_click)
        pass

    def tbl1_click(self):
        self.label_10.setText("")
        id_suministro = self.tbl1.item(self.tbl1.currentRow(),0).text()
        cnn = self.conn
        cursor = cnn.cursor()
        recordset = []
        cursor.execute("SELECT Usuarios.id_usuario, Usuarios.nombre, Usuarios.calle, Usuarios.altura, Usuarios.altura_ex, Usuarios.zona, electrodependiente FROM Usuarios INNER JOIN Suministros_Nuevos ON Usuarios.id_suministro = Suministros_Nuevos.id_suministro WHERE Suministros_Nuevos.id_suministro ='" + id_suministro + "'")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()
        self.label_3.setText(str(recordset[0][0]) + " " + recordset[0][1] + " " + recordset[0][2] + " " + recordset[0][3] + " " + recordset[0][4] + " " + recordset[0][5])
        if recordset[0][6] == "S":
            self.label_10.setText("Posee un Electrodependiente")
        pass

    def tbl2_click(self):
        id_suministro = self.tbl2.item(self.tbl2.currentRow(),0).text()
        cnn = self.conn
        cursor = cnn.cursor()
        recordset = []
        cursor.execute("SELECT Usuarios.id_usuario, Usuarios.nombre, Usuarios.calle, Usuarios.altura, Usuarios.altura_ex, Usuarios.zona, electrodependiente FROM Usuarios WHERE Usuarios.id_suministro ='" + id_suministro + "'")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()
        self.label_5.setText(str(recordset[0][0]) + " " + recordset[0][1] + " " + recordset[0][2] + " " + recordset[0][3] + " " + recordset[0][4] + " " + recordset[0][5])
        if recordset[0][6] == "S":
            self.label_10.setText("Posee un Electrodependiente")
        pass

    def aceptar(self):
        #cnn = self.conn
        #cursor = cnn.cursor()
        #cursor.execute("UPDATE Nodos SET " + str_set + " WHERE Geoname=" + str(self.geoname))
        #cnn.commit()
        #QMessageBox.information(None, 'EnerGis 5', str_set)
        self.close()
        pass

    def agregar(self):
        cnn = self.conn
        cursor = cnn.cursor()
        for item in self.tbl1.selectedItems():
            if item.column()==0:
                cursor.execute("INSERT INTO Suministros (id_nodo,id_suministro) VALUES (" + str(self.geoname) + ",'" + item.text() + "')")
                cursor.execute("DELETE FROM Suministros_Nuevos WHERE id_suministro ='" + item.text() + "'")
                cnn.commit()
        self.lleno_lista1()
        self.lleno_lista2()
        pass

    def quitar(self):
        cnn = self.conn
        cursor = cnn.cursor()
        for item in self.tbl2.selectedItems():
            if item.column()==0:
                cursor.execute("INSERT INTO Suministros_Nuevos (id_suministro) VALUES ('" + item.text() + "')")
                cursor.execute("DELETE FROM Suministros WHERE id_suministro ='" + item.text() + "'")
                cnn.commit()
        self.lleno_lista1()
        self.lleno_lista2()
        pass

    def actualizar(self):
        msgBox=QMessageBox()
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setWindowTitle("Nuevos Suministros")
        msgBox.setText("Esta opción actualizará la lista de suministros sin nodo asociado")
        msgBox.setInformativeText("Desea Continuar ?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.Yes)
        resultado = msgBox.exec()

        if resultado==QMessageBox.Yes:
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("DELETE FROM Suministros_Nuevos")
            cursor.execute("INSERT INTO Suministros_Nuevos (id_suministro) SELECT usuarios.id_suministro FROM suministros RIGHT JOIN usuarios ON suministros.id_suministro = usuarios.id_suministro WHERE usuarios.ES=1 AND suministros.id_suministro IS NULL GROUP BY usuarios.id_suministro HAVING usuarios.id_suministro IS NOT NULL")
            cursor.execute("INSERT INTO Suministros_Nuevos (id_suministro) SELECT DISTINCT movimientos.id_suministro FROM movimientos WHERE tipo_mov='A' AND incorp=0 AND id_suministro NOT IN (SELECT suministros.id_suministro FROM suministros) AND id_suministro NOT IN (SELECT suministros_nuevos.id_suministro FROM suministros_nuevos)")
            cnn.commit()
            self.lleno_lista1()
        pass

    def usuarios(self):
        from .frm_usuarios_suministro import frmUsuariosSuministro
        self.dialogo = frmUsuariosSuministro(self.conn, self.geoname)
        self.dialogo.show()
        pass

    def salir(self):
        self.close()
        pass
