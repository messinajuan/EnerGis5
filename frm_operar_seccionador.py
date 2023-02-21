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
from .mod_navegacion import nodos_por_salida

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_operar_seccionador.ui'))
basepath = os.path.dirname(os.path.realpath(__file__))

class frmOperarSeccionador(DialogType, DialogBase):
        
    def __init__(self, conn, geoname, elmt, estado, capa):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.geoname = geoname
        self.elmt = elmt
        self.estado = estado
        self.capa = capa
        self.reconfiguro = False
        self.inicio()
        pass

    def inicio(self):
        if self.elmt==2:
            self.lblElemento.setText('CERRADO')
        else:
            self.lblElemento.setText('ABIERTO')

        if self.estado==2:
            self.lblEstado.setText('CERRADO')
        else:
            self.lblEstado.setText('ABIERTO')

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT aux FROM mNodos WHERE Geoname=" + str(self.geoname))
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        self.id = rst[0][0]

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
        #convierto el cursor en array
        self.mlineas = tuple(cursor)
        cursor.close()

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
        #convierto el cursor en array
        self.mnodos = tuple(cursor)
        cursor.close()

        self.cmdOperar.clicked.connect(self.operar)
        self.cmdReconfigurar.clicked.connect(self.reconfigurar)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        pass
        
    def operar(self):
        if self.estado==2:
            self.estado=3
            self.lblEstado.setText('ABIERTO')
        else:
            self.estado=2
            self.lblEstado.setText('CERRADO')
        pass

    def reconfigurar(self):
        if self.elmt==2:
            self.elmt=3
            self.lblElemento.setText('ABIERTO')
            self.estado=3
            self.lblEstado.setText('ABIERTO')
        else:
            self.elmt=2
            self.lblElemento.setText('CERRADO')
            self.estado=2
            self.lblEstado.setText('CERRADO')

        self.reconfiguro = True

        pass

    def aceptar(self):

        self.mnodos[self.id][2] = self.estado
        self.mnodos[self.id][39] = self.elmt

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute('UPDATE Nodos SET elmt=' + str(self.elmt) + ', estado=' + str(self.estado) + ' WHERE geoname=' + str(self.geoname))
        cnn.commit()

        if self.reconfiguro == True:
            #QMessageBox.information(None, 'Mensaje', 'Reconfiguro')
            nodos_por_salida(self, self.conn, self.mnodos, self.mlineas)

        self.capa.triggerRepaint()
        self.salir()
        pass

    def salir(self):
        self.close()
        pass
