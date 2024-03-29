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

import os
from PyQt5 import QtCore
from PyQt5.QtWidgets import QTableWidgetItem
#from PyQt5.QtWidgets import QMessageBox
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_usuarios_suministro.ui'))

class frmUsuariosSuministro(DialogType, DialogBase):

    def __init__(self, conn, geoname):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.geoname = geoname
        
        self.inicio()        
        pass

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
        
    def inicio(self):
        self.actualizar_grilla()
        self.rbtActivas.toggled.connect(self.rbt_click)
        self.rbtTodas.toggled.connect(self.rbt_click)
        self.cmdMedidor.clicked.connect(self.medidor)
        self.cmdSalir.clicked.connect(self.salir)

        pass

    def rbt_click(self):
        self.actualizar_grilla()

    def actualizar_grilla(self):
        rst = "SELECT DISTINCT Usuarios.id_usuario, VW_CCDATOSCOMERCIALES.Ruta, VW_CCDATOSCOMERCIALES.nro_medidor, Suministros.id_suministro, Usuarios.nombre, Usuarios.calle, Usuarios.altura, Usuarios.zona, Usuarios.tarifa, Usuarios.fase, Usuarios.Electrodependiente, Usuarios.FAE FROM (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) LEFT JOIN VW_CCDATOSCOMERCIALES ON Usuarios.id_usuario = VW_CCDATOSCOMERCIALES.id_usuario WHERE Suministros.id_nodo=" + str(self.geoname)
        if self.rbtActivas.isChecked() == True:
            rst = rst + " AND Usuarios.ES=1"

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute(rst)
        elementos = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()

        self.lleno_grilla(encabezado, elementos)

        pass

    def lleno_grilla(self, encabezado, elementos):
        self.tblUsuarios.setRowCount(0)
        if len(elementos) > 0:
            self.tblUsuarios.setRowCount(len(elementos))
            self.tblUsuarios.setColumnCount(len(elementos[0]))
        for i in range (0, len(elementos)):
            for j in range (len(elementos[0])):
                item = QTableWidgetItem(str(elementos[i][j]))
                self.tblUsuarios.setItem(i,j,item)
        self.tblUsuarios.setHorizontalHeaderLabels(encabezado)

    def medidor(self):

        self.id=0
        try:
            self.id = int(self.tblUsuarios.item(self.tblUsuarios.currentRow(),0).text())
        except:
            return

        from .frm_medidores import frmMedidores
        self.dialogo = frmMedidores(self.conn, self.id)
        self.dialogo.show()
        pass

    def salir(self):
        self.close()
        pass
