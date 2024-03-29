﻿# encoding: utf-8
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
from PyQt5 import QtCore
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_lista.ui'))

class frmLista(DialogType, DialogBase):

    def __init__(self, mapCanvas, encabezado, elementos):
        super().__init__()
        self.setupUi(self)
        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.mapCanvas = mapCanvas
        self.lleno_grilla(encabezado, elementos)
        self.tblLista.itemClicked.connect(self.elijo_item)
        self.cmdSalir.clicked.connect(self.salir)
        pass

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    def lleno_grilla(self, encabezado, elementos):
        self.tblLista.setRowCount(0)
        if len(elementos) > 0:
            self.tblLista.setRowCount(len(elementos))
            self.tblLista.setColumnCount(len(elementos[0]))

        for i in range (0, len(elementos)):
            for j in range (len(elementos[0])):
                item = QTableWidgetItem(str(elementos[i][j]))
                self.tblLista.setItem(i,j,item)
        self.tblLista.setHorizontalHeaderLabels(encabezado)

        self.tblLista.resizeColumnToContents(0)
        self.tblLista.resizeColumnToContents(1)
        self.tblLista.resizeColumnToContents(2)
        self.tblLista.resizeColumnToContents(3)
        self.tblLista.resizeColumnToContents(4)

    def elijo_item(self):
        try:
            id = int(self.tblLista.selectedItems()[2].text())
            if self.tblLista.selectedItems()[0].text()=='Nodos':
                n = self.mapCanvas.layerCount()
                layers = [self.mapCanvas.layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                        sel = lyr.getFeatures()
                        for ftr in sel:
                            if ftr.id()==id:
                                geom = ftr.geometry()
                                #box = geom.boundingBox()
                                box = geom.buffer(25,1).boundingBox()
                                self.mapCanvas.setExtent(box)
                                self.mapCanvas.refresh()
            if self.tblLista.selectedItems()[0].text()=='Lineas':
                n = self.mapCanvas.layerCount()
                layers = [self.mapCanvas.layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
                        sel = lyr.getFeatures()
                        for ftr in sel:
                            if ftr.id()==id:
                                geom = ftr.geometry()
                                box = geom.boundingBox()
                                self.mapCanvas.setExtent(box)
                                self.mapCanvas.refresh()
        except:
            pass

    def salir(self):
        self.close()
        pass
