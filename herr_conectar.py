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

from qgis.core import QgsProject, QgsGeometry
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QColor
from qgis.gui import QgsMapTool
from qgis.core import QgsPoint, QgsRectangle, QgsFeatureRequest, QgsVectorLayer, QgsFeature
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

lineas_temp = QgsVectorLayer()

class herrConectar(QgsMapTool):

    def __init__(self, iface, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.iface = iface
        self.mapCanvas = mapCanvas    
        self.conn = conn

        self.geoname_primer_nodo = 0
        self.tension = 0
        self.p1 = QgsPoint()
        self.p2 = QgsPoint()

        global lineas_temp
        
        n = self.mapCanvas.layerCount()
        b_existe = False
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyrCRS = lyr.crs().authid()
            if lyr.name() == 'Lineas_Temp':
                b_existe = True
                lineas_temp = lyr

        #global snap_temp
        #snap_temp = QgsVectorLayer("Polygon?crs=" + lyrCRS, "Snap_Temp", "memory")
        
        if b_existe == False:
            lineas_temp = QgsVectorLayer("LineString?crs=" + lyrCRS, "Lineas_Temp", "memory")
            QgsProject.instance().addMapLayer(lineas_temp)
            lineas_temp.renderer().symbol().setWidth(0.4)
            lineas_temp.renderer().symbol().setColor(QColor("red"))
        pass
                   
    def canvasPressEvent(self, event):
        global lineas_temp
        #QMessageBox.information(None, 'EnerGis 5', 'srid ' + str(lyrCRS))

        x = event.pos().x()
        y = event.pos().y()
        point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        
        self.geoname_primer_nodo = 0
        self.tension = 0
        self.p1 = QgsPoint()
        self.p2 = QgsPoint()
        
        #tengo que detectar si hay nodo en el primer click -> conectar
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                width = 5 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                i = 0
                for ftr in ftrs:
                    i = i + 1
                if i > 0:
                    geom = ftr.geometry()
                    if geom.asPoint().x() > 0:
                        self.p1 = QgsPoint(geom.asPoint().x(),geom.asPoint().y())
                        self.geoname_primer_nodo = ftr.id()
                        self.tension = lyr.name() [6 - len(lyr.name()):]
                        #QMessageBox.information(None, 'Tension', str(self.tension))
                        return
         
        #sino es la herramienta de cortar línea
        self.p1 = QgsPoint(point.x(), point.y())
        pass

    def canvasMoveEvent(self, event):
        global lineas_temp

        if self.p1.x()==0:
            return

        #Get the pos
        x = event.pos().x()
        y = event.pos().y()
        point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        self.p2 = QgsPoint(point.x(), point.y())

        #borra todos los objetos de la capa
        if not lineas_temp.isEditable():
            lineas_temp.startEditing()
        listOfIds = [feat.id() for feat in lineas_temp.getFeatures()]
        lineas_temp.deleteFeatures(listOfIds)
        lineas_temp.commitChanges()
        #----------------------------------
        puntos = []
        puntos.append(self.p1)
        puntos.append(self.p2)
        #puntos.append(QgsPoint(point.x(),point.y()))
        pts = QgsGeometry.fromPolyline(puntos)
        ftrLinea = QgsFeature()
        ftrLinea.setGeometry(pts)
        lineas_temp_data = lineas_temp.dataProvider()
        lineas_temp_data.addFeatures([ftrLinea])
        lineas_temp.triggerRepaint()

        pass
        
    def canvasReleaseEvent(self, event):
        global lineas_temp
        
        x = event.pos().x()
        y = event.pos().y()
        point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        self.p2 = QgsPoint(point.x(), point.y())
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        
        puntos = []
        puntos.append(self.p1)
        puntos.append(self.p2)

        #blanqueo los puntos para que se reinicie la herramienta
        self.p1 = QgsPoint()
        self.p2 = QgsPoint()        

        pts = QgsGeometry.fromPolyline(puntos)
        ftrLinea = QgsFeature()
        ftrLinea.setGeometry(pts)
        
        QMessageBox.information(None, 'Tension', str(self.tension))
        for lyr in layers:
            if self.tension != 0:
                #creo 3 lineas
                #QMessageBox.information(None, 'Busco Cruzar con :', lyr.name() + ' - vs - Lineas ' + str(self.tension))
                if lyr.name() == 'Lineas ' + str(self.tension):
                    #QMessageBox.information(None, 'Busco Cruzar con :','Lineas ' + str(self.tension))
                    #para cada objeto de la capa (luego sera de lo que haya en el entorno de la linea que tracé)
                    for f in lyr.getFeatures():
                        #algunas veces intesecta a la linea que toca al nodo desde, entonces paso de largo las lineas donde desde o hasta = p1
                        pts = f.geometry().asPolyline()
                        b_existe = False
                        if round(pts[0][0], 1) == round(puntos[0].x(), 1) and round(pts[0][1], 1) == round(puntos[0].y(), 1):
                            b_existe = True
                        n = len(pts)
                        if round(pts[n - 1][0], 1) == round(puntos[0].x(), 1) and round(pts[n - 1][1], 1) == round(puntos[0].y(), 1):
                            b_existe = True
                        #si p1 toca a la linea en alguno de sus extremos la paso de largo !
                        if b_existe == False:
                            if ftrLinea.geometry().intersects(f.geometry()):
                                lineas_a_borrar = str(f.id())
                                #pts contiene los quiebres de la linea intersectada
                                tramo_cruce = 0
                                nuevo_nodo = QgsFeature()
                                for q in range (1, len(pts)):
                                    #QMessageBox.information(None, 'tramos', str(pts[q][0]) + ',' + str(pts[q][1]) + ' -> ' + str(pts[q - 1][0]) + ',' + str(pts[q - 1][1]))
                                    tramo = []
                                    tramo.append(QgsPoint(pts[q][0],pts[q][1]))
                                    tramo.append(QgsPoint(pts[q - 1][0],pts[q - 1][1]))
                                    pts_tramo = QgsGeometry.fromPolyline(tramo)
                                    t = QgsFeature()
                                    t.setGeometry(pts_tramo)
                                    if ftrLinea.geometry().intersects(t.geometry()):
                                        intersection = ftrLinea.geometry().intersection(t.geometry())
                                        #QMessageBox.information(None, 'Corta en Tramo ' + str(q), str(intersection))
                                        tramo_cruce = q
                                        nuevo_nodo = intersection

                                if tramo_cruce == 0:
                                    return

                                #Si hubo cruce entre tramo y linea, creo el nodo
                                cnn = self.conn
                                cursor = cnn.cursor()
                                cursor.execute("SELECT fase, elmt, desde, hasta, estilo, zona, alimentador, exp, disposicion, conservacion, modificacion, uucc FROM Lineas WHERE geoname=" + str(f.id()))
                                rows = cursor.fetchall()
                                cursor.close()
                                for row in rows:
                                    fase = str(row[0])
                                    elmt = str(row[1])
                                    geoname_desde = str(row[2])
                                    geoname_hasta = str(row[3])
                                    estilo = str(row[4])
                                    zona = str(row[5])
                                    alimentador = str(row[6])
                                    expediente = str(row[7])
                                    disposicion = str(row[8])
                                    conservacion = str(row[9])
                                    modificacion = str(row[10])
                                    uucc = str(row[11])

                                cnn = self.conn
                                cursor = cnn.cursor()
                                cursor.execute("SELECT subzona, ISNULL(localidad, 0) FROM Nodos WHERE geoname=" + geoname_desde)
                                rows = cursor.fetchall()
                                cursor.close()
                                for row in rows:
                                    subzona = str(row[0])
                                    localidad = str(row[1])

                                #-----------------------------------------------------------
                                #-----------------------------------------------------------
                                #Creacion del nuevo nodo
                                #-----------------------------------------------------------
                                #-----------------------------------------------------------
                                x_coord = nuevo_nodo.asPoint().x()
                                y_coord = nuevo_nodo.asPoint().y()

                                cnn = self.conn
                                cursor = cnn.cursor()
                                cursor.execute("SELECT TOP 1 obj.STSrid FROM nodos")
                                rows = cursor.fetchall()
                                cursor.close()
                                for row in rows:
                                    srid = str(row[0])
                                if srid == '':
                                    srid = lyr.crs().authid()
                                    srid = srid [len(srid)-5:] #5: EPSG:
                                obj = "geometry::Point(" + str(x_coord) + ',' + str(y_coord) + ',' + srid + ")"

                                cnn = self.conn
                                cnn.autocommit = False
                                cursor = cnn.cursor()
                                cursor.execute("SELECT iid FROM iid")
                                iid = tuple(cursor)
                                id = iid[0][0] + 1
                                cursor.execute("UPDATE iid SET iid =" + str(id))
                                cnn.commit()

                                geoname_nuevo_nodo = id

                                cnn = self.conn
                                cursor = cnn.cursor()
                                str_valores = str(id) + ", "
                                str_valores = str_valores + "'', '', 0, "
                                str_valores = str_valores + str(x_coord) + ", "
                                str_valores = str_valores + str(y_coord) + ", "
                                str_valores = str_valores + "'35-EnerGIS-16777215-0-2-0', "
                                str_valores = str_valores + "0, "
                                str_valores = str_valores + str(self.tension) + ", "
                                str_valores = str_valores + "'" + zona + "', "
                                str_valores = str_valores + "'" + alimentador + "', "
                                str_valores = str_valores + "0, "
                                str_valores = str_valores + "'" + modificacion + "', "
                                str_valores = str_valores + "'" + subzona + "', "
                                str_valores = str_valores + "0, "
                                str_valores = str_valores + obj + ", "
                                str_valores = str_valores + localidad
                                #QMessageBox.information(None, 'EnerGis 5', "INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, obj, Localidad) VALUES (" + str_valores + ")")
                                cursor.execute("INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, obj, Localidad) VALUES (" + str_valores + ")")
                                cnn.commit()
                                #-----------------------------------------------------------
                                #-----------------------------------------------------------

                                nueva_linea_1 = []
                                nueva_linea_2 = []
                                nueva_linea_3 = []

                                #una vez creado el nodo podemos crear las lineas
                                p = QgsPoint(pts[0].x(),pts[0].y())
                                nueva_linea_1.append(p)
                                for q in range (1, tramo_cruce):
                                    p = QgsPoint(pts[q].x(),pts[q].y())
                                    nueva_linea_1.append(p)

                                #a la primer linea le agrego el nuevo nodo
                                p = QgsPoint(nuevo_nodo.asPoint().x(), nuevo_nodo.asPoint().y())
                                nueva_linea_1.append(p)

                                #QMessageBox.information(None, 'EnerGis 5', str(nueva_linea_1))

                                #la tercer linea va del nodo inicial al nuevo nodo
                                r = QgsPoint(puntos[0].x(),puntos[0].y())
                                nueva_linea_3.append(r)
                                nueva_linea_3.append(p)

                                #QMessageBox.information(None, 'EnerGis 5', str(nueva_linea_3))

                                #arranco la segunda linea con el nuevo nodo
                                nueva_linea_2.append(p)
                                for q in range (tramo_cruce, len(pts)):
                                    p = QgsPoint(pts[q].x(),pts[q].y())
                                    nueva_linea_2.append(p)

                                #QMessageBox.information(None, 'EnerGis 5', str(nueva_linea_2))

                                #-----------------------------------------------------------
                                #-----------------------------------------------------------
                                #Creacion de la nueva linea 1
                                #-----------------------------------------------------------
                                #-----------------------------------------------------------
                                pts = QgsGeometry.fromPolyline(nueva_linea_1)
                                ftrLinea = QgsFeature()
                                ftrLinea.setGeometry(pts)
                                longitud = ftrLinea.geometry().length()

                                geom = ftrLinea.geometry()
                                obj = "geometry::STGeomFromText('" + geom.asWkt()  + "', " + srid + ")"

                                cnn = self.conn
                                cnn.autocommit = False
                                cursor = cnn.cursor()
                                cursor.execute("SELECT iid FROM iid")
                                iid = tuple(cursor)
                                id = iid[0][0] + 1
                                cursor.execute("UPDATE iid SET iid =" + str(id))
                                cnn.commit()

                                cnn = self.conn
                                cursor = cnn.cursor()
                                str_valores = str(id) + ", "
                                str_valores = str_valores + "'" + fase + "', "
                                str_valores = str_valores + elmt + ", "
                                str_valores = str_valores + str(geoname_desde) + ", "
                                str_valores = str_valores + str(geoname_nuevo_nodo) + ", "
                                str_valores = str_valores + "'" + "" + "', " #Quiebres
                                str_valores = str_valores + str(longitud) + ", "
                                str_valores = str_valores + "'" + estilo + "', "
                                str_valores = str_valores + str(self.tension) + ", "
                                str_valores = str_valores + "'" + zona + "', "
                                str_valores = str_valores + "'" + alimentador + "', "
                                str_valores = str_valores + "0, " #Aux
                                str_valores = str_valores + "'" + modificacion + "', "
                                str_valores = str_valores + "'" + expediente + "', "
                                str_valores = str_valores + "'" + disposicion + "', "
                                str_valores = str_valores + "'" + conservacion + "', "
                                str_valores = str_valores + "'" + uucc + "', "
                                str_valores = str_valores + obj
                                #QMessageBox.information(None, 'EnerGis 5', "INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, UUCC, obj) VALUES (" + str_valores + ")")
                                cursor.execute("INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, UUCC, obj) VALUES (" + str_valores + ")")
                                cnn.commit()
                                #-----------------------------------------------------------
                                #-----------------------------------------------------------

                                #-----------------------------------------------------------
                                #-----------------------------------------------------------
                                #Creacion de la nueva linea 2
                                #-----------------------------------------------------------
                                #-----------------------------------------------------------
                                pts = QgsGeometry.fromPolyline(nueva_linea_2)
                                ftrLinea = QgsFeature()
                                ftrLinea.setGeometry(pts)
                                longitud = ftrLinea.geometry().length()

                                geom = ftrLinea.geometry()
                                obj = "geometry::STGeomFromText('" + geom.asWkt()  + "', " + srid + ")"

                                cnn = self.conn
                                cnn.autocommit = False
                                cursor = cnn.cursor()
                                cursor.execute("SELECT iid FROM iid")
                                iid = tuple(cursor)
                                id = iid[0][0] + 1
                                cursor.execute("UPDATE iid SET iid =" + str(id))
                                cnn.commit()

                                cnn = self.conn
                                cursor = cnn.cursor()
                                str_valores = str(id) + ", "
                                str_valores = str_valores + "'" + fase + "', "
                                str_valores = str_valores + elmt + ", "
                                str_valores = str_valores + str(geoname_nuevo_nodo) + ", "
                                str_valores = str_valores + str(geoname_hasta) + ", "
                                str_valores = str_valores + "'" + "" + "', " #Quiebres
                                str_valores = str_valores + str(longitud) + ", "
                                str_valores = str_valores + "'" + estilo + "', "
                                str_valores = str_valores + str(self.tension) + ", "
                                str_valores = str_valores + "'" + zona + "', "
                                str_valores = str_valores + "'" + alimentador + "', "
                                str_valores = str_valores + "0, " #Aux
                                str_valores = str_valores + "'" + modificacion + "', "
                                str_valores = str_valores + "'" + expediente + "', "
                                str_valores = str_valores + "'" + disposicion + "', "
                                str_valores = str_valores + "'" + conservacion + "', "
                                str_valores = str_valores + "'" + uucc + "', "
                                str_valores = str_valores + obj
                                #QMessageBox.information(None, 'EnerGis 5', "INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, UUCC, obj) VALUES (" + str_valores + ")")
                                cursor.execute("INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, UUCC, obj) VALUES (" + str_valores + ")")
                                cnn.commit()
                                #-----------------------------------------------------------
                                #-----------------------------------------------------------

                                #-----------------------------------------------------------
                                #-----------------------------------------------------------
                                #Creacion de la nueva linea 3, la realmente nueva
                                #-----------------------------------------------------------
                                #-----------------------------------------------------------
                                pts = QgsGeometry.fromPolyline(nueva_linea_3)
                                ftrLinea = QgsFeature()
                                ftrLinea.setGeometry(pts)
                                longitud = ftrLinea.geometry().length()

                                geom = ftrLinea.geometry()
                                obj = "geometry::STGeomFromText('" + geom.asWkt()  + "', " + srid + ")"

                                cnn = self.conn
                                cnn.autocommit = False
                                cursor = cnn.cursor()
                                cursor.execute("SELECT iid FROM iid")
                                iid = tuple(cursor)
                                id = iid[0][0] + 1
                                cursor.execute("UPDATE iid SET iid =" + str(id))
                                cnn.commit()

                                cnn = self.conn
                                cursor = cnn.cursor()
                                str_valores = str(id) + ", "
                                str_valores = str_valores + "'" + fase + "', "
                                str_valores = str_valores + elmt + ", "
                                str_valores = str_valores + str(self.geoname_primer_nodo) + ", "
                                str_valores = str_valores + str(geoname_nuevo_nodo) + ", "
                                str_valores = str_valores + "'" + "" + "', " #Quiebres
                                str_valores = str_valores + str(longitud) + ", "
                                str_valores = str_valores + "'" + estilo + "', "
                                str_valores = str_valores + str(self.tension) + ", "
                                str_valores = str_valores + "'" + zona + "', "
                                str_valores = str_valores + "'" + alimentador + "', "
                                str_valores = str_valores + "0, " #Aux
                                str_valores = str_valores + "'" + modificacion + "', "
                                str_valores = str_valores + "'" + expediente + "', "
                                str_valores = str_valores + "'" + disposicion + "', "
                                str_valores = str_valores + "'" + conservacion + "', "
                                str_valores = str_valores + "'" + uucc + "', "
                                str_valores = str_valores + obj
                                #QMessageBox.information(None, 'EnerGis 5', "INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, UUCC, obj) VALUES (" + str_valores + ")")
                                cursor.execute("INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, UUCC, obj) VALUES (" + str_valores + ")")
                                cnn.commit()
                                #-----------------------------------------------------------
                                #-----------------------------------------------------------

                                cnn = self.conn
                                cnn.autocommit = False
                                cursor = cnn.cursor()
                                cursor.execute("DELETE FROM Lineas WHERE Geoname IN (" + lineas_a_borrar + ")")
                                cnn.commit()

                                #cursor.close()
                                for lyr in layers:
                                    lyr.triggerRepaint()

                                #borra todos los objetos de la capa
                                if not lineas_temp.isEditable():
                                    lineas_temp.startEditing()
                                listOfIds = [feat.id() for feat in lineas_temp.getFeatures()]
                                lineas_temp.deleteFeatures(listOfIds)
                                lineas_temp.commitChanges()
                                #----------------------------------
                                return

            else:
                #creo 2 lineas
                if lyr.name()[:7] == 'Lineas ':
                    #QMessageBox.information(None, 'Busco Cruzar con :', lyr.name())
                    for f in lyr.getFeatures():
                        #algunas veces intesecta a la linea que toca al nodo desde, entonces paso de largo las lineas donde desde o hasta = p1
                        pts = f.geometry().asPolyline()
                        if ftrLinea.geometry().intersects(f.geometry()):
                            self.tension = lyr.name() [6 - len(lyr.name()):]
                            #QMessageBox.information(None, 'Tension', str(self.tension))
                            lineas_a_borrar = str(f.id())
                            #pts contiene los quiebres de la linea intersectada
                            tramo_cruce = 0
                            nuevo_nodo = QgsFeature()
                            for q in range (1, len(pts)):
                                #QMessageBox.information(None, 'tramos', str(pts[q][0]) + ',' + str(pts[q][1]) + ' -> ' + str(pts[q - 1][0]) + ',' + str(pts[q - 1][1]))
                                tramo = []
                                tramo.append(QgsPoint(pts[q][0],pts[q][1]))
                                tramo.append(QgsPoint(pts[q - 1][0],pts[q - 1][1]))
                                pts_tramo = QgsGeometry.fromPolyline(tramo)
                                t = QgsFeature()
                                t.setGeometry(pts_tramo)
                                if ftrLinea.geometry().intersects(t.geometry()):
                                    intersection = ftrLinea.geometry().intersection(t.geometry())
                                    #QMessageBox.information(None, 'Corta en Tramo ' + str(q), str(intersection))
                                    tramo_cruce = q
                                    nuevo_nodo = intersection

                            if tramo_cruce == 0:
                                return

                            #Si hubo cruce entre tramo y linea, creo el nodo
                            cnn = self.conn
                            cursor = cnn.cursor()
                            cursor.execute("SELECT fase, elmt, desde, hasta, estilo, zona, alimentador, exp, disposicion, conservacion, modificacion, uucc FROM Lineas WHERE geoname=" + str(f.id()))
                            rows = cursor.fetchall()
                            cursor.close()
                            for row in rows:
                                fase = str(row[0])
                                elmt = str(row[1])
                                geoname_desde = str(row[2])
                                geoname_hasta = str(row[3])
                                estilo = str(row[4])
                                zona = str(row[5])
                                alimentador = str(row[6])
                                expediente = str(row[7])
                                disposicion = str(row[8])
                                conservacion = str(row[9])
                                modificacion = str(row[10])
                                uucc = str(row[11])

                            cnn = self.conn
                            cursor = cnn.cursor()
                            cursor.execute("SELECT subzona, ISNULL(localidad, 0) FROM Nodos WHERE geoname=" + geoname_desde)
                            rows = cursor.fetchall()
                            cursor.close()
                            for row in rows:
                                subzona = str(row[0])
                                localidad = str(row[1])

                            #-----------------------------------------------------------
                            #-----------------------------------------------------------
                            #Creacion del nuevo nodo
                            #-----------------------------------------------------------
                            #-----------------------------------------------------------
                            x_coord = nuevo_nodo.asPoint().x()
                            y_coord = nuevo_nodo.asPoint().y()

                            cnn = self.conn
                            cursor = cnn.cursor()
                            cursor.execute("SELECT TOP 1 obj.STSrid FROM nodos")
                            rows = cursor.fetchall()
                            cursor.close()
                            for row in rows:
                                srid = str(row[0])
                            if srid == '':
                                srid = lyr.crs().authid()
                                srid = srid [len(srid)-5:] #5: EPSG:
                            obj = "geometry::Point(" + str(x_coord) + ',' + str(y_coord) + ',' + srid + ")"

                            cnn = self.conn
                            cnn.autocommit = False
                            cursor = cnn.cursor()
                            cursor.execute("SELECT iid FROM iid")
                            iid = tuple(cursor)
                            id = iid[0][0] + 1
                            cursor.execute("UPDATE iid SET iid =" + str(id))
                            cnn.commit()

                            geoname_nuevo_nodo = id

                            cnn = self.conn
                            cursor = cnn.cursor()
                            str_valores = str(id) + ", "
                            str_valores = str_valores + "'', '', 0, "
                            str_valores = str_valores + str(x_coord) + ", "
                            str_valores = str_valores + str(y_coord) + ", "
                            str_valores = str_valores + "'35-EnerGIS-16777215-0-2-0', "
                            str_valores = str_valores + "0, "
                            str_valores = str_valores + str(self.tension) + ", "
                            str_valores = str_valores + "'" + zona + "', "
                            str_valores = str_valores + "'" + alimentador + "', "
                            str_valores = str_valores + "0, "
                            str_valores = str_valores + "'" + modificacion + "', "
                            str_valores = str_valores + "'" + subzona + "', "
                            str_valores = str_valores + "0, "
                            str_valores = str_valores + obj + ", "
                            str_valores = str_valores + localidad
                            #QMessageBox.information(None, 'EnerGis 5', "INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, obj, Localidad) VALUES (" + str_valores + ")")
                            cursor.execute("INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, obj, Localidad) VALUES (" + str_valores + ")")
                            cnn.commit()
                            #-----------------------------------------------------------
                            #-----------------------------------------------------------

                            nueva_linea_1 = []
                            nueva_linea_2 = []

                            #una vez creado el nodo podemos crear las lineas
                            p = QgsPoint(pts[0].x(),pts[0].y())
                            nueva_linea_1.append(p)
                            for q in range (1, tramo_cruce):
                                p = QgsPoint(pts[q].x(),pts[q].y())
                                nueva_linea_1.append(p)

                            #a la primer linea le agrego el nuevo nodo
                            p = QgsPoint(nuevo_nodo.asPoint().x(), nuevo_nodo.asPoint().y())
                            nueva_linea_1.append(p)

                            #QMessageBox.information(None, 'EnerGis 5', str(nueva_linea_1))

                            #arranco la segunda linea con el nuevo nodo
                            nueva_linea_2.append(p)
                            for q in range (tramo_cruce, len(pts)):
                                p = QgsPoint(pts[q].x(),pts[q].y())
                                nueva_linea_2.append(p)

                            #QMessageBox.information(None, 'EnerGis 5', str(nueva_linea_2))

                            #-----------------------------------------------------------
                            #-----------------------------------------------------------
                            #Creacion de la nueva linea 1
                            #-----------------------------------------------------------
                            #-----------------------------------------------------------
                            pts = QgsGeometry.fromPolyline(nueva_linea_1)
                            ftrLinea = QgsFeature()
                            ftrLinea.setGeometry(pts)
                            longitud = ftrLinea.geometry().length()

                            geom = ftrLinea.geometry()
                            obj = "geometry::STGeomFromText('" + geom.asWkt()  + "', " + srid + ")"

                            cnn = self.conn
                            cnn.autocommit = False
                            cursor = cnn.cursor()
                            cursor.execute("SELECT iid FROM iid")
                            iid = tuple(cursor)
                            id = iid[0][0] + 1
                            cursor.execute("UPDATE iid SET iid =" + str(id))
                            cnn.commit()

                            cnn = self.conn
                            cursor = cnn.cursor()
                            str_valores = str(id) + ", "
                            str_valores = str_valores + "'" + fase + "', "
                            str_valores = str_valores + elmt + ", "
                            str_valores = str_valores + str(geoname_desde) + ", "
                            str_valores = str_valores + str(geoname_nuevo_nodo) + ", "
                            str_valores = str_valores + "'" + "" + "', " #Quiebres
                            str_valores = str_valores + str(longitud) + ", "
                            str_valores = str_valores + "'" + estilo + "', "
                            str_valores = str_valores + str(self.tension) + ", "
                            str_valores = str_valores + "'" + zona + "', "
                            str_valores = str_valores + "'" + alimentador + "', "
                            str_valores = str_valores + "0, " #Aux
                            str_valores = str_valores + "'" + modificacion + "', "
                            str_valores = str_valores + "'" + expediente + "', "
                            str_valores = str_valores + "'" + disposicion + "', "
                            str_valores = str_valores + "'" + conservacion + "', "
                            str_valores = str_valores + "'" + uucc + "', "
                            str_valores = str_valores + obj
                            #QMessageBox.information(None, 'EnerGis 5', "INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, UUCC, obj) VALUES (" + str_valores + ")")
                            cursor.execute("INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, UUCC, obj) VALUES (" + str_valores + ")")
                            cnn.commit()
                            #-----------------------------------------------------------
                            #-----------------------------------------------------------

                            #-----------------------------------------------------------
                            #-----------------------------------------------------------
                            #Creacion de la nueva linea 2
                            #-----------------------------------------------------------
                            #-----------------------------------------------------------
                            pts = QgsGeometry.fromPolyline(nueva_linea_2)
                            ftrLinea = QgsFeature()
                            ftrLinea.setGeometry(pts)
                            longitud = ftrLinea.geometry().length()

                            geom = ftrLinea.geometry()
                            obj = "geometry::STGeomFromText('" + geom.asWkt()  + "', " + srid + ")"

                            cnn = self.conn
                            cnn.autocommit = False
                            cursor = cnn.cursor()
                            cursor.execute("SELECT iid FROM iid")
                            iid = tuple(cursor)
                            id = iid[0][0] + 1
                            cursor.execute("UPDATE iid SET iid =" + str(id))
                            cnn.commit()

                            cnn = self.conn
                            cursor = cnn.cursor()
                            str_valores = str(id) + ", "
                            str_valores = str_valores + "'" + fase + "', "
                            str_valores = str_valores + elmt + ", "
                            str_valores = str_valores + str(geoname_nuevo_nodo) + ", "
                            str_valores = str_valores + str(geoname_hasta) + ", "
                            str_valores = str_valores + "'" + "" + "', " #Quiebres
                            str_valores = str_valores + str(longitud) + ", "
                            str_valores = str_valores + "'" + estilo + "', "
                            str_valores = str_valores + str(self.tension) + ", "
                            str_valores = str_valores + "'" + zona + "', "
                            str_valores = str_valores + "'" + alimentador + "', "
                            str_valores = str_valores + "0, " #Aux
                            str_valores = str_valores + "'" + modificacion + "', "
                            str_valores = str_valores + "'" + expediente + "', "
                            str_valores = str_valores + "'" + disposicion + "', "
                            str_valores = str_valores + "'" + conservacion + "', "
                            str_valores = str_valores + "'" + uucc + "', "
                            str_valores = str_valores + obj
                            #QMessageBox.information(None, 'EnerGis 5', "INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, UUCC, obj) VALUES (" + str_valores + ")")
                            cursor.execute("INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, UUCC, obj) VALUES (" + str_valores + ")")
                            cnn.commit()
                            #-----------------------------------------------------------
                            #-----------------------------------------------------------

                            cnn = self.conn
                            cursor = cnn.cursor()
                            cursor.execute("DELETE FROM Lineas WHERE Geoname IN (" + lineas_a_borrar + ")")
                            cnn.commit()

                            for lyr in layers:
                                lyr.triggerRepaint()

                            #borra todos los objetos de la capa
                            if not lineas_temp.isEditable():
                                lineas_temp.startEditing()
                            listOfIds = [feat.id() for feat in lineas_temp.getFeatures()]
                            lineas_temp.deleteFeatures(listOfIds)
                            lineas_temp.commitChanges()
                            #----------------------------------
                            return
