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
from PyQt5.QtWidgets import QMessageBox, QTreeWidgetItem, QTableWidgetItem, QFileDialog
from PyQt5 import uic, QtCore

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_datos_seleccion.ui'))

class frmDatosSeleccion(DialogType, DialogBase):

    def __init__(self, mapCanvas, conn):
        super().__init__()
        self.setupUi(self)

        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        #self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.ftrs_nodos=[]
        self.ftrs_lineas=[]
        self.ftrs_postes=[]
        self.ftrs_parcelas=[]
        self.str_lista_nodos=""

        #armo las colecciones de objetos a mover en grupo
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            #QMessageBox.information(None, 'EnerGis 5', str(lyr.name()))
            if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                for ftr in lyr.selectedFeatures():
                    b_existe=False
                    for i in range (0, len(self.ftrs_nodos)):
                        if self.ftrs_nodos[i]==ftr.id():
                            b_existe=True
                    if b_existe==False and ftr.id()!=0:
                        self.ftrs_nodos.append(ftr.id())
            if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
                for ftr in lyr.selectedFeatures():
                    b_existe=False
                    for i in range (0, len(self.ftrs_lineas)):
                        if self.ftrs_lineas[i]==ftr.id():
                            b_existe=True
                    if b_existe==False and ftr.id()!=0:
                        self.ftrs_lineas.append(ftr.id())
            if lyr.name()[:6] == 'Postes':
                for ftr in lyr.selectedFeatures():
                    b_existe=False
                    for i in range (0, len(self.ftrs_postes)):
                        if self.ftrs_postes[i]==ftr.id():
                            b_existe=True
                    if b_existe==False and ftr.id()!=0:
                        self.ftrs_postes.append(ftr.id())
            if lyr.name() == 'Parcelas':
                for ftr in lyr.selectedFeatures():
                    b_existe=False
                    for i in range (0, len(self.ftrs_parcelas)):
                        if self.ftrs_parcelas[i]==ftr.id():
                            b_existe=True
                    if b_existe==False and ftr.id()!=0:
                        self.ftrs_parcelas.append(ftr.id())

        self.treeWidget.clear()
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setHeaderLabels(["Elemento", "Cant"])
        self.treeWidget.setColumnWidth(0, 250)
        self.treeWidget.setColumnWidth(1, 50)
        #self.treeWidget.setColumnAlignment(1, 1)

        if len(self.ftrs_nodos)>0:
            self.nodos = QTreeWidgetItem(["Nodos", str(len(self.ftrs_nodos))])
            self.treeWidget.addTopLevelItem(self.nodos)
        if len(self.ftrs_lineas)>0:
            self.lineas = QTreeWidgetItem(["Lineas", str(len(self.ftrs_lineas))])
            self.treeWidget.addTopLevelItem(self.lineas)
        if len(self.ftrs_postes)>0:
            self.postes = QTreeWidgetItem(["Postes", str(len(self.ftrs_postes))])
            self.treeWidget.addTopLevelItem(self.postes)
        if len(self.ftrs_parcelas)>0:
            self.parcelas = QTreeWidgetItem(["Parcelas", str(len(self.ftrs_parcelas))])
            self.treeWidget.addTopLevelItem(self.parcelas)

        cnn = self.conn
        #cursor = cnn.cursor()
        #elementos_nodos = []
        #cursor.execute("SELECT id, Descripcion FROM Elementos_Nodos")
        #convierto el cursor en array
        #elementos_nodos = tuple(cursor)
        #cursor.close()

        #--------------- ANALISIS DE CARGA ---------------
        self.str_lista_nodos='0'
        for ftr in self.ftrs_nodos:
            self.str_lista_nodos=self.str_lista_nodos + ',' + str(ftr)

        cursor = cnn.cursor()
        recordset = []
        cursor.execute("SELECT Sum(CAST([Val1] AS DECIMAL(8,2))) As kVA, Count(Nodos.Geoname) As Cant FROM Nodos WHERE Nodos.Elmt=4 AND Geoname IN (" + self.str_lista_nodos + ")")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        self.txtTransformadores.setText(str(recordset[0][1]))
        self.txtPotenciaInstalada.setText(str(recordset[0][0]))

        cursor = cnn.cursor()
        recordset = []
        cursor.execute("SELECT Count(Usuarios.id_usuario) As Cant FROM Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro WHERE ES=1 AND Suministros.id_nodo IN (" + self.str_lista_nodos + ")")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        self.txtUsuarios.setText(str(recordset[0][0]))

        cursor = cnn.cursor()
        recordset = []
        cursor.execute("SELECT Min(Energia_Facturada.Desde) As Desde, Max(Energia_Facturada.Hasta) As Hasta FROM Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro INNER JOIN Energia_Facturada ON Usuarios.id_usuario = Energia_Facturada.id_usuario WHERE Suministros.id_nodo IN (" + self.str_lista_nodos + ")")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        try:
            self.datDesde.setDate(recordset[0][0])
            self.datHasta.setDate(recordset[0][1])
            desde = recordset[0][0]
            hasta = recordset[0][1]
            import datetime
            if desde < hasta + datetime.timedelta(days=-365):
                desde = hasta + datetime.timedelta(days=-365)
                self.datDesde.setDate(desde)
            else:
                self.datHasta.setDate(recordset[0][0])
            self.cambio_fecha()
        except:
            pass

        #mediciones adicionales
        #"SELECT SUM(CAST(LEFT(RIGHT([mediciones].[nombre],LEN([mediciones].[nombre])-2),LEN([mediciones].[nombre])-5) AS DECIMAL(8,2))) FROM Nodos_Temp_" & Codigo_Usuario & " INNER JOIN mediciones ON Nodos_Temp_" & Codigo_Usuario & ".Geoname = mediciones.Geoname WHERE (((Right([mediciones].[Nombre],3))='kVA') AND ((Left([mediciones].[Nombre],2))='SC'));"
        #------------- FIN ANALISIS DE CARGA -------------

        self.cmdActualizarDatos.clicked.connect(self.actualizar_datos)
        self.cmdExportar.clicked.connect(self.exportar)
        self.cmdSalir.clicked.connect(self.salir)
        self.tblResultado.itemClicked.connect(self.elijo_item)
        self.treeWidget.itemDoubleClicked.connect(self.elijo_rama)
        self.datDesde.dateChanged.connect(self.cambio_fecha)
        self.datHasta.dateChanged.connect(self.cambio_fecha)
        self.txtFactorCarga.textChanged.connect(self.cambio_fc)

    def elijo_rama(self):
        cnn = self.conn
        cursor = cnn.cursor()

        items = self.treeWidget.selectedItems()
        if len(items) != 0:
            item = items[0]

        #self.treeWidget.resizeColumnToContents(0)
        #QMessageBox.information(None, 'EnerGis 5', str(item.data(0, QtCore.Qt.DisplayRole)))
        if item.data(1,QtCore.Qt.DisplayRole)!='0':

            #------------------------ NODOS --------------------------

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Nodos':
                str_lista='0'
                for ftr in self.ftrs_nodos:
                    #QMessageBox.information(None, 'EnerGis 5', str(ftr))
                    str_lista=str_lista + ',' + str(ftr)
                try:
                    cursor.execute('DROP TABLE #Nodos')
                except:
                    pass
                #QMessageBox.information(None, 'EnerGis 5', str_lista)
                cursor.execute("SELECT geoname, nombre, Nodos.descripcion, CASE WHEN LEFT(Elementos_Nodos.Descripcion,14) = 'Elemento Corte' THEN 'Elemento Corte' ELSE ISNULL(Elementos_Nodos.Descripcion, 'Nodo Simple') END AS elemento, tension, zona, alimentador, uucc INTO #Nodos FROM Nodos LEFT JOIN Elementos_Nodos ON Nodos.elmt=Elementos_Nodos.id WHERE geoname IN (" + str_lista + ")")
                cursor.commit()

                if item.childCount()==0:
                    cursor.execute('SELECT Elemento, count(*) FROM #Nodos GROUP BY Elemento')
                    elementos = tuple(cursor)
                    for elemento in elementos:
                        self.nodos.addChild(QTreeWidgetItem([elemento[0], str(elemento[1])]))
                    cursor.close()

                cursor = cnn.cursor()
                cursor.execute("SELECT * FROM #Nodos")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Nodo Simple':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Nodo Simple'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Fuente':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Fuente'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Elemento Corte':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Elemento Corte'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Centro Transformación':
                cursor.execute("SELECT #Nodos.*, Tension_2, Mat_Plataf, Tipo_ct, Potencia, Conexionado, Marca, N_Chapa FROM #Nodos LEFT JOIN Ct ON #Nodos.nombre=Ct.id_ct LEFT JOIN Transformadores ON #Nodos.nombre = Transformadores.id_ct WHERE elemento='Centro Transformación'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Suministro':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Suministro'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)

                if len(elementos)>0:
                    cursor = cnn.cursor()
                    cursor.execute("SELECT COUNT(Usuarios.id_usuario) FROM #Nodos INNER JOIN Suministros ON #Nodos.geoname=Suministros.id_nodo INNER JOIN Usuarios ON Suministros.id_suministro=Usuarios.id_suministro WHERE elemento='Suministro'")
                    usuarios = tuple(cursor)
                    encabezado = [column[0] for column in cursor.description]
                    cursor.close()
                    if usuarios[0][0]>0:
                        if item.childCount()==0:
                            item.addChild(QTreeWidgetItem(['Usuarios', str(usuarios[0][0])]))
                return

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Capacitor':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Capacitor'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Salida de Alimentador':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Salida de Alimentador'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Regulador de Tensión':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Regulador de Tensión'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Generador':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Generador'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Usuarios':
                cursor.execute("SELECT Usuarios.* FROM #Nodos INNER JOIN Suministros ON #Nodos.geoname=Suministros.id_nodo INNER JOIN Usuarios ON Suministros.id_suministro=Usuarios.id_suministro WHERE elemento='Suministro'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

            #------------------------ LINEAS --------------------------

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Lineas':
                str_lista='0'
                for ftr in self.ftrs_lineas:
                    #QMessageBox.information(None, 'EnerGis 5', str(ftr))
                    str_lista=str_lista + ',' + str(ftr)
                try:
                    cursor.execute('DROP TABLE #Lineas')
                except:
                    pass
                #QMessageBox.information(None, 'EnerGis 5', str_lista)
                cursor.execute("SELECT geoname, fase, descripcion, longitud, tension, zona, alimentador, disposicion, conservacion, ternas, acometida, uucc INTO #Lineas FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.elmt=Elementos_Lineas.id WHERE geoname IN (" + str_lista + ")")
                cursor.commit()

                if item.childCount()==0:
                    cursor.execute("SELECT tension, count(*) FROM #Lineas GROUP BY tension")
                    tensiones = tuple(cursor)
                    for tension in tensiones:
                        self.lineas.addChild(QTreeWidgetItem(['Lineas ' + str(tension[0]), str(tension[1])]))
                    cursor.close()

                cursor = cnn.cursor()
                cursor.execute("SELECT * FROM #Lineas")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

            if str(item.data(0,QtCore.Qt.DisplayRole))[:7]=='Lineas ':
                nombre_item=str(item.data(0,QtCore.Qt.DisplayRole))
                str_tension = nombre_item [7 - len(nombre_item):]
                cursor = cnn.cursor()
                cursor.execute("SELECT * FROM #Lineas WHERE tension=" + str_tension)
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return


            #------------------------ POSTES --------------------------


            #QMessageBox.information(None, 'EnerGis 5', str(item.data(0,QtCore.Qt.DisplayRole)))

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Postes':
                str_lista='0'
                for ftr in self.ftrs_postes:
                    str_lista=str_lista + ',' + str(ftr)
                try:
                    cursor.execute('DROP TABLE #Postes')
                except:
                    pass

                cursor.execute("SELECT geoname, elementos_postes.descripcion as montaje, altura, estructuras.descripcion as estructura, tipo, ternas, aislacion, tension, zona INTO #Postes FROM Postes INNER JOIN Elementos_Postes ON Postes.elmt=Elementos_Postes.id INNER JOIN Estructuras ON Postes.Estructura = Estructuras.id WHERE geoname IN (" + str_lista + ")")
                cursor.commit()
                #QMessageBox.information(None, 'EnerGis 5', str_lista)
                if item.childCount()==0:
                    cursor.execute("SELECT tension, count(*) FROM #Postes GROUP BY tension")
                    tensiones = tuple(cursor)
                    for tension in tensiones:
                        #QMessageBox.information(None, 'EnerGis 5', str(tension[0]))
                        self.postes.addChild(QTreeWidgetItem(['Postes ' + str(tension[0]), str(tension[1])]))
                    cursor.close()

                cursor = cnn.cursor()
                cursor.execute("SELECT * FROM #Postes")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

            if str(item.data(0,QtCore.Qt.DisplayRole))[:7]=='Postes ':
                nombre_item=str(item.data(0,QtCore.Qt.DisplayRole))

                str_tension = nombre_item [7 - len(nombre_item):]
                cursor = cnn.cursor()
                cursor.execute("SELECT * FROM #Postes WHERE tension=" + str_tension)
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return


            #------------------------ PARCELAS --------------------------


            #QMessageBox.information(None, 'EnerGis 5', str(item.data(0,QtCore.Qt.DisplayRole)))

            if str(item.data(0,QtCore.Qt.DisplayRole))=='Parcelas':

                str_lista='0'
                for ftr in self.ftrs_parcelas:
                    str_lista=str_lista + ',' + str(ftr)
                try:
                    cursor.execute('DROP TABLE #Parcelas')
                except:
                    pass

                cursor.execute("SELECT geoname,parcela,manzana,chacra,quinta,seccion,circunscripcion,zona INTO #Parcelas FROM Parcelas WHERE geoname IN (" + str_lista + ")")
                cursor.commit()

                cursor = cnn.cursor()
                cursor.execute("SELECT * FROM #Parcelas")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

    def cambio_fecha(self):

        fecha_desde = self.datDesde.date().toString('yyyyMMdd')
        fecha_hasta = self.datHasta.date().toString('yyyyMMdd')

        cnn = self.conn
        cursor = cnn.cursor()
        recordset = []
        cursor.execute("SELECT SUM(EtF) AS EtF FROM Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro INNER JOIN Energia_Facturada ON Usuarios.id_usuario = Energia_Facturada.id_usuario WHERE Suministros.id_nodo IN (" + self.str_lista_nodos + ") AND Energia_Facturada.Desde>='" + fecha_desde + "' AND Energia_Facturada.Hasta<='" + fecha_hasta + "'")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        self.txtEnergiaTotal.setText('0')
        self.txtHoras.setText('0')
        self.txtDemanda.setText('-')
        self.txtMemoria.clear()

        try:
            self.txtEnergiaTotal.setText(str(format(recordset[0][0], ".2f")))
            self.txtHoras.setText('0')
            desde = self.datDesde.date()
            hasta = self.datHasta.date()
            self.txtHoras.setText(str((desde.daysTo(hasta)+1)*24))
            self.calculo_demanda()
        except:
            pass

    def cambio_fc(self):
        self.txtDemanda.setText('-')
        self.calculo_demanda()

    def calculo_demanda(self):
        self.txtMemoria.clear()
        self.txtMemoria.append("Cálculo de la Demanda")
        self.txtMemoria.append("---------------------")
        self.txtMemoria.append("")

        try:
            energia = float(self.txtEnergiaTotal.text())
            horas = float(self.txtHoras.text())
            fc = float(self.txtFactorCarga.text())
            demanda = energia / horas / fc
            self.txtDemanda.setText(str(format(demanda, ".2f")))

            self.txtMemoria.append("    Energía Total = " + str(energia) + " [kWh]")
            self.txtMemoria.append("")

            self.txtMemoria.append(" Período Energías = desde " + str(self.datDesde.date().toString('yyyy-MM-dd')) + " hasta " + str(self.datHasta.date().toString('yyyy-MM-dd')))
            self.txtMemoria.append("    Horas Totales = " + str(horas) + " [h]")
            self.txtMemoria.append("")
            self.txtMemoria.append("  Factor de Carga : Es una medida de la tasa de utilización o eficiencia del uso de energía eléctrica. Un factor de carga bajo indica que la carga no está ejerciendo presión sobre el sistema eléctrico, mientras que los consumidores o los generadores que ejercen más presión sobre la distribución eléctrica tendrán un factor de carga alto.")
            self.txtMemoria.append("")
            self.txtMemoria.append("     Factor Carga = Carga Media / Carga Máxina = " + str(fc))
            self.txtMemoria.append("")
            self.txtMemoria.append("Demanda Calculada = Energía Total / (Horas Totales * Factor Carga)")
            self.txtMemoria.append("Demanda Calculada = " + str(format(demanda, ".2f")) + " [kW]")

        except:
            pass

    def lleno_grilla(self, encabezado, elementos):
        self.tblResultado.setRowCount(0)
        if len(elementos) > 0:
            self.tblResultado.setRowCount(len(elementos))
            self.tblResultado.setColumnCount(len(elementos[0]))
        for i in range (0, len(elementos)):
            for j in range (len(elementos[0])):
                item = QTableWidgetItem(str(elementos[i][j]))
                self.tblResultado.setItem(i,j,item)
        self.tblResultado.setHorizontalHeaderLabels(encabezado)

    def elijo_item(self):
        #QMessageBox.information(None, 'EnerGis 5', self.tblResultado.selectedItems()[0].text())
        #geom = QgsGeometry.fromWkt(self.tblResultado.selectedItems()[0].text())
        #box = geom.buffer(25,1).boundingBox()
        #self.mapCanvas.setExtent(box)
        self.mapCanvas.refresh()

    def exportar(self):
        #pip install xlwt
        import xlwt
        if self.tblResultado.rowCount()==0:
            return

        filename = QFileDialog.getSaveFileName(self, 'Guardar Archivo', '', ".xls(*.xls)")
        #QMessageBox.information(None, 'EnerGis 5', str(filename))

        if filename[0]=='' or filename[1]=='':
            return

        wbk = xlwt.Workbook()
        sheet = wbk.add_sheet("sheet", cell_overwrite_ok=True)
        for currentColumn in range(self.tblResultado.columnCount()):
            for currentRow in range(self.tblResultado.rowCount()):
                teext = str(self.tblResultado.item(currentRow, currentColumn).text())
                sheet.write(currentRow, currentColumn, teext)
        wbk.save(filename[0])

        QMessageBox.information(None, 'EnerGis 5', 'Exportado !')

    def actualizar_datos(self):
        if self.tblResultado.rowCount()==0:
            return
        items = self.treeWidget.selectedItems()
        if len(items) != 0:
            item = items[0]
        else:
            return

        if item.data(1,QtCore.Qt.DisplayRole)!='0':
            str_lista='0'
            for currentRow in range(self.tblResultado.rowCount()):
                str_lista=str_lista + ',' + str(self.tblResultado.item(currentRow, 0).text())

            #QMessageBox.information(None, 'EnerGis 5', str_lista)
            if str(item.data(0,QtCore.Qt.DisplayRole))=='Nodos':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.DisplayRole))=='Nodo Simple':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.DisplayRole))=='Fuente':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.DisplayRole))=='Elemento Corte':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.DisplayRole))=='Centro Transformación':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.DisplayRole))=='Suministro':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.DisplayRole))=='Capacitor':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.DisplayRole))=='Salida de Alimentador':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.DisplayRole))=='Regulador de Tensión':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.DisplayRole))=='Generador':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.DisplayRole))=='Usuarios':
                return
            if str(item.data(0,QtCore.Qt.DisplayRole))[:6]=='Lineas':
                from .frm_reasignar_lineas import frmReasignarLineas
                self.dialogo = frmReasignarLineas(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.DisplayRole))[:6]=='Postes':
                from .frm_reasignar_postes import frmReasignarPostes
                self.dialogo = frmReasignarPostes(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.DisplayRole))=='Parcelas':
                return

    def salir(self):
        self.close()
        pass
