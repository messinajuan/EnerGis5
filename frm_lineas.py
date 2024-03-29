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
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_lineas.ui'))

class frmLineas(DialogType, DialogBase):

    def __init__(self, tipo_usuario, mapCanvas, conn, tension, nodo_desde, nodo_hasta, longitud, obj, geoname):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.tension = tension
        self.nodo_desde = nodo_desde
        self.nodo_hasta = nodo_hasta
        self.longitud = longitud
        self.obj = obj
        self.geoname = geoname
        self.fase=123
        self.alimentador='<desc.>'
        self.descripcion = ''
        self.disposicion = 'Horizontal'
        self.conservacion = 'Bueno'
        self.fecha_instalacion = QDate.currentDate()
        self.elmt=0
        self.uucc=''
        self.where=''
        self.estilo = "0-Falso-1-1-0"
        self.estilo_catalogo = "0-Falso-1-1-0"

        vfloat = QDoubleValidator()
        self.txtLongitud.setValidator(vfloat)

        #QMessageBox.information(None, 'EnerGis 5', str(self.tipo_usuario))
        if self.tipo_usuario==4:
            self.cmdNueva.setEnabled(False)
            self.cmdEditar.setText('Datos')
            self.cmdAceptar.setEnabled(False)

        #QMessageBox.information(None, 'EnerGis 5', 'Inicio')
        cnn = self.conn

        self.lleno_lista()

        self.cmbFase.addItem('123')
        self.cmbFase.addItem('12')
        self.cmbFase.addItem('23')
        self.cmbFase.addItem('13')
        self.cmbFase.addItem('1')
        self.cmbFase.addItem('2')
        self.cmbFase.addItem('3')

        self.cmbDisposicion.addItem('No Aplica')
        self.cmbDisposicion.addItem('Horizontal')
        self.cmbDisposicion.addItem('Vertical')
        self.cmbDisposicion.addItem('Triangular')

        self.cmbTernas.addItem('Simple Terna')
        self.cmbTernas.addItem('2 Ternas')
        self.cmbTernas.addItem('3 Ternas')
        self.cmbTernas.addItem('4 Ternas')
        self.cmbTernas.addItem('Alumbrado')

        self.cmbEstado.addItem('Bueno')
        self.cmbEstado.addItem('Regular')
        self.cmbEstado.addItem('Malo')

        cursor = cnn.cursor()
        cursor.execute("SELECT Tension FROM Niveles_Tension WHERE Tension>=50")
        #convierto el cursor en array
        tensiones = tuple(cursor)
        cursor.close()

        n = self.mapCanvas.layerCount()
        j = 0
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Lineas':
                str_tension = lyr.name() [7 - len(lyr.name()):]
                for tension in tensiones:
                    if str(tension[0])==str_tension:
                        self.cmbCapa.addItem(str_tension)
                        if str_tension == str(self.tension):
                            j = self.cmbCapa.count() - 1

        self.cmbCapa.setCurrentIndex(j)

        if self.geoname != 0:
            self.lblLinea.setText(str(self.geoname))
            cursor = cnn.cursor()
            cursor.execute("SELECT Descripcion, Val1 AS I, Val2 AS Seccion, Val3 AS R1, Val4 AS X1, Val5 AS R0, Val6 AS X0, Val7 AS Xc, Fase, Elmt, Desde, Hasta, Longitud, Tension, Zona, Alimentador, Modificacion, Exp, Disposicion, Conservacion, Ternas, UUCC, Acometida, Lineas.Estilo, Elementos_Lineas.Estilo FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt=Elementos_Lineas.id WHERE Geoname=" + str(self.geoname))
            #convierto el cursor en array
            datos_linea = tuple(cursor)
            cursor.close()

            #self.liwElementos.setCurrentRow(0)
            for i in range (0, self.liwElementos.count()):
                if self.liwElementos.item(i).text() == str(datos_linea[0][0]):
                    self.liwElementos.setCurrentRow(i)
                    self.liwElementos.setFocus()

            #self.cmbCapa.setCurrentIndex(0)
            for i in range (0, self.cmbCapa.count()):
                if self.cmbCapa.itemText(i) == str(datos_linea[0][13]):
                    self.cmbCapa.setCurrentIndex(i)

            #self.cmbFase.setCurrentIndex(0)
            for i in range (0, self.cmbFase.count()):
                if self.cmbFase.itemText(i) == str(datos_linea[0][8]):
                    self.cmbFase.setCurrentIndex(i)

            self.lblNodoDesde.setText(str(datos_linea[0][10]))
            self.lblNodoHasta.setText(str(datos_linea[0][11]))

            self.txtLongitud.setText(str(format(datos_linea[0][12], ",.2f")).replace(',',''))

            self.elmt = datos_linea[0][9]
            #QMessageBox.information(None, 'inicio', str(self.elmt))

            self.tension = datos_linea[0][13]

            self.lblLongitud.setText(str(format(self.longitud, ",.2f")))
            self.lblZona.setText(str(datos_linea[0][14]))
            self.lblAlimentador.setText(str(datos_linea[0][15]))

            #setCurrent|(QDate::currentDate())
            #self.datInstalacion.setDisplayFormat('dd MM yyyy')
            self.datInstalacion.setDate(datos_linea[0][16])

            self.txtExpediente.setText(str(datos_linea[0][17]))

            self.cmbDisposicion.setCurrentIndex(0)
            for i in range (0, self.cmbDisposicion.count()):
                if self.cmbDisposicion.itemText(i) == str(datos_linea[0][18]):
                    self.cmbDisposicion.setCurrentIndex(i)

            self.cmbEstado.setCurrentIndex(0)
            for i in range (0, self.cmbEstado.count()):
                if self.cmbEstado.itemText(i) == str(datos_linea[0][19]):
                    self.cmbEstado.setCurrentIndex(i)

            self.cmbTernas.setCurrentIndex(0)
            for i in range (0, self.cmbTernas.count()):
                if self.cmbTernas.itemText(i) == str(datos_linea[0][20]):
                    self.cmbTernas.setCurrentIndex(i)

            if datos_linea[0][21] != None:
                self.txtUUCC.setText(datos_linea[0][21])

            if datos_linea[0][22]==1:
                self.chkAcometida.setChecked(True)

            self.estilo = datos_linea[0][23]
            self.estilo_catalogo = datos_linea[0][24]

            cursor = cnn.cursor()
            cursor.execute("SELECT Aux FROM mLineas WHERE Geoname=" + str(self.geoname))
            #convierto el cursor en array
            datos_linea = tuple(cursor)
            cursor.close()
            self.lblAux.setText('(' + str(datos_linea[0][0])  + ')')

        else: #Linea nueva

            cursor = cnn.cursor()
            cursor.execute("SELECT zona FROM Nodos WHERE geoname=" + str(self.nodo_desde))
            #convierto el cursor en array
            zona = tuple(cursor)
            cursor.close()
            self.lblZona.setText(zona[0][0])

            cursor = cnn.cursor()
            cursor.execute("SELECT MIN(Tension), ISNULL(MAX(Fase),'123'), MAX(Alimentador), MAX(Descripcion), MAX(Disposicion), MAX(Conservacion), MAX(Modificacion), MAX(Elmt), MAX(Lineas.Estilo), MAX(Lineas.UUCC) FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.elmt=Elementos_Lineas.id WHERE Desde=" + str(self.nodo_desde) + " OR Hasta=" + str(self.nodo_desde))
            #convierto el cursor en array
            datos_linea = tuple(cursor)
            cursor.close()

            if datos_linea[0][0]==None:
                cursor = cnn.cursor()
                cursor.execute("SELECT MIN(Tension), ISNULL(MAX(Fase),'123'), MAX(Alimentador), MAX(Descripcion), MAX(Disposicion), MAX(Conservacion), MAX(Modificacion), MAX(Elmt), MAX(Lineas.Estilo), MAX(Lineas.UUCC) FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.elmt=Elementos_Lineas.id WHERE Desde=" + str(self.nodo_hasta) + " OR Hasta=" + str(self.nodo_hasta))
                #convierto el cursor en array
                datos_linea2 = tuple(cursor)
                cursor.close()
                if datos_linea2[0][0]==None:
                    #fases = '123'
                    #alimentador = '<desc.>'
                    pass
                else:
                    self.tension = datos_linea2[0][0]
                    self.fase = datos_linea2[0][1]
                    self.alimentador = datos_linea2[0][2]
                    self.descripcion = datos_linea2[0][3]
                    self.disposicion = datos_linea2[0][4]
                    self.conservacion = datos_linea2[0][5]
                    self.fecha_instalacion = datos_linea2[0][6]
                    self.elmt = datos_linea2[0][7]
                    self.estilo = datos_linea2[0][8]
                    self.uucc = datos_linea2[0][9]
            else:
                #QMessageBox.information(None, 'EnerGis 5', str(datos_linea[0]))
                self.tension = datos_linea[0][0]
                self.fase = datos_linea[0][1]
                self.alimentador = datos_linea[0][2]
                self.descripcion = datos_linea[0][3]
                self.disposicion = datos_linea[0][4]
                self.conservacion = datos_linea[0][5]
                self.fecha_instalacion = datos_linea[0][6]
                self.elmt = datos_linea[0][7]
                self.estilo = datos_linea[0][8]
                self.uucc = datos_linea[0][9]

            self.lblNodoDesde.setText(str(self.nodo_desde))
            self.lblNodoHasta.setText(str(self.nodo_hasta))

            self.txtLongitud.setText(str(format(self.longitud, ",.2f")))
            self.lblLongitud.setText(str(format(self.longitud, ",.2f")))

            #self.liwElementos.setCurrentRow(0)
            for i in range (0, self.liwElementos.count()):
                if self.liwElementos.item(i).text() == self.descripcion:
                    self.liwElementos.setCurrentRow(i)
                    self.liwElementos.setFocus()

            #self.cmbCapa.setCurrentIndex(0)
            for i in range (0, self.cmbCapa.count()):
                if self.cmbCapa.itemText(i) == str(self.tension):
                    self.cmbCapa.setCurrentIndex(i)

            #self.cmbFase.setCurrentIndex(0)
            for i in range (0, self.cmbFase.count()):
                if self.cmbFase.itemText(i) == str(self.fase):
                    self.cmbFase.setCurrentIndex(i)

            #self.cmbDisposicion.setCurrentIndex(0)
            for i in range (0, self.cmbDisposicion.count()):
                if self.cmbDisposicion.itemText(i) == self.disposicion:
                    self.cmbDisposicion.setCurrentIndex(i)

            #self.cmbEstado.setCurrentIndex(0)
            for i in range (0, self.cmbEstado.count()):
                if self.cmbEstado.itemText(i) == self.conservacion:
                    self.cmbEstado.setCurrentIndex(i)

            self.lblAlimentador.setText(self.alimentador)
            self.datInstalacion.setDate(self.fecha_instalacion)

            self.txtUUCC.setText(self.uucc)
            pass

        self.cmdNueva.clicked.connect(self.nueva)
        self.cmdEditar.clicked.connect(self.editar)
        self.liwElementos.currentRowChanged.connect(self.elijo_elemento)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdUUCC.clicked.connect(self.elegir_uucc)
        self.cmdSalir.clicked.connect(self.salir)
        pass

    def closeEvent(self, event):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name() == 'Lineas_Temp':
                #QgsProject.instance().removeMapLayer(lyr)
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

    def lleno_lista(self):
        self.liwElementos.clear()
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT id, Descripcion, Estilo FROM Elementos_Lineas")
        #convierto el cursor en array
        self.elementos_lineas = tuple(cursor)
        cursor.close()
        for i in range (0, len(self.elementos_lineas)):
            if i==0: #coloco el primero como a seleccionar
                self.descripcion = self.elementos_lineas[i][1]
                self.estilo_catalogo = self.elementos_lineas[i][2]
            self.liwElementos.addItem(self.elementos_lineas[i][1])

    def nueva(self):
        from .frm_abm_lineas import frmAbmLineas
        dialogo = frmAbmLineas(self.tipo_usuario, self.conn, 0)
        dialogo.exec()
        self.lleno_lista()
        dialogo.close()

    def editar(self):
        if self.elmt==0:
            return
        from .frm_abm_lineas import frmAbmLineas
        self.dialogo = frmAbmLineas(self.tipo_usuario, self.conn, self.elmt)
        self.dialogo.show()

    def elijo_elemento(self):
        if self.liwElementos.currentItem()==None:
            return
        for i in range (0, len(self.elementos_lineas)):
            if self.liwElementos.currentItem().text()==self.elementos_lineas[i][1]:
                self.elmt = self.elementos_lineas[i][0]
                self.estilo_catalogo = self.elementos_lineas[i][2]
        #--------------------------------------------------

        cnn = self.conn
        cursor = cnn.cursor()
        if self.lblZona.text()=="Rural" or self.lblZona.text()=="Urbana":
            cursor.execute("SELECT TOP 1 ISNULL(UUCC,'') FROM lineas WHERE (Elmt = "  + str(self.elmt) + ") AND (Tension = " + str(self.tension) + ") AND (Zona = '" + self.lblZona.text() + "') GROUP BY UUCC HAVING (NOT (UUCC IS NULL)) ORDER BY COUNT(Geoname) DESC")
        else:
            cursor.execute("SELECT TOP 1 ISNULL(UUCC,'') FROM lineas WHERE (Elmt = "  + str(self.elmt) + ") AND (Tension = " + str(self.tension) + ") GROUP BY UUCC HAVING (NOT (UUCC IS NULL)) ORDER BY COUNT(Geoname) DESC")                
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()

        self.txtUUCC.setText("")
        if len(rst)>0:
            self.txtUUCC.setText(rst[0][0])
        pass

    def elegir_uucc(self):
        if self.chkAcometida.isChecked() == True:
            self.where = "Tipo = 'ACOMETIDA'"
        else:
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT Val8 FROM Elementos_Lineas WHERE id =" + str(self.elmt))
            #convierto el cursor en array
            rst = tuple(cursor)
            cursor.close()

            if rst[0][0] == "S":
                self.where = "Tipo = 'CABLE SUBTERRANEO'"
            else:
                self.where = "(Tipo = 'LINEA AEREA'"
                if self.tension <= 1000:
                    self.where = self.where + " AND Tipo_Instalacion = 'LBT')"
                elif self.tension > 1000 and self.tension < 66000:
                    if len(str(self.fase)) == 1:
                        self.where = self.where + " AND Tipo_Instalacion IN ('LMT RPT', 'LMT 7,6'))"
                    else:
                        self.where = self.where + " AND Tipo_Instalacion IN ('LMT 13,2', 'LMT 33'))"
                else:
                    self.where = self.where + " AND Tipo_Instalacion IN ('LAT 132', 'LAT 220', 'LAT 66'))"

        self.uucc = self.txtUUCC.text
        from .frm_elegir_uucc import frmElegirUUCC
        dialogo = frmElegirUUCC(self.conn, self.tension, self.where, self.uucc)
        dialogo.exec()
        if dialogo.uucc != '':
            self.txtUUCC.setText(dialogo.uucc)
        dialogo.close()
        pass

    def aceptar(self):
        obj = ''
        
        #QMessageBox.information(None, 'EnerGis 5', self.estilo)
        str_matriz = self.estilo.split("-")
        color = str_matriz[0]
        interleaved = str_matriz[1]
        if int(self.cmbCapa.currentText()) < 1000:
            ancho = len(self.cmbFase.currentText()) - 1
        elif int(self.cmbCapa.currentText()) >= 1000 and int(self.cmbCapa.currentText()) < 50000:
            ancho = len(self.cmbFase.currentText()) + 1
        else:
            ancho = len(self.cmbFase.currentText()) + 2
        unidad = str_matriz[4]
        str_matriz = self.estilo_catalogo.split("-")
        estilo = str_matriz[2]

        try:
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
                cursor.execute("SELECT MAX(Aux) FROM Lineas")
                auxlineas = tuple(cursor)
                cursor.close()
                aux = auxlineas[0][0] + 1

                cursor = cnn.cursor()
                cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
                rows = cursor.fetchall()
                cursor.close()
                srid = rows[0][0]

                obj = "geometry::STGeomFromText(" + "'" + self.obj.geometry().asWkt() + "'," + srid + ")"

                cursor = cnn.cursor()
                str_valores = str(id) + ", "
                str_valores = str_valores + "'" + self.cmbFase.currentText() + "', "
                str_valores = str_valores + str(self.elmt) + ", "
                str_valores = str_valores + self.lblNodoDesde.text() + ", "
                str_valores = str_valores + self.lblNodoHasta.text() + ", "
                str_valores = str_valores + "'" + "" + "', " #Quiebres
                str_valores = str_valores + self.txtLongitud.text().replace(',','') + ", "
                str_valores = str_valores + "'" + color + "-" + interleaved + "-" + estilo + "-" + str(ancho) + "-" + unidad + "', "
                str_valores = str_valores + self.cmbCapa.currentText() + ", "
                str_valores = str_valores + "'" + self.lblZona.text() + "', "
                str_valores = str_valores + "'" + self.lblAlimentador.text() + "', "
                str_valores = str_valores + str(aux) + ", "
                str_valores = str_valores + "'" + str(self.datInstalacion.date().toPyDate()).replace('-','') + "', "
                str_valores = str_valores + "'" + self.txtExpediente.text() + "', "
                str_valores = str_valores + "'" + self.cmbDisposicion.currentText() + "', "
                str_valores = str_valores + "'" + self.cmbEstado.currentText() + "', "
                str_valores = str_valores + "'" + self.cmbTernas.currentText() + "', "
                str_valores = str_valores + "'" + self.txtUUCC.text() + "', "
                if self.chkAcometida.isChecked() == True:
                    str_valores = str_valores + "'1', "
                else:
                    str_valores = str_valores + "'0', "
                str_valores = str_valores + obj
                cursor.execute("INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, Ternas, UUCC, Acometida, obj) VALUES (" + str_valores + ")")
                cnn.commit()

            else: #Si cambio algo -> UPDATE
                cnn = self.conn
                cursor = cnn.cursor()
                str_set = "Elmt=" + str(self.elmt) + ", "
                str_set = str_set + "Fase='" + self.cmbFase.currentText() + "', "
                str_set = str_set + "Quiebres='" + "" + "', "
                str_set = str_set + "Longitud=" + self.txtLongitud.text().replace(',','') + ", "
                str_set = str_set + "Tension=" + self.cmbCapa.currentText() + ", "
                str_set = str_set + "Estilo='" + color + "-" + interleaved + "-" + estilo + "-" + str(ancho) + "-" + unidad + "', "
                str_set = str_set + "Zona='" + self.lblZona.text() + "', "
                str_set = str_set + "Alimentador='" + self.lblAlimentador.text() + "', "
                str_set = str_set + "Modificacion='" + str(self.datInstalacion.date().toPyDate()).replace('-','') + "', "
                str_set = str_set + "Exp='" + self.txtExpediente.text() + "', "
                str_set = str_set + "Disposicion='" + self.cmbDisposicion.currentText() + "', "
                str_set = str_set + "Conservacion='" + self.cmbEstado.currentText() + "',"
                str_set = str_set + "Ternas='" + self.cmbTernas.currentText() + "',"
                str_set = str_set + "UUCC='" + self.txtUUCC.text() + "',"
                if self.chkAcometida.isChecked() == True:
                    str_set = str_set + "Acometida=1"
                else:
                    str_set = str_set + "Acometida=0"
                cursor.execute("UPDATE Lineas SET " + str_set + " WHERE Geoname=" + str(self.geoname))
                cursor.execute("UPDATE A SET d=o FROM (SELECT Nodos.Alimentador AS d, Lineas.Alimentador AS o FROM Lineas INNER JOIN Nodos ON Lineas.Alimentador <> Nodos.Alimentador AND Lineas.Desde = Nodos.Geoname WHERE (Nodos.Alimentador = N'<desc.>') AND (Nodos.Elmt <> 8) AND (Nodos.Elmt <> 3)) A")
                cursor.execute("UPDATE A SET d=o FROM (SELECT Nodos.Alimentador AS d, Lineas.Alimentador AS o FROM Lineas INNER JOIN Nodos ON Lineas.Alimentador <> Nodos.Alimentador AND Lineas.Hasta = Nodos.Geoname WHERE (Nodos.Alimentador = N'<desc.>') AND (Nodos.Elmt <> 8) AND (Nodos.Elmt <> 3)) A")
                cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.information(None, 'EnerGis 5', 'No se pudo actualizar la Base de Datos')

        self.close()
        pass

    def salir(self):
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("delete from lineas where desde=0 or hasta=0 or desde=hasta")
        cnn.commit()

        self.close()
        pass
