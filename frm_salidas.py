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
from PyQt5 import QtWidgets
#from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIntValidator
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_salidas.ui'))

class frmSalidas(DialogType, DialogBase):
        
    def __init__(self, conn, geoname):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.geoname = geoname
        vint = QIntValidator()
        self.txtPrioridad.setValidator(vint)
        self.inicio()
        pass

    def inicio(self):
        #QMessageBox.information(None, 'EnerGis 5', 'Inicio')
        cnn = self.conn
        cursor = cnn.cursor()
        #salida = []
        #cursor.execute("SELECT Nombre, Descripcion, Val1, Val2 FROM Nodos WHERE geoname= + geoname")
        #convierto el cursor en array
        #salida = tuple(cursor)
        #cursor.close()

        if self.geoname != 0:
            cursor = cnn.cursor()
            datos_nodo = []
            cursor.execute("SELECT ISNULL(Val1, ''), ISNULL(Val5, ''), ISNULL(descripcion, ''), ISNULL(Val2, '') FROM Nodos WHERE Geoname=" + str(self.geoname))
            #convierto el cursor en array
            datos_nodo = tuple(cursor)
            cursor.close()        
            self.txtNombre.setText(str(datos_nodo[0][0]))
            self.txtPrioridad.setText(str(datos_nodo[0][1]))
            self.cmbCD.setCurrentIndex(0) #str(datos_nodo[0][2])

            try:
                str_color = str(hex(int(datos_nodo[0][3]))).replace('0x','')
                str_color = '000000' + str_color
                str_color = str_color[-6:]

                self.linea.setStyleSheet("color:#" + str_color + ";")
                self.qcolor = self.linea.palette().window().color()
            except:
                 pass
            pass

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdColor.clicked.connect(self.cambiar_color)
        self.cmdSalir.clicked.connect(self.salir)
        pass
        
    def aceptar(self):
        if self.geoname==0:
            return

        cnn = self.conn
        cursor = cnn.cursor()
        str_set = "Val1='" + self.txtNombre.text() + "', "
        str_set = str_set + "Val5='" + self.txtPrioridad.text() + "', "
        str_set = str_set + "descripcion='" + self.cmbCD.currentText() + "', "
        str_set = str_set + "Val2='" + str(int(self.qcolor.name().replace('#',''), 16)) + "'"

        cursor.execute("UPDATE Nodos SET " + str_set + " WHERE Geoname=" + str(self.geoname))
        cnn.commit()

        self.close()
        pass

    def cambiar_color(self):
        self.qcolor = self.linea.palette().window().color()
        self.qcolor = QtWidgets.QColorDialog.getColor(self.qcolor, self)
        self.linea.setStyleSheet("color:" + self.qcolor.name() + ";")

    def salir(self):
        self.close()
        pass
