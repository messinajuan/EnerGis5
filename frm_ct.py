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
from PyQt5.QtGui import QIntValidator
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_ct.ui'))

class frmCT(DialogType, DialogBase):
        
    def __init__(self, tipo_usuario, conn, tension, geoname, nombre):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.conn = conn
        self.tension = tension
        self.geoname = geoname
        self.nombre = nombre
        vint = QIntValidator()
        self.txtDescargadores.setValidator(vint)
        self.txtcaeis.setValidator(vint)
        self.txtcaeies.setValidator(vint)
        self.txtcaees.setValidator(vint)
        self.txtcaeees.setValidator(vint)
        self.txtcasis.setValidator(vint)
        self.txtcasies.setValidator(vint)
        self.txtcases.setValidator(vint)
        self.txtcasees.setValidator(vint)

        if self.tipo_usuario==4:
            self.cmdAceptar.setEnabled(False)

        self.cmbPlataforma.addItem('Madera')
        self.cmbPlataforma.addItem('Hormigón')
        self.cmbPlataforma.addItem('Mixta')
        self.cmbPlataforma.addItem('SD')

        self.cmbTipo.addItem('Monoposte')
        self.cmbTipo.addItem('A Nivel')
        self.cmbTipo.addItem('Biposte')
        self.cmbTipo.addItem('Plataforma')
        self.cmbTipo.addItem('Cámara')
        self.cmbTipo.addItem('Cámara Nivel')
        self.cmbTipo.addItem('Cámara Subterránea')
        self.cmbTipo.addItem('Cámara Elevada')
        self.cmbTipo.addItem('Centro Compacto')

        self.cmbEstado.addItem('Bueno')
        self.cmbEstado.addItem('Regular')
        self.cmbEstado.addItem('Malo')

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT id_ct,ubicacion,mat_plataf,Tipo_Ct,obs,es,caeis,caeies,caees,caeees,casis,casies,cases,casees,exp,conservacion,descargadores FROM Ct WHERE id_ct IN (SELECT Nombre FROM Nodos WHERE Nodos.Tension>0 AND  geoname=" + str(self.geoname) + ")")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        if len(recordset) == 0: #nuevo

            str_campos = "id_ct,ubicacion,mat_plataf,Tipo_Ct,obs,es,caeis,caeies,caees,caeees,casis,casies,cases,casees,exp,conservacion,descargadores"
            str_valores = "'" + self.nombre + "','','Madera','Monoposte','',1,0,0,0,0,0,0,0,0,'1111/2001','Bueno',1"

            try:
                cnn = self.conn
                cursor = cnn.cursor()
                cursor.execute("INSERT INTO Ct (" + str_campos + ") VALUES (" + str_valores + ")")
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.information(None, 'EnerGis 5', "No se pudo insertar !")
                pass
            self.txtCT.setText(self.nombre)

        else:

            self.txtCT.setText(recordset[0][0])
            self.txtUbicacion.setText(recordset[0][1])
            self.cmbPlataforma.setCurrentIndex(0)
            for i in range (0, self.cmbPlataforma.count()):
                if self.cmbPlataforma.itemText(i) == str(recordset[0][2]):
                    self.cmbPlataforma.setCurrentIndex(i)
            self.cmbTipo.setCurrentIndex(0)
            for i in range (0, self.cmbTipo.count()):
                if self.cmbTipo.itemText(i) == str(recordset[0][3]):
                    self.cmbTipo.setCurrentIndex(i)
            self.txtObservaciones.setText(recordset[0][4])
            self.chkES.setChecked(recordset[0][5])

            self.txtcaeis.setText(str(recordset[0][6]))
            self.txtcaeies.setText(str(recordset[0][7]))
            self.txtcaees.setText(str(recordset[0][8]))
            self.txtcaeees.setText(str(recordset[0][9]))
            self.txtcasis.setText(str(recordset[0][10]))
            self.txtcasies.setText(str(recordset[0][11]))
            self.txtcases.setText(str(recordset[0][12]))
            self.txtcasees.setText(str(recordset[0][13]))
            self.txtExpediente.setText(recordset[0][14])

            self.cmbEstado.setCurrentIndex(0)
            for i in range (0, self.cmbEstado.count()):
                if self.cmbEstado.itemText(i) == str(recordset[0][15]):
                    self.cmbEstado.setCurrentIndex(i)

            self.txtDescargadores.setText(str(recordset[0][16]))

        pass


    def aceptar(self):
        cnn = self.conn
        cursor = cnn.cursor()

        str_set = "ubicacion='" + self.txtUbicacion.text().replace("'","") + "', "
        str_set = str_set + "mat_plataf='" + self.cmbPlataforma.currentText() + "', "
        str_set = str_set + "Tipo_Ct='" + self.cmbTipo.currentText() + "', "
        str_set = str_set + "obs='" + self.txtObservaciones.toPlainText().replace("'","") + "', "

        if self.chkES.isChecked() == True:
            str_set = str_set + "es=1, "
        else:
            str_set = str_set + "es=0, "

        str_set = str_set + "caeis=" + self.txtcaeis.text() + ", "
        str_set = str_set + "caeies=" + self.txtcaeies.text() + ", "
        str_set = str_set + "caees=" + self.txtcaees.text() + ", "
        str_set = str_set + "caeees=" + self.txtcaeees.text() + ", "
        str_set = str_set + "casis=" + self.txtcasis.text() + ", "
        str_set = str_set + "casies=" + self.txtcasies.text() + ", "
        str_set = str_set + "cases=" + self.txtcases.text() + ", "
        str_set = str_set + "casees=" + self.txtcasees.text() + ", "

        str_set = str_set + "exp='" + self.txtExpediente.text() + "', "
        str_set = str_set + "conservacion='" + self.cmbEstado.currentText() + "',"
        str_set = str_set + "descargadores=" + self.txtDescargadores.text()

        try:
            cursor.execute("UPDATE Ct SET " + str_set + " WHERE id_ct='" + self.txtCT.text() + "'")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.information(None, 'EnerGis 5', "No se pudo actualizar !")
        pass
        #QMessageBox.information(None, 'EnerGis 5', str_set)
        self.close()
        pass

    def salir(self):
        self.close()
        pass
