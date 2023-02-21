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
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_abm_postes.ui'))

class frmAbmPostes(DialogType, DialogBase):
        
    def __init__(self, conn):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.inicio()
        pass

    def inicio(self):
        self.cmbMaterial.addItem('Madera')
        self.cmbMaterial.addItem('Hierro Columna')
        self.cmbMaterial.addItem('Hierro Riel')
        self.cmbMaterial.addItem('Hierro Perfil')
        self.cmbMaterial.addItem('Hormigón Armado')
        self.cmbMaterial.addItem('PRFV')
        self.cmbMaterial.addItem('Compuesto')

        self.cmbTipo.addItem('Poste')
        self.cmbTipo.addItem('Ménsula')
        self.cmbTipo.addItem('Grampa')
        self.cmbTipo.addItem('Portico')

        self.cmdAgregarEstructura.clicked.connect(self.agregar_estructura)
        self.cmdAgregarPoste.clicked.connect(self.agregar_poste)
        self.cmdSalir.clicked.connect(self.salir)
        pass

    def agregar_estructura(self):
        cnn = self.conn
        cursor = cnn.cursor()

        cursor.execute("SELECT MAX(id) FROM Estructuras")
        rows = cursor.fetchall()
        cursor.close()
        id = rows[0][0] + 1

        descripcion = self.txtEstructura.text()
        estilo = '39-MapInfo Oil&Gas-16777215-0-12'

        reply = QMessageBox.question(None, 'EnerGis 5', 'Desea insertar un nuevo tipo de estructura?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        cursor.execute("INSERT INTO Estructuras (id, descripcion, estilo) VALUES (" + str(id) + ",'" + descripcion + "','" + estilo + "')")
        cnn.commit()
        pass

    def agregar_poste(self):
        cnn = self.conn
        cursor = cnn.cursor()

        cursor.execute("SELECT MAX(id) FROM Elementos_Postes")
        rows = cursor.fetchall()
        cursor.close()
        id = rows[0][0] + 1

        descripcion = self.txtPoste.text()
        estilo = '38-Map Symbols-16777215-255-6-0'
        value1 = self.cmbMaterial.currentText()
        value2 = self.cmbTipo.currentText()

        reply = QMessageBox.question(None, 'EnerGis 5', 'Desea insertar un nuevo tipo de poste?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        cursor.execute("INSERT INTO Postes (id, descripcion, estilo, value1, value2) VALUES (" + str(id) + ",'" + descripcion + "','" + estilo + "','" + value1 + "','" + value2 + "')")
        cnn.commit()
        pass

    def salir(self):
        self.close()
        pass
