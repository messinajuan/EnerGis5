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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_seccionadores.ui'))

class frmSeccionadores(DialogType, DialogBase):
        
    def __init__(self, conn, tension, geoname):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.tension = tension
        self.geoname = geoname

        self.inicio()
        pass

    def inicio(self):

        self.liwTipo.addItem("Interruptor")
        self.liwTipo.addItem("Seccionador")
        self.liwTipo.addItem("Reconectador")
        self.liwTipo.addItem("Seccionalizador")
        if float(self.tension) < 1000:
            self.liwTipo.addItem("Fusible")
        self.liwTipo.addItem("Otro")

        self.cmbCorriente.addItem("0.5")
        self.cmbCorriente.addItem("1")
        self.cmbCorriente.addItem("2")
        self.cmbCorriente.addItem("4")
        self.cmbCorriente.addItem("6")
        self.cmbCorriente.addItem("10")
        self.cmbCorriente.addItem("16")
        self.cmbCorriente.addItem("20")
        self.cmbCorriente.addItem("25")
        self.cmbCorriente.addItem("32")
        self.cmbCorriente.addItem("35")
        self.cmbCorriente.addItem("40")
        self.cmbCorriente.addItem("50")
        self.cmbCorriente.addItem("63")
        self.cmbCorriente.addItem("80")
        self.cmbCorriente.addItem("100")
        self.cmbCorriente.addItem("125")
        self.cmbCorriente.addItem("160")
        self.cmbCorriente.addItem("200")
        self.cmbCorriente.addItem("224")
        self.cmbCorriente.addItem("250")
        self.cmbCorriente.addItem("315")
        self.cmbCorriente.addItem("355")
        self.cmbCorriente.addItem("400")
        self.cmbCorriente.addItem("500")
        self.cmbCorriente.addItem("630")
        self.cmbCorriente.addItem("800")
        self.cmbCorriente.addItem("1000")
        self.cmbCorriente.addItem("1250")
        self.cmbCorriente.addItem("1600")
        self.cmbCorriente.addItem("2000")
        self.cmbCorriente.addItem("2500")
        self.cmbCorriente.addItem("3150")
        self.cmbCorriente.addItem("4000")
        self.cmbCorriente.addItem("5000")

        self.cmbPoderCorte.addItem("0")
        self.cmbPoderCorte.addItem("16")
        self.cmbPoderCorte.addItem("20")
        self.cmbPoderCorte.addItem("25")
        self.cmbPoderCorte.addItem("31.5")
        self.cmbPoderCorte.addItem("36")
        self.cmbPoderCorte.addItem("40")
        self.cmbPoderCorte.addItem("45")
        self.cmbPoderCorte.addItem("50")
        self.cmbPoderCorte.addItem("63")
        self.cmbPoderCorte.addItem("70")
        self.cmbPoderCorte.addItem("75")
        self.cmbPoderCorte.addItem("80")
        self.cmbPoderCorte.addItem("100")

        self.liwTipo.currentRowChanged.connect(self.elegir_aparato)

        cnn = self.conn
        cursor = cnn.cursor()
        rs = []
        cursor.execute("SELECT Val1, LEFT(Nodos.Val2,15), LEFT(RIGHT(Nodos.Val2,35),5), LEFT(RIGHT(Nodos.Val2,30),15), RIGHT(Nodos.Val2,15), Val4, UUCC FROM Nodos WHERE geoname=" + str(self.geoname))
        #convierto el cursor en array
        rs = tuple(cursor)
        cursor.close()

        for i in range (0, self.liwTipo.count()):
            if self.liwTipo.item(i).text() == str(rs[0][0]).strip():
                self.liwTipo.setCurrentRow(i)
                self.liwTipo.setFocus()

        for i in range (0, self.cmbParametro1.count()):
            if self.cmbParametro1.itemText(i) == str(rs[0][1]).strip():
                self.cmbParametro1.setCurrentIndex(i)

        for i in range (0, self.cmbPoderCorte.count()):
            if self.cmbPoderCorte.itemText(i) == str(rs[0][2]).strip():
                self.cmbPoderCorte.setCurrentIndex(i)

        for i in range (0, self.cmbParametro2.count()):
            if self.cmbParametro2.itemText(i) == str(rs[0][3]).strip():
                self.cmbParametro2.setCurrentIndex(i)

        for i in range (0, self.cmbParametro3.count()):
            if self.cmbParametro3.itemText(i) == str(rs[0][4]).strip():
                self.cmbParametro3.setCurrentIndex(i)

        if rs[0][5]=="Aereo-Subt":
            self.chkDescargadores.setChecked(True)
        self.txtUUCC.setText(rs[0][6])

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdUUCC.clicked.connect(self.uucc)
        self.cmdSalir.clicked.connect(self.salir)
        pass
        
    def elegir_aparato(self):

        self.lbl_parametro1.setText("Modelo")
        self.lbl_parametro2.setText("Tecnología")

        self.cmbParametro1.clear()
        self.cmbParametro2.clear()
        self.cmbParametro3.clear()

        if self.liwTipo.currentItem().text()=="Interruptor":
            self.cmbParametro1.addItem("De Potencia")
            self.cmbParametro1.addItem("Caja Moldeada")
            self.cmbParametro1.addItem("PIA")

            self.cmbParametro2.addItem("Aire")
            self.cmbParametro2.addItem("Aire Comprimido")
            self.cmbParametro2.addItem("Aceite")
            self.cmbParametro2.addItem("Vacío")
            self.cmbParametro2.addItem("SF6")
            self.cmbParametro2.addItem("Otro")

            self.lbl_parametro3.setText("Relé")
            self.cmbParametro3.addItem("Con Prot Relé")
            self.cmbParametro3.addItem("Sin Prot Relé")

        if self.liwTipo.currentItem().text()== "Seccionador":
            self.cmbParametro1.addItem("APR")
            self.cmbParametro1.addItem("Bornera Secc.")
            self.cmbParametro1.addItem("Cuch Giratorias")
            self.cmbParametro1.addItem("Cuch Deslizante")
            self.cmbParametro1.addItem("Col Giratoria")
            self.cmbParametro1.addItem("Pantógrafo")
            self.cmbParametro1.addItem("Semipantografo")
            self.cmbParametro1.addItem("Bajo Carga")

            self.cmbParametro2.addItem("Aire")
            self.cmbParametro2.addItem("Aire Comprimido")
            self.cmbParametro2.addItem("Aceite")
            self.cmbParametro2.addItem("Vacío")
            self.cmbParametro2.addItem("SF6")
            self.cmbParametro2.addItem("Otro")

            self.lbl_parametro3.setText("P.A.T.")
            self.cmbParametro3.addItem("Con P.A.T.")
            self.cmbParametro3.addItem("Sin P.A.T.")

        if self.liwTipo.currentItem().text()=="Reconectador":
            self.lbl_parametro3.setText("Marca")

        if self.liwTipo.currentItem().text()=="Seccionalizador":
            self.lbl_parametro3.setText("Marca")

        if self.liwTipo.currentItem().text()=="Fusible":
            self.cmbParametro1.addItem("HH")
            self.cmbParametro1.addItem("NH")
            self.cmbParametro1.addItem("DIAZED")
            self.cmbParametro1.addItem("NEOZED")
            self.cmbParametro1.addItem("Otro")
            self.lbl_parametro3.setText("Marca")

        if self.liwTipo.currentItem().text()=="Bornera Seccionable":
            self.lbl_parametro3.setText("Marca")

        #'15 - 5 - 15 - 15
        cnn = self.conn
        cursor = cnn.cursor()
        rs = []
        cursor.execute("SELECT LEFT(Nodos.Val2,15) FROM Nodos WHERE Nodos.Val1='" + self.liwTipo.currentItem().text() + "' AND (Elmt=2 OR Elmt=3) AND Nodos.Val2 <> '' GROUP BY LEFT(Nodos.Val2,15)")
        #convierto el cursor en array
        rs = tuple(cursor)
        cursor.close()

        for i in range (0, len(rs)):
            b_existe = False
            for j in range (0, self.cmbParametro1.count()):
                if self.cmbParametro1.itemText(j) == rs[0][0].strip() or self.cmbParametro1.itemText(j) == rs[0][0].strip() + ' *':
                    b_existe=True
            if b_existe==False:
                self.cmbParametro1.addItem (rs[0][0].strip() + ' *')

        cnn = self.conn
        cursor = cnn.cursor()
        rs = []
        cursor.execute("SELECT LEFT(RIGHT(Nodos.Val2,35),5) FROM Nodos WHERE Nodos.Val1='" + self.liwTipo.currentItem().text() + "' AND (Elmt=2 OR Elmt=3) AND Nodos.Val2 <> '' GROUP BY LEFT(RIGHT(Nodos.Val2,35),5)")
        #convierto el cursor en array
        rs = tuple(cursor)
        cursor.close()

        for i in range (0, len(rs)):
            b_existe = False
            for j in range (0, self.cmbPoderCorte.count()):
                if self.cmbPoderCorte.itemText(j) == rs[0][0].strip() or self.cmbPoderCorte.itemText(j) == rs[0][0].strip() + ' *':
                    b_existe=True
            if b_existe==False:
                self.cmbPoderCorte.addItem (rs[0][0].strip() + ' *')

        cnn = self.conn
        cursor = cnn.cursor()
        rs = []
        cursor.execute("SELECT LEFT(RIGHT(Nodos.Val2,30),15) FROM Nodos WHERE Nodos.Val1='" + self.liwTipo.currentItem().text() + "' AND (Elmt=2 OR Elmt=3) AND Nodos.Val2 <> '' GROUP BY LEFT(RIGHT(Nodos.Val2,30),15)")
        #convierto el cursor en array
        rs = tuple(cursor)
        cursor.close()

        for i in range (0, len(rs)):
            b_existe = False
            for j in range (0, self.cmbParametro2.count()):
                if self.cmbParametro2.itemText(j) == rs[0][0].strip() or self.cmbParametro2.itemText(j) == rs[0][0].strip() + ' *':
                    b_existe=True
            if b_existe==False:
                self.cmbParametro2.addItem (rs[0][0].strip() + ' *')

        cnn = self.conn
        cursor = cnn.cursor()
        rs = []
        cursor.execute("SELECT RIGHT(Nodos.Val2,15) FROM Nodos WHERE Nodos.Val1='" + self.liwTipo.currentItem().text() + "' AND (Elmt=2 OR Elmt=3) AND Nodos.Val2 <> '' GROUP BY RIGHT(Nodos.Val2,15)")
        #convierto el cursor en array
        rs = tuple(cursor)
        cursor.close()

        for i in range (0, len(rs)):
            b_existe = False
            for j in range (0, self.cmbParametro3.count()):
                if self.cmbParametro3.itemText(j) == rs[0][0].strip() or self.cmbParametro3.itemText(j) == rs[0][0].strip() + ' *':
                    b_existe=True
            if b_existe==False:
                self.cmbParametro3.addItem (rs[0][0].strip() + ' *')

    def aceptar(self):
        if self.geoname==0:
            return
        #'15 - 5 - 15 - 15
        cnn = self.conn
        cursor = cnn.cursor()
        str_set = "Val1='" + self.liwTipo.currentItem().text() + "'"
        val = "               " + self.cmbParametro1.currentText().strip()
        val = val[-15:]
        val2 = val
        val = "     " + self.cmbPoderCorte.currentText().strip()
        val = val[-5:]
        val2 = val2 + val
        val = "               " + self.cmbParametro2.currentText().strip()
        val = val[-15:]
        val2 = val2 + val
        val = "               " + self.cmbParametro3.currentText().strip()
        val = val[-15:]
        val2 = val2 + val

        str_set = str_set + ", Val2='" + val2 + "'"
        str_set = str_set + ", Val3='" + self.txtUUCC.text() + "'"

        if self.chkDescargadores.isChecked() == True:
            str_set = str_set + ", Val4='Aereo-Subt'"
        else:
            str_set = str_set + ", Val4=''"

        #QMessageBox.information(None, 'EnerGis 5', str_set)
        cursor.execute("UPDATE Nodos SET " + str_set + " WHERE Geoname=" + str(self.geoname))
        cnn.commit()
        #QMessageBox.information(None, 'EnerGis 5', str_set)
        self.close()
        pass

    def uucc(self):
        self.where = "Tipo = 'TELECONTROL'"

        if self.where != '':
            self.uucc = self.txtUUCC.text

            from .frm_elegir_uucc import frmElegirUUCC
            dialogo = frmElegirUUCC(self.conn, self.tension, self.where, self.uucc)
            dialogo.exec()
            self.txtUUCC.setText(dialogo.uucc)
            dialogo.close()
        pass

    def salir(self):
        self.close()
        pass
