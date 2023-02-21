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
#from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QDoubleValidator
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_fuentes.ui'))

class frmFuentes(DialogType, DialogBase):
        
    def __init__(self, conn, geoname):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.geoname = geoname
        vfloat = QDoubleValidator()
        self.txtVpu.setValidator(vfloat)
        self.txtAngulo.setValidator(vfloat)
        self.txtScc.setValidator(vfloat)
        self.inicio()        
        pass

    def inicio(self):
        self.cmbTipo.addItem('Combustión Interna')
        self.cmbTipo.addItem('Eólica')
        self.cmbTipo.addItem('Hidroeléctrica')
        self.cmbTipo.addItem('Biomasa')
        self.cmbTipo.addItem('Solar')
        self.cmbTipo.addItem('Otro')

        self.txtSSEE.setText('SSEE')
        self.txtVpu.setText('1')
        self.txtAngulo.setText('0')
        self.rbtPuntoCompra.setChecked(True)
        self.txtExpediente.setText("1111/2001")
        self.txtScc.setText('0')

        if self.geoname!=0:
            cnn = self.conn
            cursor = cnn.cursor()
            fuente = []
            cursor.execute("SELECT ISNULL(Descripcion, ''), Val1, Val2, Val3, Val4 FROM Nodos WHERE geoname=" + str(self.geoname))
            #convierto el cursor en array
            fuente = tuple(cursor)
            cursor.close()

            self.txtSSEE.setText(str(fuente[0][0]))
            self.txtVpu.setText(str(fuente[0][2]))
            self.txtAngulo.setText(str(fuente[0][3]))

            str_matriz = str(fuente[0][4]).split("-")

            tipo_fuente = str_matriz[0]
            if tipo_fuente=='1':
                self.rbtGeneracion.setChecked(True)
            if tipo_fuente=='0':
                self.rbtPuntoCompra.setChecked(True)

            if len (str_matriz)==3:
                self.txtExpediente.setText(str_matriz[1])
                tipo_generacion = str_matriz[2]
                if tipo_generacion!='':
                    for i in range (0, self.cmbTipo.count()):
                        if self.cmbTipo.itemText(i) == tipo_generacion:
                            self.cmbTipo.setCurrentIndex(i)
                self.txtScc.setText(str_matriz[3])

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        pass
        
    def aceptar(self):
        if self.geoname==0:
            return

        cnn = self.conn
        cursor = cnn.cursor()

        str_set = "Descripcion='" + self.txtSSEE.text() + "', "

        str_set = str_set + "Val1=Tension, "
        str_set = str_set + "Val2='" + self.txtVpu.text() + "', "
        str_set = str_set + "Val3='" + self.txtAngulo.text() + "', "
        str_set = str_set + "Val4='" + self.txtScc.text() + "'"

        cursor.execute("UPDATE Nodos SET " + str_set + " WHERE Geoname=" + str(self.geoname))
        cnn.commit()
        #QMessageBox.information(None, 'EnerGis 5', str_set)
        self.close()
        pass

    def salir(self):
        self.close()
        pass
