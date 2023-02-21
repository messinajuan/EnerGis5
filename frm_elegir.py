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
from PyQt5.QtWidgets import QTableWidgetItem
#from PyQt5.QtWidgets import QMessageBox
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_elegir.ui'))

class frmElegir(DialogType, DialogBase):

    def __init__(self, conn, sql):
        super().__init__()
        self.setupUi(self)
        #self.setFixedSize(self.size())
        self.conn = conn
        self.sql = sql
        self.inicio()
        pass

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.seleccionado = ""
            self.close()
        
    def inicio(self):
        cnn = self.conn
        cursor = cnn.cursor()
        recordset = []
        cursor.execute(self.sql)
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        self.tblListado.setRowCount(len(recordset))
        self.tblListado.setColumnCount(len(recordset[0]))
        self.tblListado.setHorizontalHeaderLabels(["Id", "Valor"])
        
        self.tblListado.setColumnWidth(0, 50)
        self.tblListado.setColumnWidth(1, 150)
        
        for i in range (0, len(recordset)):
            for j in range (0, len(recordset[0])):
                self.tblListado.setItem(i, j, QTableWidgetItem(str(recordset[i][j])))
        
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        pass

    def aceptar(self):
        self.seleccionado = self.tblListado.item(self.tblListado.currentRow(),0).text()
        self.close()
        pass

    def salir(self):
        self.seleccionado = ""
        self.close()
        pass
