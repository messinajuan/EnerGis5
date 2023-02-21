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

from .mod_navegacion import caida_tension
#from PyQt5.QtWidgets import QMessageBox
from qgis.gui import QgsMapTool
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrCaidaTension(QgsMapTool):

    def __init__(self, iface, mapCanvas, conn, nodo):
        QgsMapTool.__init__(self, mapCanvas)
        self.iface = iface
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.nodo = nodo

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
        #--------------------------------------------
        caida_tension(self, self.mnodos, self.mlineas, self.nodo)
        #--------------------------------------------
        #from .frm_seleccion import frmSeleccion
        #self.dialogo = frmSeleccion(self.mapCanvas)
        #self.dialogo.show()
        pass
