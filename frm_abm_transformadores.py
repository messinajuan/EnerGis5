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
from PyQt5.QtGui import QDoubleValidator
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_abm_transformadores.ui'))

class frmAbmTransformadores(DialogType, DialogBase):

    def __init__(self, conn, id):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        #basepath = os.path.dirname(os.path.realpath(__file__))
        self.conn = conn
        self.id = id
        vint = QIntValidator()
        vfloat = QDoubleValidator()
        self.txtPotencia.setValidator(vfloat)
        self.txtV1.setValidator(vfloat)
        self.txtV2.setValidator(vfloat)
        self.txtAnio.setValidator(vint)
        self.inicio()
        pass

    def inicio(self):
        self.cmbConexionado.addItem('M')
        self.cmbConexionado.addItem('B')
        self.cmbConexionado.addItem('Yy0')
        self.cmbConexionado.addItem('Yd5')
        self.cmbConexionado.addItem('Yd11')
        self.cmbConexionado.addItem('Dy5')
        self.cmbConexionado.addItem('Dy11')

        self.cmbTipo.addItem('Monofásico')
        self.cmbTipo.addItem('Bifásico')
        self.cmbTipo.addItem('Trifásico')

        self.txtTrafo.setText(str(self.id))

        cnn = self.conn

        if self.id!=0: #edit
            cursor = cnn.cursor()
            datos_trafo = []
            cursor.execute("SELECT Potencia,Conexionado,Tension_1,Tension_2,Marca,N_chapa,Tipo,Anio_fabricacion,Obs,Prop_usuario,Kit,Cromatografia,Anomalia,Fecha_norm,Obs_pcb,Certificado,aceite FROM Transformadores WHERE id_trafo=" + str(self.id))
            #convierto el cursor en array
            datos_trafo = tuple(cursor)
            cursor.close()

            self.txtPotencia.setText(str(datos_trafo[0][0]))

            for i in range (0, self.cmbConexionado.count()):
                if self.cmbConexionado.itemText(i) == str(datos_trafo[0][1]):
                    self.cmbConexionado.setCurrentIndex(i)

            self.txtV1.setText(str(datos_trafo[0][2]))
            self.txtV2.setText(str(datos_trafo[0][3]))
            self.txtMarca.setText(datos_trafo[0][4])
            self.txtNroChapa.setText(datos_trafo[0][5])
            if datos_trafo[0][6]==1:
                self.cmbTipo.setCurrentIndex(0)
            elif datos_trafo[0][6]==2:
                self.cmbTipo.setCurrentIndex(1)
            else:
                self.cmbTipo.setCurrentIndex(2)
            self.txtAnio.setText(datos_trafo[0][7])
            self.txtObservaciones.setText(datos_trafo[0][8])
            if datos_trafo[0][9]==1:
                self.chkPropiedadUsuario.setChecked(True)
            else:
                self.chkPropiedadUsuario.setChecked(False)

            self.txtKit.setText(datos_trafo[0][10])
            self.txtCromatografia.setText(datos_trafo[0][11])
            self.txtAnomalia.setText(datos_trafo[0][12])

            if datos_trafo[0][13]!=None:
                self.datNormalizacion.setDate(datos_trafo[0][13])

            self.txtObservacionesPCB.setText(datos_trafo[0][14])
            if datos_trafo[0][15]==1:
                self.chkCertificado.setChecked(True)
            else:
                self.chkCertificado.setChecked(False)
            self.txtAceite.setText(str(datos_trafo[0][16]))

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        self.cmdParametros.clicked.connect(self.parametros)
        pass

    def aceptar(self):
        cnn = self.conn
        if self.cmbTipo.currentText()=='Monofasico':
            tipo=1
        else:
            if self.cmbTipo.currentText()=='Bifasico':
                tipo=2
            else:
                tipo=3
        if self.chkCertificado.isChecked() == True:
            certificado=1
        else:
            certificado=0
        if self.chkPropiedadUsuario.isChecked() == True:
            prop_usuario=1
        else:
            prop_usuario=0
        if self.txtPotencia.text() == "":
            QMessageBox.information(None, 'EnerGis 5', "Debe ingresar una potencia")
            return

        if self.id==0: #Nuevo
            reply = QMessageBox.question(None, 'EnerGis 5', '¿ Guardar los datos ?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                cursor = cnn.cursor()
                cursor.execute("SELECT MAX(id) FROM Transformadores")
                rows = cursor.fetchall()
                cursor.close()
                id = rows[0][0] + 1
                try:
                    cursor = cnn.cursor()
                    cursor.execute("INSERT INTO Transformadores (Id,Potencia,Conexionado,Marca,N_chapa,Tension_1,Tension_2,Tipo,Anio_fabricacion,Obs,Kit,Cromatografia,Anomalia,Fecha_norm,Certificado,Obs_pcb,aceite,Prop_usuario) VALUES (" + str(id) + "," + self.txtPotencia.text() + ",'" + self.cmbConexionado.currentText() + "','" + self.txtMarca.text() + "','" + self.txtNroChapa.text() + "'," + self.txtV1.text() + "," + self.txtV2.text() + "," + str(tipo) + ",'" + self.txtAnio.text() + "','" + self.txtObservaciones.toPlainText() + "','" + self.txtKit.currentText() + "','" + self.txtCromatografia.currentText() + "','" + self.txtAnomalia.currentText() + "','" + str(self.datNormalizacion.date().toPyDate()).replace('-','') + "'," + str(certificado) + ",'" + self.txtObservacionesPCB.currentText() + "'," + self.txtAceite.currentText() + "," + str(prop_usuario))
                    cnn.commit()
                    QMessageBox.information(None, 'EnerGis 5', "Transformador agregado !")
                except:
                    cnn.rollback()
                    QMessageBox.information(None, 'EnerGis 5', "No se pudo grabar !")
                    return

        else: #edicion
            str_set = "Potencia=" + self.txtPotencia.text() + ", "
            str_set = str_set + "Conexionado='" + self.cmbConexionado.currentText() + "', "
            str_set = str_set + "Marca='" + self.txtMarca.text() + "', "
            str_set = str_set + "N_chapa='" + self.txtNroChapa.text() + "', "
            str_set = str_set + "Tension_1=" + self.txtV1.text() + ", "
            str_set = str_set + "Tension_2=" + self.txtV2.text() + ", "
            str_set = str_set + "Tipo=" + str(tipo) + ", "
            str_set = str_set + "Anio_fabricacion=" + self.txtAnio.text() + ", "
            str_set = str_set + "Obs='" + self.txtObservaciones.toPlainText() + "', "
            str_set = str_set + "Kit='" + self.txtKit.text() + "', "
            str_set = str_set + "Cromatografia='" + self.txtCromatografia.text() + "', "
            str_set = str_set + "Anomalia='" + self.txtAnomalia.text() + "', "
            str_set = str_set + "Fecha_norm='" + str(self.datNormalizacion.date().toPyDate()).replace('-','') + "', "
            str_set = str_set + "Certificado=" + str(certificado) + ", "
            str_set = str_set + "Obs_pcb='" + self.txtObservacionesPCB.text() + "', "
            str_set = str_set + "aceite='" + self.txtAceite.text() + "', "
            str_set = str_set + "Prop_usuario=" + str(prop_usuario)

            reply = QMessageBox.question(None, 'EnerGis 5', '¿ Desea guardar los cambios ?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    cursor = cnn.cursor()
                    cursor.execute("UPDATE Transformadores SET " + str_set + " WHERE id_trafo=" + str(self.id))
                    cnn.commit()
                    QMessageBox.information(None, 'EnerGis 5', "Actualizado !")
                except:
                    QMessageBox.information(None, 'EnerGis 5', "UPDATE Transformadores SET " + str_set + " WHERE id_trafo=" + self.txtTrafo.text())
                    cnn.rollback()
                    QMessageBox.information(None, 'EnerGis 5', "No se pudo actualizar !")
                    return

            cnn.commit()
        self.close()
        pass

    def parametros(self):
        from .frm_parametros_trafo import frmParametrosTrafo
        dialogo = frmParametrosTrafo(self.conn, self.id, float(self.txtPotencia.text()))
        dialogo.exec()
        dialogo.close()
        pass

    def taps(self):
        from .frm_taps import frmTaps
        dialogo = frmTaps(self.conn, self.id)
        dialogo.exec()
        dialogo.close()
        pass

    def salir(self):
        self.close()
        pass
