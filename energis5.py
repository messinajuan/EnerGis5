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

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QComboBox, QAction
from qgis.core import QgsMapLayerType, QgsVectorFileWriter
from copy import deepcopy

from .mod_navegacion import navegar_compilar_red, buscar_loops
from .herr_seleccion import herrSeleccion
from .herr_seleccion_aleatoria import herrSeleccionAleatoria
from .herr_nodo import herrNodo
from .herr_linea import herrLinea
from .herr_agregar_vertice import herrAgregarVertice
from .herr_quitar_vertice import herrQuitarVertice
from .herr_poste import herrPoste
from .herr_area import herrArea
from .herr_parcela import herrParcela
from .herr_mover import herrMover
from .herr_rotar import herrRotar
from .herr_conectar import herrConectar
from .herr_zoom import herrZoom
from .herr_navegar_fuentes import herrNavegarFuentes
from .herr_navegar_extremos import herrNavegarExtremos
from .mod_navegacion import nodos_por_seccionador
from .mod_navegacion import nodos_por_salida

import os
import pyodbc

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class EnerGis5(object):

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.mapCanvas = iface.mapCanvas()
        self.utils = iface.mapCanvas().snappingUtils()

        # create action that will start plugin configuration
        self.energis_action = QAction(QIcon(os.path.join(basepath,"icons", 'energis.ico')), "EnerGis", self.iface.mainWindow())
        self.energis_action.setWhatsThis("")

        self.energis_action.setStatusTip("Detenido")
        self.energis_action.triggered.connect(self.run)

        # add toolbar button and menu item
        self.iface.addToolBarIcon(self.energis_action)
        self.iface.addPluginToMenu("EnerGis 5", self.energis_action)

    def initGui(self):

        pass

    def run(self):

        if self.energis_action.statusTip()=="Detenido":
            self.energis_action.setStatusTip("Iniciado")
            str_conexion = str(self.energis_action.whatsThis())
        else:
            self.energis_action.setStatusTip("Detenido")
            str_conexion = ""

        if self.energis_action.statusTip()=="Iniciado":

            try:
                self.conn = pyodbc.connect(str_conexion)
            except:
                #QMessageBox.information(None, 'EnerGis 5', 'No se pudo conectar ' + str_conexion)
                self.energis_action.setStatusTip("Detenido")
                str_conexion = ""

                #aca vamos a la ventana de configuracion
                from .frm_configuracion import frmConfiguracion
                self.dialogo = frmConfiguracion()
                self.dialogo.show()
                pass

                return

            #Creo una barra de herramientas
            self.actions = []
            self.menu = ('EnerGIS')
            self.toolbar_h = self.iface.addToolBar('EnerGISh')
            self.toolbar_v = self.iface.addToolBar('EnerGISv')
            #self.toolbar_v.area = Qt.LeftToolBarArea

            self.id_usuario_sistema = 0
            self.tipo_usuario = 4
            self.tension = 0

            self.mnodos=()
            self.mlineas=()

            self.seleccion_n = []
            self.seleccion_l = []

            #self.elijo_tension()

            #------------------------------------------
            inicio = QtWidgets.QPushButton("Inicio")
            self.toolbar_h.addWidget(inicio)
            menu = QtWidgets.QMenu()
            #------------------------------------------
            self.m_calidad = menu.addMenu('Calidad de Servicio')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Contingencias', self.iface.mainWindow())
            action.triggered.connect(self.carga_contingencias)
            self.m_calidad.addAction(action)
            #------------------------------------------
            self.m_usuarios = menu.addMenu('ABMs')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Usuarios', self.iface.mainWindow())
            action.triggered.connect(self.abm_usuarios)
            self.m_usuarios.addAction(action)
            #------------------------------------------
            self.m_listados = menu.addMenu('Listados')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Seccionadores', self.iface.mainWindow())
            action.triggered.connect(self.listado_seccionadores)
            self.m_listados.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Postes', self.iface.mainWindow())
            action.triggered.connect(self.listado_postes)
            self.m_listados.addAction(action)
            #------------------------------------------
            self.m_listado_transformadores = self.m_listados.addMenu('Transformadores')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Transformadores', self.iface.mainWindow())
            action.triggered.connect(self.listado_transformadores)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Transformadores en la Red', self.iface.mainWindow())
            action.triggered.connect(self.listado_transformadores_red)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Movimientos de Transformadores', self.iface.mainWindow())
            action.triggered.connect(self.listado_movimiento_transformadores)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Movimientos de un Transformador', self.iface.mainWindow())
            action.triggered.connect(self.listado_movimientos_trafo)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Movimientos en un CT', self.iface.mainWindow())
            action.triggered.connect(self.listado_movimientos_ct)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            self.m_listado_usuarios = self.m_listados.addMenu('Usuarios')
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Usuarios', self.iface.mainWindow())
            action.triggered.connect(self.listado_usuarios)
            self.m_listado_usuarios.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Usuarios en la Red', self.iface.mainWindow())
            action.triggered.connect(self.listado_usuarios_red)
            self.m_listado_usuarios.addAction(action)
            #------------------------------------------
            self.m_administrador = menu.addMenu('Administrador')
            self.m_modelo = self.m_administrador.addMenu('Modelo')
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_verificar.png')), 'Reiniciar Conectividad', self.iface.mainWindow())
            action.triggered.connect(self.crear_red)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_verificar.png')), 'Llevar Red al Estado Normal', self.iface.mainWindow())
            action.triggered.connect(self.red_a_estado_normal)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_verificar.png')), 'Definir Configuración Actual como Normal', self.iface.mainWindow())
            action.triggered.connect(self.establecer_estado_normal)
            self.m_modelo.addAction(action)
            #------------------------------------------
            #m_exportar = menu.addMenu('Exportar')
            #action = QAction(QIcon(os.path.join(basepath,"icons", 'img_qfield.png')), 'ESRI Shape', self.iface.mainWindow())
            #action.triggered.connect(self.exportar_shp)
            #m_exportar.addAction(action)
            #------------------------------------------
            inicio.setMenu(menu)
            #------------------------------------------
            self.toolbar_h.addSeparator()
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_verificar.png'), 'Verificar Red', self.h_verificar_red, True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_elementos_seleccionados.png'), 'Ubicar Selección', self.h_elementos_seleccionados, True, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_seleccion.png'), 'Selección', self.h_seleccion,  True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_seleccion_aleatoria.png'), 'Selección por Area', self.h_seleccion_aleatoria, True, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_nodo.png'), 'Nodo', self.h_nodo, True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_linea.png'), 'Linea', self.h_linea,  True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_agregar_vertice.png'), 'Agregar Vertice', self.h_agregar_vertice,  True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_quitar_vertice.png'), 'Borrar Vertice', self.h_quitar_vertice,  True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_poste.png'), 'Poste', self.h_poste,  True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_mover.png'), 'Mover', self.h_mover,  True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_rotar.png'), 'Rotar', self.h_rotar,  True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_conectar.png'), 'Conectar', self.h_conectar,  True, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_area.png'), 'Area', self.h_area,  True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_parcela.png'), 'Parcela', self.h_parcela,  True, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta_horizontal(os.path.join(basepath,"icons", 'img_borrar.png'), 'Borrar', self.h_borrar,  True, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            #--------------------------------------------------
            self.cmbTension = QComboBox(self.iface.mainWindow())
            #--------------------------------------------------

            cursor = self.conn.cursor()
            tensiones = []
            cursor.execute("SELECT Tension FROM Niveles_Tension WHERE Tension>=200")
            #convierto el cursor en array
            tensiones = tuple(cursor)
            cursor.close()

            self.cmbTension.clear()
            for t in range (0, len(tensiones)):
                self.cmbTension.addItem(str(tensiones[t][0]))

            #Esto puede servir para ver si están cargadas todas las capas electricas
            #n = self.mapCanvas.layerCount()
            #layers = [self.mapCanvas.layer(i) for i in range(n)]
            #for lyr in layers:
            #    if lyr.name()[:5] == 'Nodos':
            #        str_tension = lyr.name() [6 - len(lyr.name()):]
            #        for t in tensiones:
            #            if str(t[0])==str_tension:
            #                self.cmbTension.addItem(str_tension)

            #--------------------------------------------------
            self.cmbTensionAction = self.toolbar_h.addWidget(self.cmbTension)
            self.cmbTension.currentIndexChanged.connect(self.elijo_tension)
            self.cmbTension.setToolTip("Capa")
            #--------------------------------------------------
            self.agregar_herramienta_vertical(os.path.join(basepath,"icons", 'img_zoom_in.png'), 'Zoom In', self.h_zoomIn,  True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_vertical(os.path.join(basepath,"icons", 'img_zoom_out.png'), 'Zoom Out', self.h_zoomOut,  True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_vertical(os.path.join(basepath,"icons", 'img_pan.png'), 'Pan', self.h_Pan,  True, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta_vertical(os.path.join(basepath,"icons", 'img_buscar.png'), 'Buscar', self.h_buscar,  True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_vertical(os.path.join(basepath,"icons", 'img_nav_fuente.png'), 'Navegar a la Fuente', self.h_navegar_fuentes,  True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_vertical(os.path.join(basepath,"icons", 'img_nav_extremos.png'), 'Navegar a los Extremos', self.h_navegar_extremos,  True, True, True, None, None, self.iface.mainWindow())
            #self.agregar_herramienta_vertical(os.path.join(basepath,"icons", 'img_desconectados.png'), 'Desconectados', self.h_desconectados,  True, True, True, None, None, self.iface.mainWindow())
            #self.agregar_herramienta_vertical(os.path.join(basepath,"icons", 'img_aislados.png'), 'Aislados', self.h_aislados,  True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta_vertical(os.path.join(basepath,"icons", 'img_loops.png'), 'Loops', self.h_loops,  True, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta_vertical(os.path.join(basepath,"icons", 'img_usuario.png'), 'Usuarios Nuevos', self.h_usuarios_nuevos,  True, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta_vertical(os.path.join(basepath,"icons", 'img_resultado_seleccion.png'), 'Datos de la Selección', self.h_datos_seleccion,  True, True, True, None, None, self.iface.mainWindow())

            self.h_login()
        else:
            self.toolbar_h.deleteLater()
            self.toolbar_v.deleteLater()
        pass

    def agregar_herramienta_horizontal(self, icon_path, text, callback, enabled_flag, add_to_menu, add_to_toolbar, status_tip, whats_this, parent):
        try:
            icon = QIcon(icon_path)
            action = QAction(icon, text, parent)
            action.triggered.connect(callback)
            action.setEnabled(enabled_flag)
            if status_tip is not None:
                action.setStatusTip(status_tip)
            if whats_this is not None:
                action.setWhatsThis(whats_this)
            if add_to_toolbar:
                self.toolbar_h.addAction(action)
            if add_to_menu:
                #self.iface.addPluginToVectorMenu(self.menu, action)
                pass
            self.actions.append(action)
            return action
        except:
            return None

    def agregar_herramienta_vertical(self, icon_path, text, callback, enabled_flag, add_to_menu, add_to_toolbar, status_tip, whats_this, parent):
        try:
            icon = QIcon(icon_path)
            action = QAction(icon, text, parent)
            action.triggered.connect(callback)
            action.setEnabled(enabled_flag)
            if status_tip is not None:
                action.setStatusTip(status_tip)
            if whats_this is not None:
                action.setWhatsThis(whats_this)
            if add_to_toolbar:
                self.toolbar_v.addAction(action)
            if add_to_menu:
                #self.iface.addPluginToVectorMenu(self.menu, action)
                pass
            self.actions.append(action)
            return action
        except:
            return None

    def unload(self):
        self.iface.removeToolBarIcon(self.energis_action)
        try:
            del self.toolbar_h
            del self.toolbar_v
        except:
            pass

    def elijo_tension(self):
        self.tension = self.cmbTension.currentText()
        #QMessageBox.information(None, 'elijo_tension', str(self.tension))
        pass

    def abm_usuarios(self):
        from .frm_energias import frmEnergias
        self.dialogo = frmEnergias(self.conn)
        pass

    def carga_contingencias(self):
        from .frm_contingencias import frmContingencias
        self.dialogo = frmContingencias(self.conn)
        self.dialogo.show()
        pass

    def listado_seccionadores(self):
            str_sql = "SELECT Nodos.Geoname As id_nodo, Nodos.Nombre As secc, Nodos.Val1 As tipo, Nodos.Val2 As subtipo, Nodos.Val3 As fusible, Nodos.Val4 As marca, Nodos.Val5 As modelo, Nodos.Nivel As nivel, Nodos.Tension As tension, Nodos.Zona As zona, Nodos.Alimentador As alimentador, Nodos.XCoord As x, Nodos.YCoord As y FROM Nodos WHERE Nodos.Elmt = 2 Or Nodos.Elmt = 3"
            from .frm_listados import frmListados
            self.dialogo = frmListados(self.conn, str_sql)
            self.dialogo.show()
            pass

    def listado_postes(self):
            str_sql = "SELECT Postes.Geoname AS id_poste, Elementos_Postes.Descripcion AS material, Estructuras.Descripcion AS estructura, Postes.Altura, Riendas.Descripcion AS rienda, Lineas.Zona AS zona, Lineas.Alimentador AS alimentador, Lineas.Tension AS tension, Postes.XCoord AS x, Postes.YCoord AS y FROM (Lineas_Postes INNER JOIN (Riendas RIGHT JOIN ((Postes LEFT JOIN Elementos_Postes ON Postes.Elmt = Elementos_Postes.Id) LEFT JOIN Estructuras ON Postes.Estructura = Estructuras.Id) ON Riendas.Id = Postes.Rienda) ON Lineas_Postes.id_poste = Postes.Geoname) INNER JOIN Lineas ON Lineas_Postes.id_linea = Lineas.Geoname"
            from .frm_listados import frmListados
            self.dialogo = frmListados(self.conn, str_sql)
            self.dialogo.show()
            pass

    def listado_transformadores(self):
            str_sql = "SELECT Transformadores.Id_trafo AS id_trafo, Transformadores.id_ct AS id_ct, Ubicaciones.Descripcion AS [ubicado en], Ct.Ubicacion AS ubicacion, Transformadores.Potencia AS potencia, Transformadores.Tension_1 AS v1, Transformadores.Tension_2 AS v2, Tipo_Trafo.Tipo AS tipo_trafo, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_chapa AS nro_chapa, Transformadores.Anio_fabricacion AS año, Ct.Mat_plataf AS plataforma, Ct.Tipo_Ct AS tipo_ct, Transformadores.Kit AS kit, Transformadores.Cromatografia AS cromatografia, Transformadores.Anomalia AS anomalia, Transformadores.Fecha_norm AS fecha_norm, Transformadores.Obs_pcb AS observaciones_pcb FROM ((Tipo_Trafo INNER JOIN Transformadores ON Tipo_Trafo.Numero = Transformadores.Tipo) LEFT JOIN Ct ON Transformadores.id_ct = Ct.id_ct) INNER JOIN Ubicaciones ON Transformadores.Usado = Ubicaciones.Id_Ubicacion"
            from .frm_listados import frmListados
            self.dialogo = frmListados(self.conn, str_sql)
            self.dialogo.show()
            pass

    def listado_transformadores_red(self):
            str_sql = "SELECT Transformadores.Id_trafo AS id_trafo, Nodos.Geoname AS id_nodo, Nodos.Nombre AS id_ct, Ct.Ubicacion AS ubicacion, Transformadores.Potencia AS potencia, Transformadores.Tension_1 AS v1, Transformadores.Tension_2 AS v2, Tipo_Trafo.Tipo AS tipo_trafo, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_chapa AS nro_chapa, Transformadores.Obs AS Observaciones, Transformadores.Anio_fabricacion AS año, Ct.Mat_plataf AS plataforma, Ct.Tipo_ct AS tipo_ct, Nodos.Nivel AS nivel, Nodos.Tension AS tensión_nodo, Nodos.Zona AS zona, Nodos.Alimentador AS alimentador_mt, Nodos.XCoord AS x, Nodos.YCoord AS y, Transformadores.Kit AS kit, Transformadores.Cromatografia AS cromatografia, Transformadores.Anomalia AS anomalia, Transformadores.Fecha_norm AS fecha_norm, Transformadores.Obs_pcb AS observaciones_pcb, Count(Usuarios.id_usuario) AS cant_usuarios FROM ((Ct INNER JOIN ((Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN ((Nodos AS Nodos_1 LEFT JOIN Suministros_Trafos ON Nodos_1.Geoname = Suministros_Trafos.Geoname_s) INNER JOIN Nodos ON Suministros_Trafos.Geoname_t = Nodos.Geoname) ON Suministros.id_nodo = Suministros_Trafos.Geoname_s) ON Ct.Id_ct = Nodos.Nombre) INNER JOIN Transformadores ON Ct.Id_ct = Transformadores.Id_ct) INNER JOIN Tipo_Trafo ON Transformadores.Tipo = Tipo_Trafo.Numero GROUP BY Transformadores.Id_trafo, Nodos.Geoname, Nodos.Nombre, Ct.Ubicacion, Transformadores.Potencia, Transformadores.Tension_1, Transformadores.Tension_2, Tipo_Trafo.Tipo, Transformadores.Conexionado, Transformadores.Marca, Transformadores.N_chapa, Transformadores.Obs, Transformadores.Anio_fabricacion, Ct.Mat_plataf, Ct.Tipo_ct, Nodos.Nivel, Nodos.Tension, Nodos.Zona, Nodos.Alimentador, Nodos.XCoord, Nodos.YCoord, Transformadores.Kit, Transformadores.Cromatografia, Transformadores.Anomalia, Transformadores.Fecha_norm, Transformadores.Obs_pcb,Usuarios.ES"
            from .frm_listados import frmListados
            self.dialogo = frmListados(self.conn, str_sql)
            self.dialogo.show()
            pass

    def listado_movimiento_transformadores(self):
            str_sql = "SELECT Movimiento_Transformadores.id_mov AS id_movimiento, Movimiento_Transformadores.Fecha AS fecha_movimiento, Ubicaciones.Descripcion AS ubicacion_desde, Ubicaciones_1.Descripcion AS ubicacion_hasta, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo AS id_trafo, Transformadores.Potencia AS potencia, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_Chapa AS nro_chapa, Transformadores.Anio_fabricacion AS año FROM Ct, ((Movimiento_Transformadores INNER JOIN Transformadores ON Movimiento_Transformadores.id_trafo = Transformadores.Id_Trafo) INNER JOIN Ubicaciones ON Movimiento_Transformadores.mov_desde = Ubicaciones.Id_Ubicacion) INNER JOIN Ubicaciones AS Ubicaciones_1 ON Movimiento_Transformadores.mov_hasta = Ubicaciones_1.Id_Ubicacion GROUP BY Movimiento_Transformadores.id_mov, Movimiento_Transformadores.Fecha, Ubicaciones.Descripcion, Ubicaciones_1.Descripcion, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo, Transformadores.Potencia, Transformadores.Conexionado, Transformadores.Marca, Transformadores.N_Chapa, Transformadores.Anio_fabricacion ORDER BY Movimiento_Transformadctores.Fecha"
            from .frm_listados import frmListados
            self.dialogo = frmListados(self.conn, str_sql)
            self.dialogo.show()
            pass

    def listado_movimientos_trafo(self):
            id_trafo=''
            str_sql = "SELECT Movimiento_Transformadores.id_mov AS id_movimiento, Movimiento_Transformadores.Fecha AS fecha_movimiento, Ubicaciones.Descripcion AS ubicacion_desde, Ubicaciones_1.Descripcion AS ubicacion_hasta, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo AS id_trafo, Transformadores.Potencia AS potencia, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_Chapa AS nro_chapa, Transformadores.Anio_fabricacion AS año FROM Ct, ((Movimiento_Transformadores INNER JOIN Transformadores ON Movimiento_Transformadores.id_trafo = Transformadores.Id_Trafo) INNER JOIN Ubicaciones ON Movimiento_Transformadores.mov_desde = Ubicaciones.Id_Ubicacion) INNER JOIN Ubicaciones AS Ubicaciones_1 ON Movimiento_Transformadores.mov_hasta = Ubicaciones_1.Id_Ubicacion GROUP BY Movimiento_Transformadores.id_mov, Movimiento_Transformadores.Fecha, Ubicaciones.Descripcion, Ubicaciones_1.Descripcion, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo, Transformadores.Potencia, Transformadores.Conexionado, Transformadores.Marca, Transformadores.N_Chapa, Transformadores.Anio_fabricacion HAVING Transformadores.id_trafo=" + id_trafo + " ORDER BY Movimiento_Transformadores.Fecha"
            from .frm_listados import frmListados
            self.dialogo = frmListados(self.conn, str_sql)
            self.dialogo.show()
            pass

    def listado_movimientos_ct(self):
            id_ct=''
            str_sql = "SELECT Movimiento_Transformadores.id_mov AS id_movimiento, Movimiento_Transformadores.Fecha AS fecha_movimiento, Ubicaciones.Descripcion AS ubicacion_desde, Ubicaciones_1.Descripcion AS ubicacion_hasta, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo AS id_trafo, Transformadores.Potencia AS potencia, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_Chapa AS nro_chapa, Transformadores.Anio_fabricacion AS año FROM Ct, ((Movimiento_Transformadores INNER JOIN Transformadores ON Movimiento_Transformadores.id_trafo = Transformadores.Id_Trafo) INNER JOIN Ubicaciones ON Movimiento_Transformadores.mov_desde = Ubicaciones.Id_Ubicacion) INNER JOIN Ubicaciones AS Ubicaciones_1 ON Movimiento_Transformadores.mov_hasta = Ubicaciones_1.Id_Ubicacion GROUP BY Movimiento_Transformadores.id_mov, Movimiento_Transformadores.Fecha, Ubicaciones.Descripcion, Ubicaciones_1.Descripcion, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo, Transformadores.Potencia, Transformadores.Conexionado, Transformadores.Marca, Transformadores.N_Chapa, Transformadores.Anio_fabricacion HAVING Movimiento_Transformadores.observaciones LIKE '%CT " + id_ct + "%' OR Movimiento_Transformadores.observaciones LIKE '%SET " + id_ct + "%' ORDER BY Movimiento_Transformadores.Fecha"
            from .frm_listados import frmListados
            self.dialogo = frmListados(self.conn, str_sql)
            self.dialogo.show()
            pass

    def listado_usuarios(self):
            str_sql = "SELECT Usuarios.id_usuario, Medidores.nro_medidor, Usuarios.nombre, Usuarios.calle, Usuarios.altura, Usuarios.altura_ex, Usuarios.zona, Usuarios.subzona, Usuarios.id_suministro, Usuarios.tarifa, Usuarios.fase, Usuarios.ES, Usuarios.electrodependiente, Ct.Id_ct AS codigoct, Nodos_1.XCoord AS xct, Nodos_1.YCoord AS yct, Nodos_1.Nivel AS nivelct, Nodos_1.Tension AS tensionct, Nodos_1.Zona AS zonact, Nodos_1.Alimentador AS alimct, Ct.Ubicacion AS ubicct, Ct.Mat_plataf AS matct, Ct.Tipo_ct AS tipoct, Ct.Obs AS obsct FROM Medidores RIGHT OUTER JOIN Suministros LEFT OUTER JOIN Ct RIGHT OUTER JOIN Nodos AS Nodos_1 ON Ct.Id_ct = Nodos_1.Nombre RIGHT OUTER JOIN Suministros_Trafos ON Nodos_1.Geoname = Suministros_Trafos.Geoname_t ON Suministros.id_nodo = Suministros_Trafos.Geoname_s RIGHT OUTER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro ON Medidores.id_usuario = Usuarios.id_usuario"
            from .frm_listados import frmListados
            self.dialogo = frmListados(self.conn, str_sql)
            self.dialogo.show()
            pass

    def listado_usuarios_red(self):
            str_sql = "SELECT Usuarios.id_usuario, Medidores.nro_medidor, Usuarios.nombre, Usuarios.calle, Usuarios.altura, Usuarios.altura_ex, Usuarios.zona, Usuarios.Subzona, Usuarios.id_suministro, Usuarios.tarifa, Usuarios.fase, Usuarios.[ES], Usuarios.electrodependiente, Ct.Id_ct AS codigoct, Nodos_1.XCoord AS xct, Nodos_1.YCoord AS yct, Nodos_1.Nivel AS nivelct, Nodos_1.Tension AS tensionct, Nodos_1.Zona AS zonact, Nodos_1.Alimentador AS alimct, Ct.Ubicacion AS ubicct, Ct.Mat_plataf AS matct, Ct.Tipo_ct AS tipoct, Ct.Obs AS obsct FROM (Ct INNER JOIN Nodos AS Nodos_1 ON Ct.Id_ct = Nodos_1.Nombre) INNER JOIN ((Medidores RIGHT JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Medidores.id_usuario = Usuarios.id_usuario) INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s) ON Nodos_1.Geoname = Suministros_Trafos.Geoname_t"
            from .frm_listados import frmListados
            self.dialogo = frmListados(self.conn, str_sql)
            self.dialogo.show()
            pass

    def h_login(self):

        if self.id_usuario_sistema == 0:
            f = open('C:\GIS\EnerGis5\conexion.ini','r')
            ini = f.readlines()
            f.close()
            try:
                str_conexion_seguridad = ini[0].strip()
                self.nombre_usuario = ini[1].strip()
            except:
                self.nombre_usuario = ""

        from .frm_login import frmLogin
        dialogo = frmLogin(str_conexion_seguridad, self.nombre_usuario)
        dialogo.exec()
        self.id_usuario_sistema = dialogo.id_usuario_sistema
        self.tipo_usuario = dialogo.tipo_usuario
        dialogo.close()
        if str(self.tipo_usuario)=='4':
            #deshabilito los botones
            for action in self.actions:
                if str(action.text())=='Verificar Red':
                    action.setEnabled(False)
                if str(action.text())=='Nodo':
                    action.setEnabled(False)
                if str(action.text())=='Linea':
                    action.setEnabled(False)
                if str(action.text())=='Poste':
                    action.setEnabled(False)
                if str(action.text())=='Mover':
                    action.setEnabled(False)
                if str(action.text())=='Rotar':
                    action.setEnabled(False)
                if str(action.text())=='Agregar Vertice':
                    action.setEnabled(False)
                if str(action.text())=='Borrar Vertice':
                    action.setEnabled(False)
                if str(action.text())=='Conectar':
                    action.setEnabled(False)
                if str(action.text())=='Area':
                    action.setEnabled(False)
                if str(action.text())=='Parcela':
                    action.setEnabled(False)
                if str(action.text())=='Borrar':
                    action.setEnabled(False)
                if str(action.text())=='Usuarios Nuevos':
                    action.setEnabled(False)
            self.m_calidad.setEnabled(False)
            self.m_usuarios.setEnabled(False)
            self.m_administrador.setEnabled(False)
        pass

    def crear_red(self):
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("crear_red")
        cnn.commit()

    def red_a_estado_normal(self):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE nodos SET estado=elmt WHERE (elmt=2 OR elmt=3) AND estado<>elmt")
        cursor.close()
        self.crear_red
        QMessageBox.information(None, 'EnerGis 5', "Red en Estado Normal")

    def establecer_estado_normal(self):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE nodos SET elmt=estado WHERE (elmt=2 OR elmt=3) AND estado<>elmt")
        cursor.close()
        QMessageBox.information(None, 'EnerGis 5', "Se estableció la Configuración de Red como Estado Normal")

    def exportar_shp(self):
        mapCanvas = self.iface.mapCanvas()
        n = mapCanvas.layerCount()
        layers = [mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Temp':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/" + lyr.name() + ".shp", "", lyr.crs(), "ESRI Shapefile")
            if lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Temp':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/" + lyr.name() + ".shp", "", lyr.crs(), "ESRI Shapefile")
        QMessageBox.information(None, 'EnerGis 5', "Exportado")

    def h_verificar_red(self):
        #QMessageBox.information(None, 'enerGis 5', 'Inicio')
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

        self.mnodos_secc=deepcopy(self.mnodos)
        self.mnodos_sal=deepcopy(self.mnodos)

        self.mlineas_secc=deepcopy(self.mlineas)
        self.mlineas_sal=deepcopy(self.mlineas)

        cursor = self.conn.cursor()
        cursor.execute("SELECT aux, geoname FROM mNodos WHERE estado=1")
        fuentes = cursor.fetchall()
        cursor.close()
        mapCanvas = self.iface.mapCanvas()
        n = mapCanvas.layerCount()
        layers = [mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                lyr.removeSelection()
        for x in range(0, len(self.mnodos)):
            self.mnodos[x][3] = 0
            self.mnodos[x][41] = 0
            self.mnodos[x][45] = 0
        for m in range (0, len(self.mlineas)):
            self.mlineas[m][4] = 0
            self.mlineas[m][12] = 0
        self.monodos = [0] * len(self.mnodos) #valores cero de longitud igual a mnodos

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM Alimentadores WHERE Id_Alim NOT IN (SELECT Val1 FROM Nodos WHERE elmt=8)")
        cursor.execute("INSERT INTO Alimentadores (Id_Alim,Tension,Cd,SSEE) SELECT DISTINCT LEFT(Val1,15) AS Id_Alim, Tension,'0' AS Cd,'0' AS SSEE FROM Nodos WHERE elmt=8 AND LEFT(Val1,15) NOT IN (SELECT Id_Alim FROM Alimentadores)")
        cursor.execute("UPDATE Alimentadores SET ssee='0' WHERE ssee IS NULL")
        cursor.execute("UPDATE Alimentadores SET cd='0' WHERE cd IS NULL")
        cursor.commit()

        for fuente in fuentes:
            #QMessageBox.information(None, 'Navego Fuente', str(fuente[0]))
            r = navegar_compilar_red(self, self.mnodos, self.mlineas, self.monodos, fuente[0])
            if str(r) != 'Red Navegada':
                QMessageBox.information(None, 'EnerGis 5', str(r))
                return
        nodos_aislados=0
        self.seleccion_n = []
        for m in range(1, len(self.mnodos)):
            if self.mnodos[m][3] == 0 and self.mnodos[m][1]!=0:
                self.seleccion_n.append(self.mnodos[m][1])
            if self.mnodos[m][4] == 0:
                nodos_aislados=nodos_aislados+1
                #QMessageBox.information(None, 'Navego Fuente', str(self.mnodos[m][1]))
        nodos_desconectados=len(self.seleccion_n)

        self.seleccion_l = []
        for n in range (1, len(self.mlineas)):
            if self.mlineas[n][4] == 0 and self.mlineas[n][1]!=0:
                self.seleccion_l.append(self.mlineas[n][1])
        lineas_desconectadas=len(self.seleccion_l)

        nodos_por_seccionador(self, self.conn, self.mnodos_secc, self.mlineas_secc)
        nodos_por_salida(self, self.conn, self.mnodos_sal, self.mlineas_sal)

        #Verificar Red
        str_sql= "SELECT DISTINCT 'Lineas' AS Elemento,'lineas con iguales nodo desde/hasta' AS Problema,Max(A.Geoname) AS Geoname,'Linea' AS Nombre FROM (SELECT Geoname,Desde,Hasta FROM Lineas UNION SELECT Geoname,Hasta,Desde FROM Lineas) AS A GROUP BY A.Desde, A.Hasta HAVING Count(A.Geoname)>1"
        str_sql= str_sql + " UNION SELECT 'Lineas' AS Elemento,'lineas con longitud menor a cero' AS Problema,Geoname,'Linea' AS Nombre FROM Lineas WHERE Longitud<=0"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores sin nombre' AS Problema,Geoname, Nombre FROM Nodos WHERE (Elmt = 2 OR Elmt = 3) AND ((Nombre) Is null OR Nombre = '')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores con nombre repetido' AS Problema,Geoname, Nombre FROM Nodos WHERE (Elmt = 2 OR Elmt = 3) GROUP BY Geoname, Nombre HAVING Count(Nodos.Geoname)>1"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'CTs con nombre repetido' AS Problema,Geoname, Nombre FROM Nodos WHERE Elmt = 4 GROUP BY Geoname, Nombre HAVING Count(Nodos.Geoname)>1"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'salidas de alimentador sin código de alimentador' AS Problema,Geoname, Nombre FROM Nodos WHERE Elmt = 8 AND ((Val1) Is null OR Val1 = '')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'fuentes con errores de tensión' AS Problema,Geoname, Nombre FROM Nodos WHERE Elmt = 1 AND Val1 IS NULL"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'fuentes con mas de una línea' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.estado=1 AND cant_lineas>1"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores con mas de dos líneas' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE (Nodos.estado=2 OR Nodos.estado=3) AND cant_lineas>2"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'CTs con mas de dos líneas' AS Problema,Nodos.Geoname, Nodos.Nombre as Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.estado=4 AND cant_lineas>2"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'CTs con usuarios y sin máquina' AS Problema,Nodos.Geoname, Nodos.Nombre FROM (Nodos INNER JOIN ((Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s) ON Nodos.Geoname = Suministros_Trafos.Geoname_t) LEFT JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct WHERE Nodos.elmt = 4 AND Usuarios.[ES] = 1 AND Transformadores.Id_trafo Is Null GROUP BY Nodos.Geoname, Nodos.Nombre HAVING Count(Usuarios.id_usuario)>0"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'transformadores con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Transformadores INNER JOIN Nodos ON Transformadores.Id_ct = Nodos.Nombre INNER JOIN mNodos ON Nodos.Geoname = mNodos.Geoname WHERE ((mNodos.fases IN (1,2,3) AND Transformadores.Conexionado <> 'M') OR (mNodos.fases IN ('12','23','13') AND Transformadores.Conexionado NOT IN ('M','B'))) AND Nodos.Elmt=4 GROUP BY nodos.Geoname, nodos.Nombre"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'usuarios con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo  WHERE Usuarios.fase='123' GROUP BY nodos.Geoname, nodos.Nombre HAVING MIN(fase) IN ('1','2','3','12','23','13')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'nodos con inconsistencias de tarifas' AS Problema,A.Geoname, A.Nombre FROM (SELECT Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro GROUP BY Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension) AS A GROUP BY A.Geoname, A.Nombre HAVING Count(A.Nivel_Tension)>1"
        str_sql= str_sql + " UNION SELECT DISTINCT 'Nodos' AS Elemento,'nodos con inconsistencias de tarifas' AS Problema,Nodos.Geoname, Usuarios.tarifa AS Nombre FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE (((Nodos.Tension)>1000) AND ((Tarifas.Nivel_Tension)='BT')) OR (((Nodos.Tension)<1000) AND ((Tarifas.Nivel_Tension)='MT'))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'usuarios con tarifas erroneas' AS Problema,Nodos.Geoname, CAST(Usuarios.id_usuario AS varchar) + '->'+ Usuarios.Tarifa AS Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo WHERE  (((Usuarios.[ES])=1) AND ((Usuarios.tarifa) Is Null)) OR (((Usuarios.tarifa) Not In (select tarifa from tarifas)))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'alimentadores sin nombre' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos WHERE Elmt = 8 AND (Val1='' OR Val1 IS NULL)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'cambios de tension sin trafos' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta WHERE (Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Elmt=5 AND Lineas.Tension>0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'cambios de tension sin trafos' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE (Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Elmt=5 AND Lineas.Tension>0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'nodos con incosnistencia de fases' AS Problema,nodos.geoname, Nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta INNER JOIN mNodos ON Nodos.Geoname = mNodos.geoname WHERE (LEN(mNodos.fases)<>LEN(Lineas.Fase) AND mNodos.fases<>Lineas.Fase AND mNodos.fases<>123 AND Lineas.Fase<>123) AND (LEN(mNodos.fases)=2 AND CHARINDEX(Lineas.Fase, mNodos.fases, 0)=0 OR LEN(Lineas.Fase)=2 AND CHARINDEX(CONVERT(VARCHAR,mNodos.Fases), Lineas.fase, 0)=0)"

        cursor = self.conn.cursor()
        cursor.execute(str_sql)
        elementos = tuple(cursor)

        if len(elementos)!=0:
            encabezado = [column[0] for column in cursor.description]
            cursor.close()

            from .frm_lista import frmLista
            self.dialogo = frmLista(self.mapCanvas, encabezado, elementos)
            self.dialogo.setWindowTitle('Resultados Verificación')
            self.dialogo.show()

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText('Análisis de la Red')
        msg.setInformativeText('Conectividad Verificada')
        msg.setWindowTitle('EnerGis 5')
        msg.setDetailedText(str(nodos_desconectados - nodos_aislados) + ' nodos desconectados, ' + str(nodos_aislados) + ' nodos aislados, ' + str(lineas_desconectadas) + ', lineas desconectadas')
        msg.exec_()
        if nodos_desconectados==0 and lineas_desconectadas==0:
            return

        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Temp':
                lyr.select(self.seleccion_n)
            if lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Temp':
                lyr.select(self.seleccion_l)

        if len(self.seleccion_l)>0 or len(self.seleccion_n)>0:
            self.h_elementos_seleccionados()

    def h_elementos_seleccionados(self):
        from .frm_seleccion import frmSeleccion
        self.dialogo = frmSeleccion(self.mapCanvas)
        self.dialogo.show()

    def h_navegar_fuentes(self):
        ftrs = []
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                #QMessageBox.information(None, 'EnerGis 5', str(lyr.name()))
                for ftr in lyr.selectedFeatures():
                    #QMessageBox.information(None, 'EnerGis 5', str(ftr.id()))
                    ftrs.append(ftr)
        if len(ftrs) != 1:
            QMessageBox.information(None, 'EnerGis 5', 'Debe seleccionar un nodo')
            return
        id = ftrs[0].id()
        herrNavegarFuentes(self.iface, self.iface.mapCanvas(), self.conn, id)
        pass

    def h_navegar_extremos(self):
        ftrs = []
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                #QMessageBox.information(None, 'EnerGis 5', str(lyr.name()))
                for ftr in lyr.selectedFeatures():
                    #QMessageBox.information(None, 'EnerGis 5', str(ftr.id()))
                    ftrs.append(ftr)
        if len(ftrs) != 1:
            QMessageBox.information(None, 'EnerGis 5', 'Debe seleccionar un nodo')
            return
        id = ftrs[0].id()
        herrNavegarExtremos(self.iface, self.iface.mapCanvas(), self.conn, id)
        pass

    def h_loops(self):
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
        mapCanvas = self.iface.mapCanvas()
        n = mapCanvas.layerCount()
        layers = [mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                lyr.removeSelection()
        #--------------------------------------------
        buscar_loops(self, self.mnodos, self.mlineas)
        #--------------------------------------------
        self.seleccion_n = []
        for n in range(1, len(self.mnodos)):
            if self.mnodos[n][45] == 1:
                self.seleccion_n.append(self.mnodos[n][1])
        self.seleccion_l = []
        for n in range (1, len(self.mlineas)):
            if self.mlineas[n][12] == 1:
                self.seleccion_l.append(self.mlineas[n][1])
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText('Análisis de la Red')
        msg.setInformativeText('Búsqueda de Loops')
        msg.setWindowTitle('EnerGis 5')
        msg.setDetailedText(str(len(self.seleccion_l)) + ' lineas marcadas')
        msg.exec_()
        if len(self.seleccion_l)==0:
            return

        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Temp':
                lyr.select(self.seleccion_n)
            if lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Temp':
                lyr.select(self.seleccion_l)

        self.h_elementos_seleccionados()
        pass

    def h_buscar(self):
        from .frm_buscar import frmBuscar
        mapCanvas = self.iface.mapCanvas()
        self.dialogo = frmBuscar(mapCanvas, self.conn)
        self.dialogo.show()
        pass

    def h_usuarios_nuevos(self):
        from .frm_usuarios_nuevos import frmUsuariosNuevos
        mapCanvas = self.iface.mapCanvas()
        self.dialogo = frmUsuariosNuevos(mapCanvas, self.conn)
        self.dialogo.show()
        pass

    def h_datos_seleccion(self):
        from .frm_datos_seleccion import frmDatosSeleccion
        mapCanvas = self.iface.mapCanvas()
        self.dialogo = frmDatosSeleccion(mapCanvas, self.conn)
        self.dialogo.show()
        pass

    def h_seleccion(self):
        tool = herrSeleccion(self.iface.mapCanvas(), self.iface, self.conn, self.mnodos, self.mlineas, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion.png'))
        seleccion_px.setMask(seleccion_px.mask())
        seleccion_cursor = QtGui.QCursor(seleccion_px)
        self.mapCanvas.setCursor(seleccion_cursor)
        pass

    def h_seleccion_aleatoria(self):
        tool = herrSeleccionAleatoria(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion_aleatoria.png'))
        seleccion_px.setMask(seleccion_px.mask())
        seleccion_cursor = QtGui.QCursor(seleccion_px)
        self.mapCanvas.setCursor(seleccion_cursor)
        pass
        
    def h_nodo(self):
        self.tension = self.cmbTension.currentText()
        #QMessageBox.information(None, 'h_nodo', str(tension))
        tool = herrNodo(self.iface, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.mapCanvas.setCursor(curNodo)
        pass
        
    def h_linea(self):
        self.tension = self.cmbTension.currentText()
        #QMessageBox.information(None, 'h_nodo', str(tension))
        tool = herrLinea(self.iface, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.mapCanvas.setCursor(curLinea)
        pass
        
    def h_agregar_vertice(self):
        tool = herrAgregarVertice(self.iface, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.mapCanvas.setCursor(curNodo)
        pass

    def h_quitar_vertice(self):
        tool = herrQuitarVertice(self.iface, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.mapCanvas.setCursor(curNodo)
        pass

    def h_poste(self):
        self.tension = self.cmbTension.currentText()
        #QMessageBox.information(None, 'h_poste', str(tension))
        tool = herrPoste(self.iface, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punPoste = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punPoste.setMask(punPoste.mask())
        curPoste = QtGui.QCursor(punPoste)
        self.mapCanvas.setCursor(curPoste)
        pass

    def h_mover(self):
        tool = herrMover(self.iface, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punMover = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_mover.png'))
        punMover.setMask(punMover.mask())
        curMover = QtGui.QCursor(punMover)
        self.mapCanvas.setCursor(curMover)
        pass

    def h_rotar(self):
        tool = herrRotar(self.iface, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punRotar = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_rotar.png'))
        punRotar.setMask(punRotar.mask())
        curRotar = QtGui.QCursor(punRotar)
        self.mapCanvas.setCursor(curRotar)
        pass

    def h_conectar(self):
        tool = herrConectar(self.iface, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punConectar = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_conectar.png'))
        punConectar.setMask(punConectar.mask())
        curConectar = QtGui.QCursor(punConectar)
        self.mapCanvas.setCursor(curConectar)
        pass
        
    def h_area(self):
        #QMessageBox.information(None, 'h_nodo', str(tension))
        tool = herrArea(self.iface, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.mapCanvas.setCursor(curLinea)
        pass

    def h_parcela(self):
        #QMessageBox.information(None, 'h_nodo', str(tension))
        tool = herrParcela(self.iface, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.mapCanvas.setCursor(curLinea)
        pass

    def h_borrar(self):
        ftrs_nodos = []
        ftrs_lineas = []
        ftrs_postes = []
        ftrs_areas = []
        ftrs_parcelas = []
        ftrs_ejes = []
        mapCanvas = self.iface.mapCanvas()
        n = mapCanvas.layerCount()
        layers = [mapCanvas.layer(i) for i in range(n)]
        str_nodos = '0'
        str_lineas = '0'
        str_postes = '0'
        str_areas = '0'
        str_parcelas = '0'
        str_ejes = '0'
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                for ftr in lyr.selectedFeatures():
                    ftrs_nodos.append(ftr.id())
                    str_nodos = str_nodos + ',' + str(ftr.id())
                    
            if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
                for ftr in lyr.selectedFeatures():
                    ftrs_lineas.append(ftr.id())
                    str_lineas = str_lineas + ',' + str(ftr.id())

            if lyr.name()[:6] == 'Postes':
                for ftr in lyr.selectedFeatures():
                    ftrs_postes.append(ftr.id())
                    str_postes = str_postes + ',' + str(ftr.id())

            if lyr.name() == 'Areas':
                for ftr in lyr.selectedFeatures():
                    ftrs_areas.append(ftr.id())
                    str_areas = str_areas + ',' + str(ftr.id())

            if lyr.name() == 'Parcelas':
                for ftr in lyr.selectedFeatures():
                    ftrs_parcelas.append(ftr.id())
                    str_parcelas = str_parcelas + ',' + str(ftr.id())

            if lyr.name() == 'Ejes':
                for ftr in lyr.selectedFeatures():
                    ftrs_ejes.append(ftr.id())
                    str_ejes = str_ejes + ',' + str(ftr.id())

        if len(ftrs_nodos) + len(ftrs_lineas) + len(ftrs_postes) + len(ftrs_areas) + len(ftrs_parcelas) + len(ftrs_ejes) > 0:
            reply = QMessageBox.question(None, 'EnerGis 5', 'Desea borrar los elementos seleccionados ?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                layers = [self.mapCanvas.layer(i) for i in range(n)]
                for lyr in layers:

                    if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
                        #if not lyr.isEditable():
                        #    lyr.startEditing()
                        #lyr.deleteFeatures(ftrs_lineas)
                        #lyr.commitChanges()
                        cursor = self.conn.cursor()
                        cursor.execute("DELETE FROM Lineas WHERE Geoname IN (" + str_lineas + ")")
                        self.conn.commit()
                        lyr.triggerRepaint()

                    elif lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                        #if not lyr.isEditable():
                        #    lyr.startEditing()
                        #lyr.deleteFeatures(ftrs_nodos)
                        #lyr.commitChanges()
                        cursor = self.conn.cursor()
                        cursor.execute("DELETE FROM Nodos WHERE Geoname IN (" + str_nodos + ")")
                        self.conn.commit()
                        lyr.triggerRepaint()

                    elif lyr.name()[:6] == 'Postes':
                        #if not lyr.isEditable():
                        #    lyr.startEditing()
                        #lyr.deleteFeatures(ftrs_postes)
                        #lyr.commitChanges()
                        cursor = self.conn.cursor()
                        cursor.execute("DELETE FROM Postes WHERE Geoname IN (" + str_postes + ")")
                        self.conn.commit()
                        lyr.triggerRepaint()

                    elif lyr.name() == 'Areas':
                        #if not lyr.isEditable():
                        #    lyr.startEditing()
                        #lyr.deleteFeatures(ftrs_areas)
                        #lyr.commitChanges()
                        cursor = self.conn.cursor()
                        cursor.execute("DELETE FROM Areas WHERE Geoname IN (" + str_areas + ")")
                        self.conn.commit()
                        lyr.triggerRepaint()

                    elif lyr.name() == 'Parcelas':
                        #if not lyr.isEditable():
                        #    lyr.startEditing()
                        #lyr.deleteFeatures(ftrs_parcelas)
                        #lyr.commitChanges()
                        cursor = self.conn.cursor()
                        cursor.execute("DELETE FROM Parcelas WHERE Geoname IN (" + str_parcelas + ")")
                        self.conn.commit()
                        lyr.triggerRepaint()

                    elif lyr.name() == 'Ejes':
                        #if not lyr.isEditable():
                        #    lyr.startEditing()
                        #lyr.deleteFeatures(ftrs_ejes)
                        #lyr.commitChanges()
                        cursor = self.conn.cursor()
                        cursor.execute("DELETE FROM Ejes WHERE Geoname IN (" + str_ejes + ")")
                        self.conn.commit()
                        lyr.triggerRepaint()
                    else:
                        #lyr.triggerRepaint()
                        pass
        pass
        
    def h_zoomIn(self):
        tool = herrZoom(self.iface, self.iface.mapCanvas(), 'ZoomIn')
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punZoom = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_zoom_in.png'))
        punZoom.setMask(punZoom.mask())
        curZoom = QtGui.QCursor(punZoom)
        self.mapCanvas.setCursor(curZoom)
        pass

    def h_zoomOut(self):
        tool = herrZoom(self.iface, self.iface.mapCanvas(), 'ZoomOut')
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punZoom = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_zoom_out.png'))
        punZoom.setMask(punZoom.mask())
        curZoom = QtGui.QCursor(punZoom)
        self.mapCanvas.setCursor(curZoom)
        pass
        
    def h_Pan(self):
        tool = herrZoom(self.iface, self.iface.mapCanvas(), 'Pan')
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punZoom = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_pan.png'))
        punZoom.setMask(punZoom.mask())
        curZoom = QtGui.QCursor(punZoom)
        self.mapCanvas.setCursor(curZoom)
        pass
