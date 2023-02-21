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
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_parcelas.ui'))

class frmParcelas(DialogType, DialogBase):

    def __init__(self, mapCanvas, conn, obj, geoname):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.obj = obj
        self.geoname = geoname
        self.inicio()
        pass

    def closeEvent(self, event):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name() == 'Aeeas_Temp':
                #borra todos los objetos de la capa
                if not lyr.isEditable():
                    lyr.startEditing()
                listOfIds = [feat.id() for feat in lyr.getFeatures()]
                lyr.deleteFeatures(listOfIds)
                lyr.commitChanges()
                #----------------------------------
            else:
                lyr.triggerRepaint()
        pass
        
    def inicio(self):
        #QMessageBox.information(None, 'EnerGis 5', 'Inicio')

        if self.geoname != 0:
            cnn = self.conn
            cursor = cnn.cursor()
            parcelas = []
            cursor.execute("SELECT Parcela, Manzana, Chacra, Quinta, Circunscripcion, Seccion FROM Parcelas WHERE geoname=" + str(self.geoname))
            #convierto el cursor en array
            parcelas = tuple(cursor)
            cursor.close()

            self.lblGeoname.setText(str(self.geoname))
            self.txtParcela.setText(str(parcelas[0][0]))
            self.txtManzana.setText(str(parcelas[0][1]))
            self.txtChacra.setText(str(parcelas[0][2]))
            self.txtQuinta.setText(str(parcelas[0][3]))
            self.txtCircunscripcion.setText(str(parcelas[0][4]))
            self.txtSeccion.setText(str(parcelas[0][5]))

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

        pass

    def aceptar(self):
        obj = ''
        
        if self.geoname == 0: #Si es nueva -> INSERT
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            cursor.execute("SELECT iid FROM iid")
            iid = tuple(cursor)
            id = iid[0][0] + 1
            cursor.execute("UPDATE iid SET iid =" + str(id))
            cnn.commit()

            cursor = cnn.cursor()
            cursor.execute("SELECT VAlor FROM Configuracion WHERE Variable='SRID'")
            rows = cursor.fetchall()
            cursor.close()
            srid = rows[0][0]

            obj = "geometry::STGeomFromText(" + "'" + self.obj.geometry().asWkt() + "'," + srid + ")"

            str_valores = str(id) + ", "
            str_valores = str_valores + "'" + self.txtParcela.text() + "', "
            str_valores = str_valores + "'" + self.txtManzana.text() + "', "
            str_valores = str_valores + "'" + self.txtChacra.text() + "', "
            str_valores = str_valores + "'" + self.txtQuinta.text() + "', "
            str_valores = str_valores + "'" + self.txtCircunscripcion.text() + "', "
            str_valores = str_valores + "'" + self.txtSeccion.text() + "', "
            str_valores = str_valores + obj

            #QMessageBox.information(None, 'EnerGis 5', str_valores)

            cursor = cnn.cursor()
            cursor.execute("INSERT INTO Parcelas (Geoname, Parcela, Manzana, Chacra, Quinta, Circunscripcion, Seccion, obj) VALUES (" + str_valores + ")")
            cnn.commit()

        else: #Si cambio algo -> UPDATE
            cnn = self.conn
            cursor = cnn.cursor()
            str_set = "Parcela='" + self.txtParcela.text() + "', "
            str_set = str_set + "Manzana='" + self.txtManzana.text() + "', "
            str_set = str_set + "Chacra='" + self.txtChacra.text() + "', "
            str_set = str_set + "Quinta='" + self.txtQuinta.text() + "', "
            str_set = str_set + "Circunscripcion='" + self.txtCircunscripcion.text() + "', "
            str_set = str_set + "Seccion='" + self.txtSeccion.text() + "'"

            cursor.execute("UPDATE Parcelas SET " + str_set + " WHERE Geoname=" + str(self.geoname))
            cnn.commit()

        self.close()
        pass

    def salir(self):
        self.close()
        pass
