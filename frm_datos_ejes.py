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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_datos_ejes.ui'))

class frmDatosEjes(DialogType, DialogBase):

    def __init__(self, tipo_usuario, conn, str_ejes):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.conn = conn
        self.str_ejes = str_ejes

        #QMessageBox.information(None, 'EnerGis 5', str(self.tipo_usuario))
        if self.tipo_usuario==4:
            self.cmdCiudades.setEnabled(False)
            self.cmdCalles.setEnabled(False)
            self.cmdAceptar.setEnabled(False)

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT ciudad, descripcion FROM Ciudades")
        #convierto el cursor en array
        self.ciudades = tuple(cursor)
        cursor.close()

        self.cmbCiudad.addItem('<Indistinto>')
        for ciudad in self.ciudades:
            self.cmbCiudad.addItem(ciudad[1])

        self.cmbCiudad.setCurrentIndex(0)

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT ciudad, descripcion FROM Calles WHERE ciudad='0'")
        #convierto el cursor en array
        self.calles = tuple(cursor)
        cursor.close()

        self.cmbCalle.clear()
        for calle in self.calles:
            self.cmbCalle.addItem(calle[1])

        self.txtIzqde.setText('0')
        self.txtIzqa.setText('0')
        self.txtDerde.setText('0')
        self.txtDera.setText('0')

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        self.cmbCiudad.activated.connect(self.elijo_ciudad)

    def elijo_ciudad(self): #Evento de elegir
        self.ciudad=0
        #busco en la base el id del elemento seleccionado
        for i in range (0, len(self.ciudades)):
            if self.cmbCiudad.currentText()==self.ciudades[i][1]:
                self.ciudad = self.ciudades[i][0]

        if self.cmbCiudad.currentText()=='<indistinto>':
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT calle, descripcion FROM Calles")
            #convierto el cursor en array
            self.calles = tuple(cursor)
            cursor.close()
        else:
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT calle, descripcion FROM Calles WHERE ciudad='" + str(self.ciudad) + "'")
            #convierto el cursor en array
            self.calles = tuple(cursor)
            cursor.close()

        self.cmbCalle.clear()
        for calle in self.calles:
            self.cmbCalle.addItem(str(calle[1]))

    def nueva_ciudad(self):
        #from .frm_abm_lineas import frmAbmLineas
        #dialogo = frmAbmLineas(self.tipo_usuario, self.conn, 0)
        #dialogo.exec()
        #dialogo.close()
        pass

    def nueva_calle(self):
        #from .frm_abm_lineas import frmAbmLineas
        #self.dialogo = frmAbmLineas(self.tipo_usuario, self.conn, self.elmt)
        #self.dialogo.show()
        pass

    def aceptar(self):
        #mensaje=''
        id_ciudad=0
        id_calle=0
        for ciudad in self.ciudades:
            if self.cmbCiudad.currentText()==ciudad[1]:
                id_ciudad=ciudad[0]
        for calle in self.calles:
            if self.cmbCalle.currentText()==calle[1]:
                id_calle=calle[0]
        try:
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()

            if self.toolBox.currentIndex()==0:
                str_set = "Ciudad='" + str(id_ciudad) + "', "
                str_set = str_set + "Calle=" + str(id_calle)
            if self.toolBox.currentIndex()==1:
                str_set = "IzqDe=" + self.txtIzqde.text() + ", "
                str_set = str_set + "IzqA=" + self.txtIzqa.text() + ", "
                str_set = str_set + "DerDe=" + self.txtDerde.text() + ", "
                str_set = str_set + "DerA=" + self.txtDera.text()
            cursor.execute("UPDATE Ejes SET " + str_set + " WHERE Geoname IN (" + self.str_ejes + ")")
            #mensaje = "UPDATE Ejes SET " + str_set + " WHERE Geoname IN (" + self.str_ejes + ")"
            cnn.commit()
        except:
            #QMessageBox.information(None, 'EnerGis 5', 'Error en:', mensaje)
            cnn.rollback()
            QMessageBox.information(None, 'EnerGis 5', "No se pudo actualizar !")

        self.close()
        pass

    def salir(self):
        self.close()
        pass
