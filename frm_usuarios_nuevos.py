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
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox, QListWidgetItem, QTableWidgetItem
from qgis.core import QgsMapLayerType, QgsGeometry
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_usuarios_nuevos.ui'))

class frmUsuariosNuevos(DialogType, DialogBase):

    def __init__(self, mapCanvas, conn):
        super().__init__()
        self.setupUi(self)

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.move(20,200)

        self.mapCanvas = mapCanvas
        self.conn = conn

        self.suministro=''

        self.m_separar_suministros.triggered.connect(self.separar_suministros)
        self.m_suministros_sin_usuarios.triggered.connect(self.suministros_sin_usuarios)
        self.m_conectar_suministros_aislados.triggered.connect(self.conectar_suministros_aislados)
        self.m_suministros_con_coordenadas_externas.triggered.connect(self.suministros_con_coordenadas_externas)
        self.m_suministros_con_ejes_de_calle.triggered.connect(self.suministros_con_ejes_de_calle)
        self.m_suministros_por_catastro.triggered.connect(self.suministros_por_catastro)

        self.m_salir.triggered.connect(self.salir)

        self.cmdActualizar.clicked.connect(self.actualizar)
        self.cmdAproximar.clicked.connect(self.aproximar)

        self.tblSuministros.clicked.connect(self.elijo_suministro)

        self.actualizar_grilla()

    def separar_suministros(self):
        reply = QMessageBox.question(None, 'EnerGis 5', 'Desea separar a los usuarios del suministro ' + self.suministro + '?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("UPDATE Usuarios SET id_suministro=id_usuario WHERE id_suministro='" + self.suministro + "'")
            cursor.commit()
            pass
        pass

    def suministros_sin_usuarios(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT Nodos.Geoname, Nodos.Tension FROM ((Nodos LEFT JOIN Lineas AS Lineas_1 ON Nodos.Geoname = Lineas_1.Hasta) LEFT JOIN (Suministros LEFT JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo) LEFT JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE Nodos.Elmt = 6 GROUP BY Nodos.Geoname, Nodos.Tension, Nodos.Elmt HAVING (COUNT(Lineas_1.Geoname) + COUNT(Lineas.Geoname) = 1) AND (COUNT(Usuarios.id_usuario) = 0) OR (COUNT(Lineas_1.Geoname) + COUNT(Lineas.Geoname) = 0) AND (COUNT(Usuarios.id_usuario) = 0)")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                lyr.removeSelection()

        self.seleccion_n = []
        for n in range(1, len(recordset)):
            self.seleccion_n.append(recordset[n][0])

        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Temp':
                lyr.select(self.seleccion_n)

        from .frm_seleccion import frmSeleccion
        self.dialogo = frmSeleccion(self.mapCanvas)
        for m in range (0, len(self.seleccion_n)):
            self.dialogo.liwNodos.addItem(QListWidgetItem(str(self.seleccion_n[m])))
        self.dialogo.show()

        pass

    def conectar_suministros_aislados(self):
        #    Long_Maxima = 0
        #    frmConectarAislados.Show 1
        #    If Elemento1 = 0 Or Elemento2 = 0 Or Long_Maxima = 0 Then Exit Sub
        #    'Busco suministros aislados
        #    Adodc1.RecordSource = "SELECT Nodos.Geoname, Fases.fases, Nodos.Tension, Aux, XCoord, YCoord" & _
        #                          " FROM Nodos INNER JOIN (SELECT Suministros.id_nodo, MAX(Usuarios.fase) AS fases" & _
        #                          " FROM Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro" & _
        #                          " GROUP BY Suministros.id_nodo) AS Fases ON Nodos.Geoname = Fases.id_nodo" & _
        #                          " WHERE Nodos.Tension = " & str$(Tension) & " AND (((Nodos.Geoname) Not In (SELECT Desde FROM Lineas) AND (Nodos.Geoname) Not In (SELECT Hasta" & _
        #                          " FROM Lineas AS Lineas_1)) AND ((Nodos.Elmt)=6))"
        #    Adodc1.Refresh
        #    If Adodc1.Recordset.RecordCount <> 0 Then frmBarra.ProgressBar1.Max = Adodc1.Recordset.RecordCount
        #    'Dibujo las lineas
        #    Do While Not Adodc1.Recordset.EOF
        #        frmBarra.Caption = "Conectando Suministros"
        #        frmBarra.Visible = True
        #        frmBarra.ZOrder 0
        #        frmBarra.ProgressBar1.Value = frmBarra.ProgressBar1.Value + 1
        #        X1 = Adodc1.Recordset("XCoord")
        #        Y1 = Adodc1.Recordset("YCoord")
        #        'Busco el nodo del mismo nivel de tensión a menos de 20m
        #        If Fuente_Datos = 2 Then
        #            Adodc2.RecordSource = "SELECT TOP 1 Geoname, Zona, Alimentador, subzona, Elmt, Tension, Aux, XCoord, YCoord" & _
        #                                  " FROM nodos" & _
        #                                  " WHERE Sqrt(Power(XCoord - " & str$(X1) & ", 2) + Power(YCoord - " & str$(Y1) & ", 2)) <= " & str$(Long_Maxima) & _
        #                                  " AND nodos.Elmt = 0 AND nodos.Tension = " & Adodc1.Recordset("tension") & _
        #                                  " ORDER BY Sqrt(Power(XCoord - " & str$(X1) & ", 2) + Power(YCoord - " & str$(Y1) & ", 2))"
        #            Adodc2.Refresh
        #        Else
        #            Adodc2.RecordSource = "SELECT TOP 1 nodos.Geoname, nodos.Zona, nodos.Alimentador, nodos.subzona, nodos.Elmt, nodos.Tension, nodos.Aux, nodos.XCoord, nodos.YCoord" & _
        #                                  " FROM nodos" & _
        #                                  " WHERE nodos.Elmt = 0 AND nodos.Tension = " & Adodc1.Recordset("tension") & _
        #                                  " AND Sqr((XCoord - " & str$(X1) & ") ^ 2 + (YCoord - " & str$(Y1) & ") ^ 2) <= " & str$(Long_Maxima) & _
        #                                  " ORDER BY Sqr((XCoord - " & str$(X1) & ") ^ 2 + (YCoord - " & str$(Y1) & ") ^ 2)"
        #            Adodc2.Refresh
        #        End If
        #        If Adodc2.Recordset.RecordCount > 0 Then
        #            frmEditor.Map1(IdMapa).CenterX = X1
        #            frmEditor.Map1(IdMapa).CenterY = Y1
        #            frmEditor.Map1(IdMapa).Zoom = 100
        #            Dfb = MsgBox("Conectar Suministro ? La opción de cancelar detiene toda la operación de conectar.", vbYesNoCancel)
        #            If Dfb = 2 Then
        #                Unload frmBarra
        #                Exit Sub
        #            End If
        #            If Dfb = 6 Then
        #                Node_From = Adodc1.Recordset("geoname")
        #                Node_To = Adodc2.Recordset("geoname")
        #                Node_Pos_From = Adodc1.Recordset("aux")
        #                Node_Pos_To = Adodc2.Recordset("aux")
        #                fase = Adodc1.Recordset("fases")
        #                If InStr(1, Trim(CStr(mnodos(Node_Pos_To, 37))), Trim(CStr(fase)), vbTextCompare) = 0 Then
        #                    If mnodos(Node_Pos_To, 37) > 0 Then
        #                        If Len(Trim(CStr(fase))) = 123 Then
        #                            fase = 123
        #                        Else
        #                            fase = CInt(Left$(Trim(CStr(mnodos(Node_Pos_To, 37))), 1))
        #                        End If
        #                    End If
        #                End If
        #                Zon_Lin = Adodc2.Recordset("zona")
        #                Alim_Lin = Adodc2.Recordset("alimentador")
        #                Volt_Lin = Adodc1.Recordset("tension")
        #                Disp_Lin = "No Aplica"
        #                Exp_Lin = "1111/2001"
        #                X2 = Adodc2.Recordset("XCoord")
        #                Y2 = Adodc2.Recordset("YCoord")
        #                Elemento = Elemento2
        #                If fase <> 123 Then Elemento = Elemento1
        #                'genero el nodo
        #                Iid = NuevoIid
        #                Set Ftr22 = New MapXLib.Feature
        #                Set NewObj22 = New MapXLib.Feature
        #                'objeto Grafico
        #'                Ftr22.Attach frmEditor.Map1(IdMapa)
        #                NewObj22.Attach frmEditor.Map1(IdMapa)
        #                NewObj22.Type = miFeatureTypeLine
        #                NewObj22.Style = frmEditor.Map1(IdMapa).DefaultStyle
        #                Set Pts1 = New MapXLib.Points
        #                Pts1.AddXY X1, Y1
        #                Pts1.AddXY X2, Y2
        #                For l_idtension = 1 To Cant_Niveles_Tension
        #                    If C_LINES(l_idtension, 2) = Volt_Lin Then
        #                        IdTension = l_idtension
        #                    End If
        #                Next l_idtension
        #                NewObj22.Parts.Add Pts1
        #                Set Ftr22 = frmEditor.Map1(IdMapa).Layers(C_LINES(IdTension, 1)).AddFeature(NewObj22)
        #                Set NewObj22 = Nothing
        #                Longitud = Ftr22.Length
        #                Ftr22.KeyValue = Iid
        #                Ftr22.Update
        #                DoEvents
        #                'registro BD
        #                AdoCon.BeginTrans
        #                    If str_estilo = "" Then str_estilo = "0-0-2-0-0"
        #                    '*******************************************
        #                    Set RS = CreateObject("Adodb.Recordset")
        #                    RS.Open "SELECT MAX(Aux) FROM Lineas", AdoCon, adOpenStatic, adLockReadOnly, adCmdText
        #                    n_lineas = RS(0) + 1
        #                    If RS.State = 1 Then RS.Close
        #                    '*******************************************
        #                    If EjecutarSqlTrans("INSERT INTO Lineas (Geoname,Fase,Elmt,Desde,Hasta,Estilo,Zona,Alimentador,Longitud,Tension,Aux,Disposicion,Modificacion,Exp,Conservacion,Ternas,Acometida) VALUES (" & Iid & ",'" & fase & "'," & Elemento & "," & Node_From & "," & Node_To & ",'" & str_estilo & "','" & Zon_Lin & "','" & Alim_Lin & "'," & str$(Longitud) & "," & Volt_Lin & "," & n_lineas & ",'" & Disp_Lin & "'," & Caracter_Fecha & str_fecha & Caracter_Fecha & ",'" & Exp_Lin & "','Bueno','Simple Terna',1)") = False Then
        #                        MsgBox "No se puede insertar la línea en la base de datos", vbCritical
        #                        'MsgBox "(" & Iid & ",'" & fase & "'," & Elemento & "," & Node_From & "," & Node_To & ",'" & str_estilo & "','" & Zon_Lin & "','" & Alim_Lin & "'," & str$(Longitud) & "," & Volt_Lin & "," & n_lineas + 1 & ",'" & Disp_Lin & "'," & Caracter_Fecha & str_fecha & Caracter_Fecha & ",'" & Exp_Lin & "')"
        #                        Delete_Feature frmEditor.Map1(IdMapa).Layers.Item(C_LINES(IdTension, 1)), Ftr22.FeatureID
        #                        AdoCon.RollbackTrans
        #                        n_lineas = n_lineas - 1
        #                        Exit Sub
        #                    Else
        #                        '*********************************************************************
        #                        Call Agrego_Linea(Iid, Node_Pos_From, Node_Pos_To, Volt_Lin, fase, n_lineas)
        #                        EjecutarSqlTrans "INSERT INTO Cambios (Tipo, Geoname, Desde, Hasta, Tension, Elmt, Aux, Usuario) VALUES (2," & Iid & "," & Node_Pos_From & "," & Node_Pos_To & "," & Volt_Lin & "," & fase & "," & n_lineas & ",'" & Codigo_Usuario & "')"
        #                        '*********************************************************************
        #                    End If
        #                AdoCon.CommitTrans
        #                Set Ftr22 = Nothing
        #                Set NewObj22 = Nothing
        #            End If
        #        End If
        #        Adodc1.Recordset.MoveNext
        #    Loop
        #    MsgBox "Suministros conectados", vbInformation
        pass

    def suministros_con_coordenadas_externas(self):
        #        EjecutarSql "UPDATE A SET d=o FROM (SELECT Suministros_Coordenadas.id_suministro as d, Usuarios.id_suministro as o FROM Suministros_Coordenadas INNER JOIN Usuarios ON Suministros_Coordenadas.id_usuario = Usuarios.id_usuario INNER JOIN Suministros_Nuevos ON Usuarios.id_suministro = Suministros_Nuevos.id_suministro WHERE Suministros_Coordenadas.id_suministro <> Usuarios.id_suministro) A"
        #        Adodc2.RecordSource = "SELECT Suministros_Coordenadas.id_usuario, Suministros_Coordenadas.Lat, Suministros_Coordenadas.Lon, Suministros_Coordenadas.Tension, Suministros_Coordenadas.id_suministro" & _
        #                              " FROM Nodos RIGHT JOIN ((Suministros_Coordenadas INNER JOIN Usuarios ON Suministros_Coordenadas.id_usuario = Usuarios.id_usuario) LEFT JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) ON Nodos.Geoname = Suministros.id_nodo" & _
        #                              " WHERE (((Nodos.Geoname) Is Null))" & _
        #                              " GROUP BY Suministros_Coordenadas.id_usuario, Suministros_Coordenadas.Lat, Suministros_Coordenadas.Lon, Suministros_Coordenadas.Tension, Suministros_Coordenadas.id_suministro"
        #        Adodc2.Refresh
        #        If Adodc2.Recordset.RecordCount <> 0 Then
        #            frmBarra.ProgressBar1.Max = Adodc2.Recordset.RecordCount
        #            frmBarra.ProgressBar1.Value = 0
        #            Adodc2.Recordset.MoveFirst
        #            Do While Not Adodc2.Recordset.EOF
        #                frmBarra.Caption = "Insertando Suministros Nuevos"
        #                frmBarra.Visible = True
        #                frmBarra.ZOrder 0
        #                frmBarra.ProgressBar1.Value = frmBarra.ProgressBar1.Value + 1
        #                x = Round(frmConvertirCoordenadas.x(Adodc2.Recordset("lon"), Adodc2.Recordset("lat")), 3)
        #                y = Round(frmConvertirCoordenadas.y(Adodc2.Recordset("lon"), Adodc2.Recordset("lat")), 3)
        #                Set Pt = New MapXLib.Point
        #                Pt.Set Px, Py
        #                Nivel_Tension = Adodc2.Recordset("tension")
        #                b_existe = False
        #                'Me fijo si ya hay un punto en esa zona
        #                Set Ftrs = frmEditor.Map1(IdMapa).Layers(Curr_Arch & "_no_" & Nivel_Tension).SearchWithinDistance(Pt, 10, miUnitMeter, miSearchTypePartiallyWithin)
        #                For Each Ftr3 In Ftrs
        #                    If Not Ftr3 Is Nothing Then
        #                        Adodc3.RecordSource = "SELECT geoname FROM Nodos WHERE elmt=6 AND geoname=" & Ftr3.KeyValue
        #                        Adodc3.Refresh
        #                        If Adodc3.Recordset.RecordCount > 0 Then
        #                            b_existe = True
        #                            If AdoCon.State = 0 Then AdoCon.Open
        #                            AdoCon.BeginTrans
        #                                b_transaccion = True
        #                                frmEditor.Map1(IdMapa).CenterX = x
        #                                frmEditor.Map1(IdMapa).CenterY = y
        #                                frmEditor.Map1(IdMapa).Refresh
        #                                'genero el suministro
        #                                EjecutarSqlTrans ("DELETE FROM Suministros WHERE id_suministro='" & Adodc2.Recordset("id_suministro") & "'")
        #                                EjecutarSqlTrans ("INSERT INTO Suministros (id_nodo, id_suministro) VALUES (" & Adodc3.Recordset("geoname") & ",'" & Adodc2.Recordset("id_suministro") & "')")
        #                                'coloco al usuario en el suministro
        #                                EjecutarSqlTrans ("UPDATE Usuarios SET id_suministro='" & Adodc2.Recordset("id_suministro") & "' WHERE id_usuario=" & caracter_IdUsuario & Adodc2.Recordset("id_usuario") & caracter_IdUsuario)
        #                                'borro el registro original
        #                                'EjecutarSqlTrans ("DELETE FROM Suministros_Coordenadas WHERE id_usuario=" & caracter_idusuario & Adodc2.Recordset("id_usuario") & caracter_idusuario)
        #                            AdoCon.CommitTrans
        #                            b_transaccion = False
        #                            GoTo 1
        #                        End If
        #                    End If
        #                Next
        #1:
        #                If b_existe = False Then
        #                    If AdoCon.State = 0 Then AdoCon.Open
        #                    'genero el nodo
        #                    Iid = NuevoIid
        #                    AdoCon.BeginTrans
        #                        b_transaccion = True
        #                        'Insert_Point frmEditor.Map1(IdMapa).Layers(Curr_Arch & "_no_" & Nivel_Tension), x, y, frmEditor.Map1(IdMapa).DefaultStyle, Iid
        #                        Ftr1.Attach frmEditor.Map1(IdMapa)
        #                        Ftr1.Type = miFeatureTypeSymbol
        #                        Ftr1.Point.Set x, y
        #                        Ftr1.Style = frmEditor.Map1(IdMapa).DefaultStyle
        #                        frmEditor.Map1(IdMapa).Refresh
        #                        DoEvents
        #                        Set Ftr2 = frmEditor.Map1(IdMapa).Layers(Curr_Arch & "_no_" & Nivel_Tension).AddFeature(frmEditor.Map1(IdMapa).FeatureFactory.CreateSymbol(Ftr1.Point, Ftr1.Style))
        #                        Set Ftr1 = Nothing
        #                        Ftr2.KeyValue = Iid
        #                        Ftr2.Update
        #                        DoEvents
        #                        frmEditor.Map1(IdMapa).CenterX = x
        #                        frmEditor.Map1(IdMapa).CenterY = y
        #                        frmEditor.Map1(IdMapa).Refresh
        #                        Set RS = CreateObject("Adodb.Recordset")
        #                        RS.Open "SELECT MAX(Aux) FROM Nodos", AdoCon, adOpenStatic, adLockReadOnly, adCmdText
        #                        n_nodos = RS(0) + 1
        #                        If RS.State = 1 Then RS.Close
        #                        '*******************************************
        #                        EjecutarSqlTrans ("INSERT INTO Nodos (Geoname, elmt, XCoord, YCoord, Tension, Estilo, Aux) VALUES (" & Iid & ",6," & str$(x) & "," & str(y) & "," & Nivel_Tension & ",'35 - EnerGIS - 0 - 4227327 - 10 - 0'," & n_nodos & ")")
        #                        '*******************************************
        #                        Call Agrego_Nodo(Iid, Nivel_Tension, n_nodos)
        #                        EjecutarSqlTrans "INSERT INTO Cambios (Tipo, Geoname, Desde, Hasta, Tension, Elmt, Aux, Usuario) VALUES (1," & Iid & ",0,0," & Nivel_Tension & ",0," & n_nodos & ",'" & Codigo_Usuario & "')"
        #                        '*******************************************
        #                        'genero el suministro
        #                        EjecutarSqlTrans ("DELETE FROM Suministros WHERE id_suministro='" & Adodc2.Recordset("id_suministro") & "'")
        #                        EjecutarSqlTrans ("INSERT INTO Suministros (id_nodo, id_suministro) VALUES (" & Iid & ",'" & Adodc2.Recordset("id_suministro") & "')")
        #                        'coloco al usuario en el suministro
        #                        EjecutarSqlTrans ("UPDATE Usuarios SET id_suministro='" & Adodc2.Recordset("id_suministro") & "' WHERE id_usuario=" & caracter_IdUsuario & Adodc2.Recordset("id_usuario") & caracter_IdUsuario & " AND id_suministro<>'" & Adodc2.Recordset("id_suministro") & "'")
        #                        'borro el registro original
        #                        'EjecutarSqlTrans ("DELETE FROM Suministros_Coordenadas WHERE id_usuario=" & caracter_idusuario & Adodc2.Recordset("id_usuario") & caracter_idusuario)
        #                    AdoCon.CommitTrans
        #                    b_transaccion = False
        #                End If
        #                Adodc2.Recordset.MoveNext
        #            Loop
        #            If AdoCon.State = 1 Then AdoCon.Close
        #        End If
        #    End If
        #    frmBarra.ProgressBar1.Value = 0
        #    frmBarra.Visible = False
        #    MsgBox "Suministros agregados", vbInformation
        pass

    def suministros_con_ejes_de_calle(self):
        #    distancia_desde_eje = 16
        #        Adodc2.RecordSource = "SELECT count(*) FROM VW_GISGEOCODIFICAR WHERE ciudad='*'" ' Si tiene * no tomo en cuenta localidad, o sea hay ids de calle unicos !
        #        Adodc2.Refresh
        #        If Adodc2.Recordset(0) = 0 Then
        #            b_considerar_localidad = False
        #        Else
        #            b_considerar_localidad = True
        #        End If
        #       If b_considerar_localidad = False Then
        #            Adodc1.RecordSource = "SELECT * FROM VW_GISGEOCODIFICAR"
        #            Adodc1.Refresh
        #            If Adodc1.Recordset.RecordCount > 0 Then Adodc1.Recordset.MoveFirst
        #            Do While Not Adodc1.Recordset.EOF
        #                EjecutarSql "DELETE FROM Suministros_Coordenadas WHERE id_usuario=" & caracter_IdUsuario & Adodc1.Recordset("id_usuario") & caracter_IdUsuario
        #                Altura = Adodc1.Recordset("altura")
        #                SQL = "SELECT * FROM Ejes WHERE (Ciudad = " & Adodc1.Recordset("Ciudad") & " AND Calle = " & Adodc1.Recordset("Calle") & " AND IzqDe <= " & Altura & " AND IzqA > " & Altura & ")"
        #                SQL = SQL & " OR (Ciudad = " & Adodc1.Recordset("Ciudad") & " AND Calle = " & Adodc1.Recordset("Calle") & " AND DerDe <= " & Altura & " AND DerA > " & Altura & ")"
        #                SQL = SQL & " OR (Ciudad = " & Adodc1.Recordset("Ciudad") & " AND Calle = " & Adodc1.Recordset("Calle") & " AND IzqA = " & Altura & ")"
        #                SQL = SQL & " OR (Ciudad = " & Adodc1.Recordset("Ciudad") & " AND Calle = " & Adodc1.Recordset("Calle") & " AND DerA = " & Altura & ")"
        #                Adodc2.RecordSource = SQL
        #                Adodc2.Refresh
        #                If Adodc2.Recordset.RecordCount > 0 Then
        #                    Xdes = 0
        #                    Ydes = 0
        #                    Set FindObject = frmEditor.Map1(IdMapa).Layers(C_AXIS).Find.Search(Adodc2.Recordset("Geoname"))
        #                    If (FindObject.FindRC Mod 10 = 1) Then
        #                        Xz1 = FindObject.Parts.Item(1).Item(1).x
        #                        Yz1 = FindObject.Parts.Item(1).Item(1).y
        #                        Xz2 = FindObject.Parts.Item(1).Item(2).x
        #                        Yz2 = FindObject.Parts.Item(1).Item(2).y
        #                        'aca hay que ver si vengo con pares o impares, entonces veo la longitud por derecha y por izquierda que pueden ser <>s
        #                        L_Cuadra = Abs(Adodc2.Recordset("IzqA") - Adodc2.Recordset("IzqDe"))
        #                        If Altura / 100 = 0 Then
        #                            D = 0
        #                        Else
        #                            D = frmEditor.Map1(IdMapa).Distance(Xz1, Yz1, Xz2, Yz2) - distancia_desde_eje * 2
        #                            D = ((Altura - Adodc2.Recordset("IzqDe")) * D / L_Cuadra) + distancia_desde_eje
        #                        End If
        #                        If Altura / 2 = Int(Altura / 2) Then 'par
        #                            EsPar = True
        #                        Else 'impar
        #                            EsPar = False
        #                        End If
        #                        Dfb = ColocarPuntoEje(Xz1, Yz1, Xz2, Yz2, D, EsPar, distancia_desde_eje, Xdes, Ydes)
        #                        XLat = str$(frmConvertirCoordenadas.Latitud(Xdes, Ydes))
        #                        XLon = str$(frmConvertirCoordenadas.Longitud(Xdes, Ydes))
        #                        EjecutarSql "INSERT INTO Suministros_Coordenadas (id_usuario, Lat, Lon, Tension, id_suministro) VALUES (" & caracter_IdUsuario & Adodc1.Recordset("id_usuario") & caracter_IdUsuario & "," & XLat & "," & XLon & "," & Adodc1.Recordset("Tension") & ",'" & Adodc1.Recordset("id_suministro") & "')"
        #                    End If
        #                End If
        #                Adodc1.Recordset.MoveNext
        #            Loop
        #        Else
        #            Adodc1.RecordSource = "SELECT * FROM VW_GISGEOCODIFICAR"
        #            Adodc1.Refresh
        #            If Adodc1.Recordset.RecordCount > 0 Then Adodc1.Recordset.MoveFirst
        #            Do While Not Adodc1.Recordset.EOF
        #                EjecutarSql "DELETE FROM Suministros_Coordenadas WHERE id_usuario=" & caracter_IdUsuario & Adodc1.Recordset("id_usuario") & caracter_IdUsuario
        #                Altura = Adodc1.Recordset("altura")
        #                SQL = "SELECT * FROM Ejes WHERE (Calle = " & Adodc1.Recordset("Calle")
        #                SQL = SQL & " AND IzqDe <= " & Altura & " AND IzqA > " & Altura & ")"
        #                SQL = SQL & " OR ( Calle = " & Adodc1.Recordset("Calle") & " AND DerDe <= " & Altura & " AND DerA > " & Altura & ")"
        #                SQL = SQL & " OR ( Calle = " & Adodc1.Recordset("Calle") & " AND IzqA = " & Altura & ")"
        #                SQL = SQL & " OR ( Calle = " & Adodc1.Recordset("Calle") & " AND DerA = " & Altura & ")"
        #                Adodc2.RecordSource = SQL
        #                Adodc2.Refresh
        #                If Adodc2.Recordset.RecordCount > 0 Then
        #                    Xdes = 0
        #                    Ydes = 0
        #                    Set FindObject = frmEditor.Map1(IdMapa).Layers(C_AXIS).Find.Search(Adodc2.Recordset("Geoname"))
        #                    If (FindObject.FindRC Mod 10 = 1) Then
        #                        Xz1 = FindObject.Parts.Item(1).Item(1).x
        #                        Yz1 = FindObject.Parts.Item(1).Item(1).y
        #                        Xz2 = FindObject.Parts.Item(1).Item(2).x
        #                        Yz2 = FindObject.Parts.Item(1).Item(2).y
        #                        'aca hay que ver si vengo con pares o impares, entonces veo la longitud por derecha y por izquierda que pueden ser <>s
        #                        L_Cuadra = Abs(Adodc2.Recordset("IzqA") - Adodc2.Recordset("IzqDe"))
        #                        If Altura / 100 = 0 Then
        #                            D = 0
        #                        Else
        #                            D = frmEditor.Map1(IdMapa).Distance(Xz1, Yz1, Xz2, Yz2) - distancia_desde_eje * 2
        #                            D = ((Altura - Adodc2.Recordset("IzqDe")) * D / L_Cuadra) + distancia_desde_eje
        #                        End If
        #                        If Altura / 2 = Int(Altura / 2) Then 'par
        #                            EsPar = True
        #                        Else 'impar
        #                            EsPar = False
        #                        End If
        #                        Dfb = ColocarPuntoEje(Xz1, Yz1, Xz2, Yz2, D, EsPar, distancia_desde_eje, Xdes, Ydes)
        #                        XLat = str$(frmConvertirCoordenadas.Latitud(Xdes, Ydes))
        #                        XLon = str$(frmConvertirCoordenadas.Longitud(Xdes, Ydes))
        #                        EjecutarSql "INSERT INTO Suministros_Coordenadas (id_usuario, Lat, Lon, Tension, id_suministro) VALUES (" & caracter_IdUsuario & Adodc1.Recordset("id_usuario") & caracter_IdUsuario & "," & XLat & "," & XLon & "," & Adodc1.Recordset("Tension") & ",'" & Adodc1.Recordset("id_suministro") & "')"
        #                    End If
        #                End If
        #                Adodc1.Recordset.MoveNext
        #            Loop
        #        End If
        #    End If
        #    Call m_dibujar_nodos_coordenadas_Click
        pass

    def suministros_por_catastro(self):
        #    If Tipo_Uso = 1 Then
        #        Adodc2.RecordSource = "SELECT Usuarios.id_usuario, Catastro.coord_x, Catastro.coord_y, 400 AS tension, Suministros_Nuevos.id_suministro" & _
        #                              " FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario INNER JOIN" & _
        #                              " Catastro ON LEFT(VW_CCDATOSCOMERCIALES.Nomenclatura_Catastral, LEN(Catastro.nomenclatura_catastral) + 1) = Catastro.nomenclatura_catastral + '-' INNER JOIN" & _
        #                              " Suministros_Nuevos ON Usuarios.id_suministro = Suministros_Nuevos.id_suministro INNER JOIN" & _
        #                              " Tarifas ON VW_CCDATOSCOMERCIALES.Tarifa = Tarifas.Tarifa" & _
        #                              " WHERE VW_CCDATOSCOMERCIALES.fecha_baja Is Null"
        #        Adodc2.Refresh
        #        If Adodc2.Recordset.RecordCount <> 0 Then
        #            Px = Adodc2.Recordset("coord_x")
        #            Py = Adodc2.Recordset("coord_y")
        #            frmBarra.ProgressBar1.Max = Adodc2.Recordset.RecordCount
        #            frmBarra.ProgressBar1.Value = 0
        #            Adodc2.Recordset.MoveFirst
        #            Do While Not Adodc2.Recordset.EOF
        #                frmBarra.Caption = "Insertando Suministros Nuevos"
        #                frmBarra.Visible = True
        #                frmBarra.ZOrder 0
        #                frmBarra.ProgressBar1.Value = frmBarra.ProgressBar1.Value + 1
        #                Set Pt = New MapXLib.Point
        #                Pt.Set Px, Py
        #                Nivel_Tension = Adodc2.Recordset("tension")
        #                b_existe = False
        #                'Me fijo si ya hay un punto en esa zona
        #                Set Ftrs = frmEditor.Map1(IdMapa).Layers(Curr_Arch & "_no_" & Nivel_Tension).SearchWithinDistance(Pt, 10, miUnitMeter, miSearchTypePartiallyWithin)
        #                For Each Ftr3 In Ftrs
        #                    If Not Ftr3 Is Nothing Then
        #                        Adodc3.RecordSource = "SELECT geoname FROM Nodos WHERE elmt=6 AND geoname=" & Ftr3.KeyValue
        #                        Adodc3.Refresh
        #                        If Adodc3.Recordset.RecordCount > 0 Then
        #                            b_existe = True
        #                            If AdoCon.State = 0 Then AdoCon.Open
        #                            AdoCon.BeginTrans
        #                                b_transaccion = True
        #                                frmEditor.Map1(IdMapa).CenterX = Px
        #                                frmEditor.Map1(IdMapa).CenterY = Py
        #                                frmEditor.Map1(IdMapa).Refresh
        #                                'genero el suministro
        #                                EjecutarSqlTrans ("DELETE FROM Suministros WHERE id_suministro='" & Adodc2.Recordset("id_suministro") & "'")
        #                                EjecutarSqlTrans ("INSERT INTO Suministros (id_nodo, id_suministro) VALUES (" & Adodc3.Recordset("geoname") & ",'" & Adodc2.Recordset("id_suministro") & "')")
        #                                'coloco al usuario en el suministro
        #                                EjecutarSqlTrans ("UPDATE Usuarios SET id_suministro='" & Adodc2.Recordset("id_suministro") & "' WHERE id_usuario=" & caracter_IdUsuario & Adodc2.Recordset("id_usuario") & caracter_IdUsuario)
        #                                'borro el registro original
        #                                'EjecutarSqlTrans ("DELETE FROM Suministros_Coordenadas WHERE id_usuario=" & caracter_idusuario & Adodc2.Recordset("id_usuario") & caracter_idusuario)
        #                            AdoCon.CommitTrans
        #                            b_transaccion = False
        #                            GoTo 1
        #                        End If
        #                    End If
        #                Next
        #1:
        #                If b_existe = False Then
        #                    If AdoCon.State = 0 Then AdoCon.Open
        #                    'genero el nodo
        #                    Iid = NuevoIid
        #                    AdoCon.BeginTrans
        #                        b_transaccion = True
        #                        'Insert_Point frmEditor.Map1(IdMapa).Layers(Curr_Arch & "_no_" & Nivel_Tension), px, py, frmEditor.Map1(IdMapa).DefaultStyle, Iid
        #                        Ftr1.Attach frmEditor.Map1(IdMapa)
        #                        Ftr1.Type = miFeatureTypeSymbol
        #                        Ftr1.Point.Set Px, Py
        #                        Ftr1.Style = frmEditor.Map1(IdMapa).DefaultStyle
        #                        frmEditor.Map1(IdMapa).Refresh
        #                        DoEvents
        #                        Set Ftr2 = frmEditor.Map1(IdMapa).Layers(Curr_Arch & "_no_" & Nivel_Tension).AddFeature(frmEditor.Map1(IdMapa).FeatureFactory.CreateSymbol(Ftr1.Point, Ftr1.Style))
        #                        Set Ftr1 = Nothing
        #                        Ftr2.KeyValue = Iid
        #                        Ftr2.Update
        #                        DoEvents
        #                        frmEditor.Map1(IdMapa).CenterX = Px
        #                        frmEditor.Map1(IdMapa).CenterY = Py
        #                        frmEditor.Map1(IdMapa).Refresh
        #                        '*******************************************
        #                        Set RS = CreateObject("Adodb.Recordset")
        #                        RS.Open "SELECT MAX(Aux) FROM Nodos", AdoCon, adOpenStatic, adLockReadOnly, adCmdText
        #                        n_nodos = RS(0) + 1
        #                        If RS.State = 1 Then RS.Close
        #                        '*******************************************
        #                        EjecutarSqlTrans ("INSERT INTO Nodos (Geoname, elmt, XCoord, YCoord, Tension, Estilo, Aux) VALUES (" & Iid & ",6," & str$(Px) & "," & str$(Py) & "," & Nivel_Tension & ",'35 - EnerGIS - 0 - 4227327 - 10 - 0'," & n_nodos & ")")
        #                        '*******************************************
        #                        Call Agrego_Nodo(Iid, Nivel_Tension, n_nodos)
        #                        EjecutarSqlTrans "INSERT INTO Cambios (Tipo, Geoname, Desde, Hasta, Tension, Elmt, Aux, Usuario) VALUES (1," & Iid & ",0,0," & Nivel_Tension & ",0," & n_nodos & ",'" & Codigo_Usuario & "')"
        #                        '*******************************************
        #                        'genero el suministro
        #                        EjecutarSqlTrans ("DELETE FROM Suministros WHERE id_suministro='" & Adodc2.Recordset("id_suministro") & "'")
        #                        EjecutarSqlTrans ("INSERT INTO Suministros (id_nodo, id_suministro) VALUES (" & Iid & ",'" & Adodc2.Recordset("id_suministro") & "')")
        #                        'coloco al usuario en el suministro
        #                        EjecutarSqlTrans ("UPDATE Usuarios SET id_suministro='" & Adodc2.Recordset("id_suministro") & "' WHERE id_usuario=" & caracter_IdUsuario & Adodc2.Recordset("id_usuario") & caracter_IdUsuario & " AND id_suministro<>'" & Adodc2.Recordset("id_suministro") & "'")
        #                        'borro el registro original
        #                        'EjecutarSqlTrans ("DELETE FROM Suministros_Coordenadas WHERE id_usuario=" & caracter_idusuario & Adodc2.Recordset("id_usuario") & caracter_idusuario)
        #                    AdoCon.CommitTrans
        #                    b_transaccion = False
        #                End If
        #                Adodc2.Recordset.MoveNext
        #            Loop
        #            If AdoCon.State = 1 Then AdoCon.Close
        #        End If
        #    End If
        #    frmBarra.ProgressBar1.Value = 0
        #    frmBarra.Visible = False
        #    MsgBox "Suministros agregados", vbInformation
        pass

    def actualizar(self):
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("TRUNCATE TABLE Suministros_Nuevos")
        cursor.execute("INSERT INTO Suministros_Nuevos (id_suministro) SELECT usuarios.id_suministro FROM suministros RIGHT JOIN usuarios ON suministros.id_suministro = usuarios.id_suministro WHERE usuarios.ES=1 AND suministros.id_suministro IS NULL GROUP BY usuarios.id_suministro HAVING usuarios.id_suministro IS NOT NULL")
        cursor.commit()

        self.actualizar_grilla()

    def aproximar(self):
        self.seleccion=''

        self.sql="SELECT MIN(Nodos.Geoname) AS geoname, Usuarios.calle + ' ' + Usuarios.altura AS direccion FROM Usuarios INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE Usuarios.calle LIKE '%" + self.txtCalle.toPlainText() + "%' GROUP BY Usuarios.calle, Usuarios.altura ORDER BY Usuarios.calle, Usuarios.altura"

        from .frm_elegir import frmElegir
        dialogo = frmElegir(self.conn, self.sql)
        dialogo.exec()
        if dialogo.seleccionado != '':
            self.seleccion = dialogo.seleccionado

            if self.suministro!='':
                cnn = self.conn
                cursor = cnn.cursor()
                cursor.execute("DELETE FROM Suministros WHERE id_suministro='" + self.suministro + "'")
                cursor.execute("INSERT INTO Suministros (id_nodo,id_suministro) VALUES ( " + self.seleccion + ",'" + self.suministro + "')")
                cursor.commit()
                self.actualizar()

        dialogo.close()
        pass

    def actualizar_grilla(self):
        cnn = self.conn
        cursor = cnn.cursor()
        recordset = []
        cursor.execute("SELECT Usuarios.Calle, Usuarios.Altura, Suministros_Nuevos.id_suministro FROM Suministros_Nuevos INNER JOIN Usuarios ON Suministros_Nuevos.id_suministro = Usuarios.id_suministro ORDER BY Usuarios.Calle, Usuarios.altura")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        self.tblSuministros.setRowCount(len(recordset))
        self.tblSuministros.setColumnCount(3)
        self.tblSuministros.setHorizontalHeaderLabels(["calle", "numero", "suministro"])

        self.tblSuministros.setColumnWidth(0, 120)
        self.tblSuministros.setColumnWidth(1, 60)
        self.tblSuministros.setColumnWidth(2, 60)

        for i in range (0, len(recordset)):
            self.tblSuministros.setItem(i, 0, QTableWidgetItem(recordset[i][0]))
            self.tblSuministros.setItem(i, 1, QTableWidgetItem(recordset[i][1]))
            self.tblSuministros.setItem(i, 2, QTableWidgetItem(recordset[i][2]))
        pass

    def elijo_suministro(self):
        self.suministro = self.tblSuministros.item(self.tblSuministros.currentRow(),2).text()

        cnn = self.conn
        cursor = cnn.cursor()
        recordset = []
        cursor.execute("SELECT Usuarios.id_usuario, Usuarios.nombre, Usuarios.calle, Usuarios.altura, Usuarios.altura_ex FROM Usuarios INNER JOIN Suministros_Nuevos ON Usuarios.id_suministro = Suministros_Nuevos.id_suministro WHERE Suministros_Nuevos.id_suministro ='" + self.suministro + "'")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        self.txtUsuario.setText(str(recordset[0][0]))
        self.txtNombre.setText(str(recordset[0][1]))
        self.txtCalle.setText(str(recordset[0][2]))
        self.txtNumero.setText(str(recordset[0][3]) + ' - ' + str(recordset[0][4]))

    def elijo_item(self):
        #QMessageBox.information(None, 'EnerGis 5', self.tblResultado.selectedItems()[0].text())
        #QMessageBox.information(None, 'EnerGis 5', self.tblResultado.selectedItems()[3].text())
        geom = QgsGeometry.fromWkt(self.tblResultado.selectedItems()[3].text())
        box = geom.buffer(25,1).boundingBox()
        self.mapCanvas.setExtent(box)
        self.mapCanvas.refresh()

    def salir(self):
        self.close()
        pass

