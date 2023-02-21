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
import pyodbc
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5 import uic
    
DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_fotos.ui'))

class frmFotos(DialogType, DialogBase):

    def __init__(self, conn, geoname):
        super().__init__()
        self.setupUi(self)
        #self.setFixedSize(self.size())
        self.conn = conn
        self.geoname = geoname

        cnn = self.conn
        cursor = cnn.cursor()
        self.fotos = []
        cursor.execute("SELECT nombre, imagen, id FROM Fotos WHERE Geoname=" + str(self.geoname))
        #convierto el cursor en array
        self.fotos = tuple(cursor)
        cursor.close()
        self.hslFotos.setMaximum(len(self.fotos))

        self.lblFoto.resize(self.size())

        if len(self.fotos)>0:
            self.hslFotos.setMinimum(1)
            self.mostrar()

        self.cmdAgregar.clicked.connect(self.agregar)
        self.cmdBorrar.clicked.connect(self.borrar)
        self.hslFotos.valueChanged.connect(self.mostrar)
        self.cmdSalir.clicked.connect(self.salir)
        pass

    def agregar(self):
        fname = QFileDialog.getOpenFileName(self, 'Abrir', 'c:\\',"Archivos de Imagen (*.jpg *.jpeg *.gif)")
        #QMessageBox.information(None, 'EnerGis 5', fname[0])

        if fname[0]=='':
            return

        f = open(fname[0], 'rb')
        bindata = f.read()
        nombre = os.path.basename(f.name)
        f.close

        cnn = self.conn
        sql = "INSERT INTO Fotos (geoname, nombre, imagen) VALUES (?,?,?)"
        cnn.cursor().execute(sql, (self.geoname, nombre, pyodbc.Binary(bindata)))
        cnn.commit()

        pixmap = QPixmap(fname[0])
        self.lblFoto.setPixmap(pixmap.scaled(self.lblFoto.size(), QtCore.Qt.KeepAspectRatio))
        self.lblFoto.setVisible(True)

        self.actualizo_fotos()

        QMessageBox.information(None, 'EnerGis 5', 'Grabado !')

        #esto es para varios archivos
        #dlg = QFileDialog()
        #dlg.setFileMode(QFileDialog.AnyFile)
        #dlg.setFilter("Text files (*.txt)")
        #filenames = QStringList()
        #if dlg.exec_():
        #    filenames = dlg.selectedFiles()

    def mostrar(self):
        if len(self.fotos)>0:
            pixmap = QPixmap()
            pixmap.loadFromData(self.fotos[self.hslFotos.value()-1][1])
            self.lblFoto.setPixmap(pixmap.scaled(self.lblFoto.size(), QtCore.Qt.KeepAspectRatio))
        pass

    def borrar(self):
        if self.hslFotos.value()-1<0:
            return
        reply = QMessageBox.question(None, 'EnerGis 5', 'Desea borrar la foto seleccionada ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM Fotos WHERE Id=" + str(self.fotos[self.hslFotos.value()-1][2]))
            self.conn.commit()
            self.lblFoto.clear()
            self.actualizo_fotos()
        pass

    def actualizo_fotos(self):
        cnn = self.conn
        cursor = cnn.cursor()
        self.fotos = []
        cursor.execute("SELECT nombre, imagen, id FROM Fotos WHERE Geoname=" + str(self.geoname))
        #convierto el cursor en array
        self.fotos = tuple(cursor)
        cursor.close()
        self.hslFotos.setMaximum(len(self.fotos))
        pass

    def salir(self):
        self.close()
        pass
