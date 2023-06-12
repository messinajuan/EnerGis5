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
from PyQt5.QtWidgets import QMessageBox, QComboBox, QAction, QInputDialog
from qgis.core import QgsMapLayerType, QgsVectorFileWriter
from qgis.core import QgsProject, QgsSimpleMarkerSymbolLayerBase

from .mod_navegacion import navegar_compilar_red, buscar_loops
from .herr_seleccion import herrSeleccion
from .herr_seleccion_aleatoria import herrSeleccionAleatoria
from .herr_seleccion_ejes import herrSeleccionEjes
from .herr_nodo import herrNodo
from .herr_linea import herrLinea
from .herr_agregar_vertice import herrAgregarVertice
from .herr_quitar_vertice import herrQuitarVertice
from .herr_poste import herrPoste
from .herr_area import herrArea
from .herr_parcela import herrParcela
from .herr_eje import herrEje
from .herr_mover import herrMover
from .herr_rotar import herrRotar
from .herr_mover_ejes import herrMoverEjes
from .herr_rotar_ejes import herrRotarEjes
from .herr_conectar import herrConectar
from .herr_zoom import herrZoom
from .herr_navegar_fuentes import herrNavegarFuentes
from .herr_navegar_extremos import herrNavegarExtremos
#from .mod_navegacion import nodos_por_seccionador
from .mod_navegacion import nodos_por_salida
from copy import deepcopy

import os
import pyodbc

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class EnerGis5(object):

    def __init__(self, iface):
        #da acceso a la interfaz QGIS
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

        self.tensiones=[]
        self.proyecto = ''

    def initGui(self):
        #llamado cuando se carga el complemento
        #La versión cambiará cuando cambie la db
        self.version = '5.0.12'
        pass

    def run(self):
        if self.energis_action.statusTip()=="Detenido":
            self.energis_action.setStatusTip("Iniciado")

            wt = str(self.energis_action.whatsThis())
            conexiones = wt.split('|')
            str_conexion = conexiones[0]
            str_conexion_seguridad = conexiones[1]

            self.nombre_modelo = QgsProject.instance().title()
            #QMessageBox.information(None, 'EnerGis 5', self.nombre_modelo)
        else:
            self.energis_action.setStatusTip("Detenido")
            str_conexion = ""

        if self.energis_action.statusTip()=="Iniciado":
            try:
                if str_conexion!="":
                    self.conn = pyodbc.connect(str_conexion)
                    self.actualizar_base_datos()
                else:
                    return
            except:
                QMessageBox.information(None, 'EnerGis 5', 'No se pudo conectar al modelo ' + str_conexion)
                self.energis_action.setStatusTip("Detenido")
                str_conexion = ""
                return

            #Creo barras de herramientas
            self.actions = []
            self.menu = ('EnerGIS')
            self.toolbar_h = self.iface.addToolBar('EnerGis Dibujo')
            self.toolbar_v = self.iface.addToolBar('EnerGis Busqueda')
            self.toolbar_p = self.iface.addToolBar('EnerGis Proyectos')
            self.toolbar_e = self.iface.addToolBar('EnerGis Ejes')
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
            inicio = QtWidgets.QPushButton("Menú")
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
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Centros de Transformación', self.iface.mainWindow())
            action.triggered.connect(self.listado_cts)
            self.m_listado_transformadores.addAction(action)
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
            m_exportar = menu.addMenu('Exportar')
            action = QAction(QIcon(os.path.join(basepath,"icons", 'img_qfield.png')), 'QField', self.iface.mainWindow())
            action.triggered.connect(self.exportar_shp)
            m_exportar.addAction(action)
            #------------------------------------------
            #action = QAction(QIcon(os.path.join(basepath,"icons", 'img_qfield.png')), 'Mapinfo TAB', self.iface.mainWindow())
            #action.triggered.connect(self.exportar_tab)
            #m_exportar.addAction(action)
            #------------------------------------------
            inicio.setMenu(menu)
            #------------------------------------------
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_verificar.png'), 'Verificar Red', self.h_verificar_red, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_elementos_seleccionados.png'), 'Ubicar Selección', self.h_elementos_seleccionados, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_seleccion.png'), 'Selección', self.h_seleccion, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_seleccion_aleatoria.png'), 'Selección por Area', self.h_seleccion_aleatoria, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_nodo.png'), 'Nodo', self.h_nodo, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_linea.png'), 'Linea', self.h_linea, True, False, True, True, None, None, self.iface.mainWindow())

            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_agregar_vertice.png'), 'Agregar Vertice', self.h_agregar_vertice, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_quitar_vertice.png'), 'Borrar Vertice', self.h_quitar_vertice, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_poste.png'), 'Poste', self.h_poste, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_mover.png'), 'Mover', self.h_mover, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_rotar.png'), 'Rotar', self.h_rotar, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_conectar.png'), 'Conectar', self.h_conectar, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_area.png'), 'Area', self.h_area, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_parcela.png'), 'Parcela', self.h_parcela, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_borrar.png'), 'Borrar', self.h_borrar, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            #--------------------------------------------------
            self.cmbTension  = QComboBox(self.iface.mainWindow())
            #--------------------------------------------------

            cursor = self.conn.cursor()
            cursor.execute("SELECT Tension FROM Niveles_Tension WHERE Tension>=50")
            #convierto el cursor en array
            self.tensiones = tuple(cursor)
            cursor.close()

            self.cmbTension.clear()
            for t in range (0, len(self.tensiones)):
                self.cmbTension.addItem(str(self.tensiones[t][0]))

            #Esto puede servir para ver si están cargadas todas las capas electricas
            #n = self.mapCanvas.layerCount()
            #layers = [self.mapCanvas.layer(i) for i in range(n)]
            #for lyr in layers:
            #    if lyr.name()[:5] == 'Nodos':
            #        str_tension = lyr.name() [6 - len(lyr.name()):]
            #        for t in tensiones:
            #            if str(t[0])==str_tension:
            #                self.cmbTension.addItem(str_tension)

            n = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Nodos Proyectos' or lyr.name() == 'Lineas Proyectos' or lyr.name() == 'Postes Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'@@'")

            #--------------------------------------------------
            self.cmbTensionAction = self.toolbar_h.addWidget(self.cmbTension)
            self.cmbTension.currentIndexChanged.connect(self.elijo_tension)
            self.cmbTension.setToolTip("Capa")
            #--------------------------------------------------
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_zoom_in.png'), 'Zoom In', self.h_zoomIn, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_zoom_out.png'), 'Zoom Out', self.h_zoomOut, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_pan.png'), 'Pan', self.h_Pan, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_buscar.png'), 'Buscar', self.h_buscar, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_buscar_direccion.png'), 'Buscar Direccion', self.h_buscar_direccion, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_nav_fuente.png'), 'Navegar a la Fuente', self.h_navegar_fuentes, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_nav_extremos.png'), 'Navegar a los Extremos', self.h_navegar_extremos, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_desconectados.png'), 'Desconectados', self.h_desconectados, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_aislados.png'), 'Aislados', self.h_aislados, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_loops.png'), 'Loops', self.h_loops, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_usuario.png'), 'Usuarios Nuevos', self.h_usuarios_nuevos, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_electrodependientes.png'), 'Usuarios Electrodependientes', self.h_electrodependientes, True, True, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_resultado_seleccion.png'), 'Datos de la Selección', self.h_datos_seleccion, True, False, True, True, None, None, self.iface.mainWindow())

            #--------------------------------------------------
            self.cmbProyecto = QComboBox(self.iface.mainWindow())
            #--------------------------------------------------

            cursor = self.conn.cursor()
            cursor.execute("SELECT Nombre FROM Proyectos")
            #convierto el cursor en array
            proyectos = tuple(cursor)
            cursor.close()

            self.cmbProyecto.clear()
            self.cmbProyecto.addItem("<Proyecto>")
            for p in range (0, len(proyectos)):
                self.cmbProyecto.addItem(str(proyectos[p][0]))

            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_nuevo.png'), 'Nuevo Proyecto', self.h_crear_proyecto, True, False, True, True, None, None, self.iface.mainWindow())
            #--------------------------------------------------

            self.cmbProyectoAction = self.toolbar_p.addWidget(self.cmbProyecto)
            self.cmbProyecto.currentIndexChanged.connect(self.elijo_proyecto)
            self.cmbProyecto.setToolTip("Proyecto")
            self.cmbProyecto.setFixedWidth(200)
            #--------------------------------------------------
            self.toolbar_p.addSeparator()
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_editar.png'), 'Modificar Proyecto', self.h_editar_proyecto, True, True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_incorporar.png'), 'Incorporar Proyecto', self.h_incorporar_proyecto, False, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_quitar.png'), 'Borrar Proyecto', self.h_borrar_proyecto, False, False, True, True, None, None, self.iface.mainWindow())

            for action in self.actions:
                if str(action.text())=='Modificar Proyecto':
                    action.setEnabled(False)

            #Esta etiqueta va ultima
            #--------------------------------------------------
            #self.lblTension = QLabel(self.iface.mainWindow())
            #--------------------------------------------------
            #self.lblTension.setText('0')
            #self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_nuevo.png'), 'Tension', self.h_crear_proyecto, True, False, True, True, None, None, self.iface.mainWindow())
            #--------------------------------------------------
            #self.lblTensionAction = self.toolbar_p.addWidget(self.lblTension)
            #self.lblTension.setToolTip("Proyecto")

            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_seleccion_ejes.png'), 'Seleccionar Eje', self.h_seleccionar_ejes, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_eje.png'), 'Eje de Calle', self.h_eje, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_editar_ejes.png'), 'Cargar Datos', self.h_datos_eje, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_mover.png'), 'Mover Ejes', self.h_mover_ejes, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_rotar.png'), 'Rotar Ejes', self.h_rotar_ejes, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_borrar.png'), 'Borrar Eje de Calle', self.h_borrar_ejes, True, False, True, True, None, None, self.iface.mainWindow())

            self.actualizar_db()

            self.h_login(str_conexion_seguridad)
            self.iface.mapCanvas().setMapTool(None)
        else:
            try:
                self.toolbar_h.deleteLater()
                self.toolbar_v.deleteLater()
                self.toolbar_p.deleteLater()
                self.toolbar_e.deleteLater()
            except:
                pass
        self.h_seleccion()
        pass

    def actualizar_base_datos(self):
        cnn = self.conn
        cursor = cnn.cursor()
        try:
            cursor.execute("delete from lineas where desde=0 or hasta=0 or desde=hasta")
            cnn.commit()
        except:
            cnn.rollback()

    def agregar_herramienta(self, toolbar, icon_path, text, callback, enabled_flag, checkable_flag, add_to_menu, add_to_toolbar, status_tip, whats_this, parent):
        try:
            icon = QIcon(icon_path)
            action = QAction(icon, text, parent)
            action.triggered.connect(callback)
            action.setEnabled(enabled_flag)
            action.setCheckable(checkable_flag)
            if status_tip is not None:
                action.setStatusTip(status_tip)
            if whats_this is not None:
                action.setWhatsThis(whats_this)
            if add_to_toolbar:
                toolbar.addAction(action)
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
            del self.toolbar_p
            del self.toolbar_e
            self.iface.mapCanvas().setMapTool(None)
        except:
            pass

    def elijo_tension(self):
        self.tension = int(self.cmbTension.currentText())
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
        str_sql = "SELECT Nodos.Geoname As id_nodo, Nodos.Nombre As secc, Nodos.Val1 As tipo, Nodos.Val2 As subtipo, Nodos.Val3 As fusible, Nodos.Val4 As marca, Nodos.Val5 As modelo, Nodos.Nivel As nivel, Nodos.Tension As tension, Nodos.Zona As zona, Nodos.Alimentador As alimentador, Nodos.XCoord As x, Nodos.YCoord As y FROM Nodos WHERE Nodos.Tension>0 AND Nodos.Elmt = 2 Or Nodos.Elmt = 3"
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

    def listado_cts(self):
        str_sql = "SELECT Transformadores.Id_trafo AS id_trafo, Nodos.Geoname AS id_nodo, Ct.id_ct, Ct.Ubicacion AS ubicacion, Transformadores.Potencia AS potencia, Transformadores.Tension_1 AS v1, Transformadores.Tension_2 AS v2, Tipo_Trafo.Tipo AS tipo_trafo, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_chapa AS nro_chapa, Transformadores.Obs AS Observaciones, Transformadores.Anio_fabricacion AS año, Ct.Mat_plataf AS plataforma, Ct.Tipo_ct AS tipo_ct, Nodos.Nivel AS nivel, Nodos.Tension AS tension_nodo, Nodos.Zona AS zona, Nodos.Alimentador AS alimentador_mt, Nodos.XCoord AS x, Nodos.YCoord AS y, Transformadores.Kit AS kit, Transformadores.Cromatografia AS cromatografia, Transformadores.Anomalia AS anomalia, Transformadores.Fecha_norm AS fecha_norm, Transformadores.Obs_pcb AS observaciones_pcb FROM Tipo_Trafo INNER JOIN Transformadores ON Tipo_Trafo.Numero = Transformadores.Tipo RIGHT OUTER JOIN Nodos RIGHT OUTER JOIN Ct ON Nodos.Nombre = Ct.Id_ct ON Transformadores.Id_ct = Ct.Id_ct WHERE Nodos.Elmt = 4 ORDER BY Ct.Id_ct"
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

    def h_login(self, str_conexion_seguridad):
        import os
        if os.path.isdir('c:/gis/')==False:
            os.mkdir('c:/gis/')

        if os.path.isdir('c:/gis/energis5/')==False:
            os.mkdir('c:/gis/energis5/')

        if self.id_usuario_sistema == 0:
            if os.path.isfile('c:/gis/energis5/user.ini')==True:
                f = open('c:/gis/energis5/user.ini','r')
                ini = f.readlines()
                f.close()
                try:
                    self.nombre_usuario = ini[0].strip()
                except:
                    self.nombre_usuario = ""

        from .frm_login import frmLogin
        dialogo = frmLogin(str_conexion_seguridad, self.nombre_usuario)
        dialogo.exec()
        self.id_usuario_sistema = dialogo.id_usuario_sistema
        self.tipo_usuario = dialogo.tipo_usuario

        #guardo el usuario
        f = open('c:/gis/energis5/user.ini','w')
        f.writelines(self.nombre_usuario)
        f.close()

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

    def actualizar_db(self):

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Configuracion")
        #convierto el cursor en array
        configuracion = tuple(cursor)
        cursor.close()

        for c in configuracion:
            if c[0]=='Version':
                v=c[1]

        if v==self.version: #deberia comparar el 5, el 0 y el 11 del 5.0.11 y hacer cambios direfenciales.
                            #cada uno de estos ifs debería ejecutarse en estos casos, o sea podrian ejecutarse mas de uno
            return

        cnn = self.conn
        cursor = cnn.cursor()

        try:
            cursor.execute("CREATE TABLE [Fotos]([Id] [int] IDENTITY(1,1) NOT NULL,[Geoname] [int] NULL,[Nombre] [varchar](50) NULL,[Imagen] [image] NULL,CONSTRAINT [PK_Fotos] PRIMARY KEY CLUSTERED ([Id] ASC) ON [PRIMARY]) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]")
            cnn.commit()
        except:
            cnn.rollback()
        try:
            cursor.execute("CREATE TABLE [Almacenes]([id_almacen] [smallint] NULL,[Nombre] [varchar](50) NULL,[Direccion] [varchar](100) NULL) ON [PRIMARY]")
            cnn.commit()
        except:
            cnn.rollback()
        try:
            cursor.execute("CREATE TABLE [Proyectos]([id] [int] IDENTITY(1,1) NOT NULL,[nombre] [varchar](15) NULL,[descripcion] [varchar](100) NULL,[fecha] [date] NULL) ON [PRIMARY]")
            cnn.commit()
        except:
            cnn.rollback()
        try:
            cursor.execute("CREATE FUNCTION Split (@cadena VARCHAR(255), @separador VARCHAR(1)) RETURNS @returnList TABLE (Name nvarchar (500)) AS BEGIN DECLARE @name NVARCHAR(255) DECLARE @pos INT WHILE CHARINDEX(@separador, @cadena) > 0 BEGIN SELECT @pos  = CHARINDEX(@separador, @cadena) SELECT @name = SUBSTRING(@cadena, 1, @pos-1) INSERT INTO @returnList SELECT @name SELECT @cadena = SUBSTRING(@cadena, @pos+1, LEN(@cadena)-@pos) END INSERT INTO @returnList SELECT @cadena RETURN END")
            cnn.commit()
        except:
            cnn.rollback()
        try:
            cursor.execute("CREATE FUNCTION Split (@cadena VARCHAR(255), @separador VARCHAR(1)) RETURNS @returnList TABLE (Name nvarchar (500)) AS BEGIN DECLARE @name NVARCHAR(255) DECLARE @pos INT WHILE CHARINDEX(@separador, @cadena) > 0 BEGIN SELECT @pos  = CHARINDEX(@separador, @cadena) SELECT @name = SUBSTRING(@cadena, 1, @pos-1) INSERT INTO @returnList SELECT @name SELECT @cadena = SUBSTRING(@cadena, @pos+1, LEN(@cadena)-@pos) END INSERT INTO @returnList SELECT @cadena RETURN END")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER FUNCTION Split (@cadena VARCHAR(255), @separador VARCHAR(1)) RETURNS @returnList TABLE (Name nvarchar (500)) AS BEGIN DECLARE @name NVARCHAR(255) DECLARE @pos INT WHILE CHARINDEX(@separador, @cadena) > 0 BEGIN SELECT @pos  = CHARINDEX(@separador, @cadena) SELECT @name = SUBSTRING(@cadena, 1, @pos-1) INSERT INTO @returnList SELECT @name SELECT @cadena = SUBSTRING(@cadena, @pos+1, LEN(@cadena)-@pos) END INSERT INTO @returnList SELECT @cadena RETURN END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE FUNCTION MAXIMO(@valor1 INT, @valor2 INT) RETURNS INT AS BEGIN DECLARE @resultado INT SET @resultado = @valor1 IF @valor2 > @resultado BEGIN SET @resultado = @valor2 END RETURN @resultado END")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER FUNCTION MAXIMO(@valor1 INT, @valor2 INT) RETURNS INT AS BEGIN DECLARE @resultado INT SET @resultado = @valor1 IF @valor2 > @resultado BEGIN SET @resultado = @valor2 END RETURN @resultado END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE PROCEDURE Compilar_Red AS BEGIN SET NOCOUNT ON DECLARE @t TABLE(Elemento VARCHAR(10), Problema VARCHAR(100), Geoname INT, Nombre VARCHAR(50)) INSERT INTO @t SELECT DISTINCT 'Lineas' AS Elemento, 'lineas con iguales nodo desde/hasta' AS Problema,Max(A.Geoname) AS Geoname,'Linea' AS Nombre FROM (SELECT Geoname,Desde,Hasta FROM Lineas WHERE Tension>0 UNION SELECT Geoname,Hasta,Desde FROM Lineas WHERE Tension>0) AS A GROUP BY A.Desde, A.Hasta HAVING Count(A.Geoname)>1 INSERT INTO @t SELECT 'Lineas' AS Elemento, 'lineas con longitud menor a cero' AS Problema,Geoname,'Linea' AS Nombre FROM Lineas WHERE Longitud<=0 AND Tension>0 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'seccionadores sin nombre' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND (Elmt = 2 OR Elmt = 3) AND ((Nombre) Is null OR Nombre = '') INSERT INTO @t SELECT 'Nodos' AS Elemento, 'seccionadores con nombre repetido' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND (Elmt = 2 OR Elmt = 3) GROUP BY Geoname, Nombre HAVING Count(Nodos.Geoname)>1 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'CTs con nombre repetido' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND Elmt = 4 GROUP BY Geoname, Nombre HAVING Count(Nodos.Geoname)>1 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'salidas de alimentador sin códi de alimentador' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND Elmt = 8 AND ((Val1) Is null OR Val1 = '') INSERT INTO @t SELECT 'Nodos' AS Elemento, 'fuentes con errores de tensión' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND Elmt = 1 AND Val1 IS NULL INSERT INTO @t SELECT 'Nodos' AS Elemento, 'fuentes con mas de una línea' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND Nodos.estado=1 AND cant_lineas>1 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'seccionadores con mas de dos líneas' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND (Nodos.estado=2 OR Nodos.estado=3) AND cant_lineas>2 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'CTs con mas de dos líneas' AS Problema, Nodos.Geoname, Nodos.Nombre as Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND Nodos.estado=4 AND cant_lineas>2 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'CTs con usuarios y sin máquina' AS Problema, Nodos.Geoname, Nodos.Nombre FROM (Nodos INNER JOIN ((Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s) ON Nodos.Geoname = Suministros_Trafos.Geoname_t) LEFT JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct WHERE Tension>0 AND Nodos.elmt = 4 AND Usuarios.ES = 1 AND Transformadores.Id_trafo Is Null GROUP BY Nodos.Geoname, Nodos.Nombre HAVING Count(Usuarios.id_usuario)>0 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'transformadores con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Transformadores INNER JOIN Nodos ON Transformadores.Id_ct = Nodos.Nombre INNER JOIN mNodos ON Nodos.Geoname = mNodos.Geoname WHERE Nodos.Tension>0 AND ((mNodos.fases IN (1,2,3) AND Transformadores.Conexionado <> 'M') OR (mNodos.fases IN ('12','23','13') AND Transformadores.Conexionado NOT IN ('M','B'))) AND Nodos.Elmt=4 GROUP BY nodos.Geoname, nodos.Nombre INSERT INTO @t SELECT 'Nodos' AS Elemento, 'usuarios con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo  WHERE Tension>0 AND Usuarios.fase='123' GROUP BY nodos.Geoname, nodos.Nombre HAVING MIN(fase) IN ('1','2','3','12','23','13') INSERT INTO @t SELECT 'Nodos' AS Elemento, 'nodos con inconsistencias de tarifas' AS Problema,A.Geoname, A.Nombre FROM (SELECT Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE Tension>0 GROUP BY Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension) AS A GROUP BY A.Geoname, A.Nombre HAVING Count(A.Nivel_Tension)>1 INSERT INTO @t SELECT DISTINCT 'Nodos' AS Elemento, 'nodos con inconsistencias de tarifas' AS Problema,Nodos.Geoname, Usuarios.tarifa AS Nombre FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE (Tension>0 AND ((Nodos.Tension)>1000) AND ((Tarifas.Nivel_Tension)='BT')) OR (Tension>0 AND ((Nodos.Tension)<1000) AND ((Tarifas.Nivel_Tension)='MT')) INSERT INTO @t SELECT 'Nodos' AS Elemento, 'usuarios con tarifas erroneas' AS Problema, Nodos.Geoname, CAST(Usuarios.id_usuario AS varchar) + '->'+ Usuarios.Tarifa AS Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo WHERE (Tension>0 AND ((Usuarios.ES)=1) AND ((Usuarios.tarifa) Is Null)) OR (Tension>0 AND ((Usuarios.tarifa) Not In (select tarifa from tarifas))) INSERT INTO @t SELECT 'Nodos' AS Elemento, 'alimentadores sin Nombre' AS Problema, nodos.Geoname, nodos.Nombre FROM Nodos WHERE Tension>0 AND Elmt = 8 AND (Val1='' OR Val1 IS NULL) INSERT INTO @t SELECT 'Nodos' AS Elemento, 'cambios de tension sin trafos' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta WHERE (Nodos.Tension>0 AND Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Tension>0 AND Nodos.Elmt=5 AND Lineas.Tension>0) INSERT INTO @t SELECT 'Nodos' AS Elemento, 'nodos con inconsistenacias de tensión' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE Nodos.Tension>0 AND Nodos.Geoname<>0 AND ((Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Elmt=5 AND Lineas.Tension>0)) select * from @t END")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER PROCEDURE Compilar_Red AS BEGIN SET NOCOUNT ON DECLARE @t TABLE(Elemento VARCHAR(10), Problema VARCHAR(100), Geoname INT, Nombre VARCHAR(50)) INSERT INTO @t SELECT DISTINCT 'Lineas' AS Elemento, 'lineas con iguales nodo desde/hasta' AS Problema,Max(A.Geoname) AS Geoname,'Linea' AS Nombre FROM (SELECT Geoname,Desde,Hasta FROM Lineas WHERE Tension>0 UNION SELECT Geoname,Hasta,Desde FROM Lineas WHERE Tension>0) AS A GROUP BY A.Desde, A.Hasta HAVING Count(A.Geoname)>1 INSERT INTO @t SELECT 'Lineas' AS Elemento, 'lineas con longitud menor a cero' AS Problema,Geoname,'Linea' AS Nombre FROM Lineas WHERE Longitud<=0 AND Tension>0 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'seccionadores sin nombre' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND (Elmt = 2 OR Elmt = 3) AND ((Nombre) Is null OR Nombre = '') INSERT INTO @t SELECT 'Nodos' AS Elemento, 'seccionadores con nombre repetido' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND (Elmt = 2 OR Elmt = 3) GROUP BY Geoname, Nombre HAVING Count(Nodos.Geoname)>1 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'CTs con nombre repetido' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND Elmt = 4 GROUP BY Geoname, Nombre HAVING Count(Nodos.Geoname)>1 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'salidas de alimentador sin códi de alimentador' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND Elmt = 8 AND ((Val1) Is null OR Val1 = '') INSERT INTO @t SELECT 'Nodos' AS Elemento, 'fuentes con errores de tensión' AS Problema,Geoname, Nombre FROM Nodos WHERE Tension>0 AND Elmt = 1 AND Val1 IS NULL INSERT INTO @t SELECT 'Nodos' AS Elemento, 'fuentes con mas de una línea' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND Nodos.estado=1 AND cant_lineas>1 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'seccionadores con mas de dos líneas' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND (Nodos.estado=2 OR Nodos.estado=3) AND cant_lineas>2 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'CTs con mas de dos líneas' AS Problema, Nodos.Geoname, Nodos.Nombre as Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND Nodos.estado=4 AND cant_lineas>2 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'CTs con usuarios y sin máquina' AS Problema, Nodos.Geoname, Nodos.Nombre FROM (Nodos INNER JOIN ((Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s) ON Nodos.Geoname = Suministros_Trafos.Geoname_t) LEFT JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct WHERE Tension>0 AND Nodos.elmt = 4 AND Usuarios.ES = 1 AND Transformadores.Id_trafo Is Null GROUP BY Nodos.Geoname, Nodos.Nombre HAVING Count(Usuarios.id_usuario)>0 INSERT INTO @t SELECT 'Nodos' AS Elemento, 'transformadores con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Transformadores INNER JOIN Nodos ON Transformadores.Id_ct = Nodos.Nombre INNER JOIN mNodos ON Nodos.Geoname = mNodos.Geoname WHERE Nodos.Tension>0 AND ((mNodos.fases IN (1,2,3) AND Transformadores.Conexionado <> 'M') OR (mNodos.fases IN ('12','23','13') AND Transformadores.Conexionado NOT IN ('M','B'))) AND Nodos.Elmt=4 GROUP BY nodos.Geoname, nodos.Nombre INSERT INTO @t SELECT 'Nodos' AS Elemento, 'usuarios con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo  WHERE Tension>0 AND Usuarios.fase='123' GROUP BY nodos.Geoname, nodos.Nombre HAVING MIN(fase) IN ('1','2','3','12','23','13') INSERT INTO @t SELECT 'Nodos' AS Elemento, 'nodos con inconsistencias de tarifas' AS Problema,A.Geoname, A.Nombre FROM (SELECT Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE Tension>0 GROUP BY Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension) AS A GROUP BY A.Geoname, A.Nombre HAVING Count(A.Nivel_Tension)>1 INSERT INTO @t SELECT DISTINCT 'Nodos' AS Elemento, 'nodos con inconsistencias de tarifas' AS Problema,Nodos.Geoname, Usuarios.tarifa AS Nombre FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE (Tension>0 AND ((Nodos.Tension)>1000) AND ((Tarifas.Nivel_Tension)='BT')) OR (Tension>0 AND ((Nodos.Tension)<1000) AND ((Tarifas.Nivel_Tension)='MT')) INSERT INTO @t SELECT 'Nodos' AS Elemento, 'usuarios con tarifas erroneas' AS Problema, Nodos.Geoname, CAST(Usuarios.id_usuario AS varchar) + '->'+ Usuarios.Tarifa AS Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo WHERE (Tension>0 AND ((Usuarios.ES)=1) AND ((Usuarios.tarifa) Is Null)) OR (Tension>0 AND ((Usuarios.tarifa) Not In (select tarifa from tarifas))) INSERT INTO @t SELECT 'Nodos' AS Elemento, 'alimentadores sin Nombre' AS Problema, nodos.Geoname, nodos.Nombre FROM Nodos WHERE Tension>0 AND Elmt = 8 AND (Val1='' OR Val1 IS NULL) INSERT INTO @t SELECT 'Nodos' AS Elemento, 'cambios de tension sin trafos' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta WHERE (Nodos.Tension>0 AND Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Tension>0 AND Nodos.Elmt=5 AND Lineas.Tension>0) INSERT INTO @t SELECT 'Nodos' AS Elemento, 'nodos con inconsistenacias de tensión' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE Nodos.Tension>0 AND Nodos.Geoname<>0 AND ((Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Elmt=5 AND Lineas.Tension>0)) select * from @t END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE PROCEDURE Crear_Red AS BEGIN SET NOCOUNT ON UPDATE Nodos SET Aux=0 WHERE Tension=0 UPDATE Lineas SET Aux=0 WHERE Tension=0 UPDATE A SET d=o FROM (SELECT ROW_NUMBER() OVER (ORDER BY Geoname) AS o, Aux AS d FROM Nodos WHERE Tension>0) A UPDATE A SET d=o FROM (SELECT ROW_NUMBER() OVER (ORDER BY Geoname) AS o, Aux AS d FROM Lineas WHERE Tension>0) A TRUNCATE TABLE mNodos TRUNCATE TABLE mLineas INSERT INTO mNodos SELECT 0 AS aux, 0 AS geoname, 0 AS estado, 0 AS navegado, 0 AS cant_lineas,0 AS linea1,0 AS linea2,0 AS linea3,0 AS linea4,0 AS linea5,0 AS linea6,0 AS linea7,0 AS linea8,0 AS linea9,0 AS linea10,0 AS linea11,0 AS linea12,0 AS linea13,0 AS linea14,0 AS linea15,0 AS linea16,0 AS linea17,0 AS linea18,0 AS linea19,0 AS linea20,0 AS linea21,0 AS linea22,0 AS linea23,0 AS linea24,0 AS linea25,0 AS linea26,0 AS linea27,0 AS linea28,0 AS linea29,0 AS linea30,0 AS linea31,0 AS linea32,0 AS fases, 1 AS tension, 0 AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, 0 AS aux8, 0 AS alim INSERT INTO mNodos SELECT aux, geoname, estado, 0 AS navegado, cant_lineas,ISNULL(linea1, 0) AS linea1,ISNULL(linea2, 0) AS linea2,ISNULL(linea3, 0) AS linea3,ISNULL(linea4, 0) AS linea4,ISNULL(linea5, 0) AS linea5,ISNULL(linea6, 0) AS linea6,ISNULL(linea7, 0) AS linea7,ISNULL(linea8, 0) AS linea8,ISNULL(linea9, 0) AS linea9,ISNULL(linea10, 0) AS linea10,ISNULL(linea11, 0) AS linea11,ISNULL(linea12, 0) AS linea12,ISNULL(linea13, 0) AS linea13,ISNULL(linea14, 0) AS linea14,ISNULL(linea15, 0) AS linea15,ISNULL(linea16, 0) AS linea16,ISNULL(linea17, 0) AS linea17,ISNULL(linea18, 0) AS linea18,ISNULL(linea19, 0) AS linea19,ISNULL(linea20, 0) AS linea20,ISNULL(linea21, 0) AS linea21,ISNULL(linea22, 0) AS linea22,ISNULL(linea23, 0) AS linea23,ISNULL(linea24, 0) AS linea24,ISNULL(linea25, 0) AS linea25,ISNULL(linea26, 0) AS linea26,ISNULL(linea27, 0) AS linea27,ISNULL(linea28, 0) AS linea28,ISNULL(linea29, 0) AS linea29,ISNULL(linea30, 0) AS linea30,ISNULL(linea31, 0) AS linea31,ISNULL(linea32, 0) AS linea32,0 AS fases, tension, elmt AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, 0 AS aux8,  alim FROM (SELECT C.aux, geoname, elmt, estado, tension, numero, linea, cant_lineas, alim FROM (SELECT aux, geoname, elmt, estado, B.tension, 'linea' + LTRIM(STR(ROW_NUMBER() OVER (PARTITION BY aux ORDER BY aux))) AS numero, linea, ISNULL(Alimentadores.Id, 0) AS alim FROM (SELECT Nodos.Aux, Nodos.Geoname, Nodos.Elmt, Nodos.Estado, Nodos.Tension, Lineas.Aux AS linea, nodos.Alimentador FROM dbo.Lineas INNER JOIN dbo.Nodos ON dbo.Lineas.Desde = dbo.Nodos.Geoname UNION SELECT Nodos_1.Aux, Nodos_1.Geoname, Nodos_1.Elmt, Nodos_1.Estado, Nodos_1.Tension, Lineas_1.Aux AS linea, nodos_1.Alimentador FROM dbo.Lineas AS Lineas_1 INNER JOIN dbo.Nodos AS Nodos_1 ON Lineas_1.Hasta = Nodos_1.Geoname) B LEFT JOIN Alimentadores ON B.Alimentador =Alimentadores.Id_Alim) C INNER JOIN (SELECT aux, COUNT(linea) AS cant_lineas FROM (SELECT aux, linea FROM (SELECT Nodos.Aux, Lineas.Aux AS linea FROM dbo.Lineas INNER JOIN dbo.Nodos ON dbo.Lineas.Desde = dbo.Nodos.Geoname UNION SELECT Nodos_1.Aux, Lineas_1.Aux AS linea FROM dbo.Lineas AS Lineas_1 INNER JOIN dbo.Nodos AS Nodos_1 ON Lineas_1.Hasta = Nodos_1.Geoname) D) E GROUP BY aux) A ON C.aux=A.aux WHERE Tension>0 ) Sal PIVOT (SUM(linea) FOR numero IN (linea1,linea2,linea3,linea4,linea5,linea6,linea7,linea8,linea9,linea10,linea11,linea12,linea13,linea14,linea15,linea16,linea17,linea18,linea19,linea20,linea21,linea22,linea23,linea24,linea25,linea26,linea27,linea28,linea29,linea30,linea31,linea32)) Pvt order by aux INSERT INTO mLineas SELECT  0 AS aux, 0 AS geoname, 0 AS desde, 0 AS hasta, 0 AS fuente, 1 AS tension, 0 AS fases, 0 AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, 0 AS alim INSERT INTO mLineas SELECT Lineas.aux, Lineas.geoname, Nodos.Aux AS desde, Nodos_1.Aux AS hasta, 0 AS fuente, Lineas.tension, Lineas.Fase AS fases, 0 AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, Alimentadores.Id AS alim FROM Lineas INNER JOIN Nodos ON Lineas.Desde = Nodos.Geoname INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname LEFT JOIN Alimentadores ON Lineas.Alimentador = Alimentadores.Id_Alim WHERE Lineas.Tension>0 ORDER BY Lineas.Aux UPDATE B SET d=o FROM  (SELECT mNodos.Fases AS d, A.Fases AS o FROM mNodos INNER JOIN (SELECT F.Geoname, MAX(F.Fases) AS Fases FROM (SELECT mNodos.Geoname, CONVERT(SMALLINT, dbo.mLineas.Fases) AS Fases FROM dbo.mLineas INNER JOIN dbo.mNodos ON dbo.mLineas.Desde = dbo.mNodos.Aux UNION SELECT mNodos.Geoname, CONVERT(SMALLINT, dbo.mLineas.Fases) AS Fases FROM dbo.mLineas INNER JOIN	dbo.mNodos ON dbo.mLineas.Hasta = dbo.mNodos.Aux) F GROUP BY F.Geoname) A ON mNodos.Geoname=A.Geoname) B iNSERT INTO mNodos SELECT aux, geoname, estado, 0 AS navegado, 0 AS cant_lineas, 0 AS linea1,0 AS linea2,0 AS linea3,0 AS linea4, 0 AS linea5,0 AS linea6,0 AS linea7,0 AS linea8, 0 AS linea9,0 AS linea10,0 AS linea11,0 AS linea12, 0 AS linea13,0 AS linea14,0 AS linea15,0 AS linea16, 0 AS linea17,0 AS linea18,0 AS linea19,0 AS linea20, 0 AS linea21,0 AS linea22,0 AS linea23,0 AS linea24, 0 AS linea25,0 AS linea26,0 AS linea27,0 AS linea28, 0 AS linea29,0 AS linea30,0 AS linea31,0 AS linea32, 0 AS fases, tension, elmt AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, 0 AS aux8, 0 AS alim FROM Nodos WHERE Tension>0 AND Geoname NOT IN (select Geoname FROM mNodos) END")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER PROCEDURE Crear_Red AS BEGIN SET NOCOUNT ON UPDATE Nodos SET Aux=0 WHERE Tension=0 UPDATE Lineas SET Aux=0 WHERE Tension=0 UPDATE A SET d=o FROM (SELECT ROW_NUMBER() OVER (ORDER BY Geoname) AS o, Aux AS d FROM Nodos WHERE Tension>0) A UPDATE A SET d=o FROM (SELECT ROW_NUMBER() OVER (ORDER BY Geoname) AS o, Aux AS d FROM Lineas WHERE Tension>0) A TRUNCATE TABLE mNodos TRUNCATE TABLE mLineas INSERT INTO mNodos SELECT 0 AS aux, 0 AS geoname, 0 AS estado, 0 AS navegado, 0 AS cant_lineas,0 AS linea1,0 AS linea2,0 AS linea3,0 AS linea4,0 AS linea5,0 AS linea6,0 AS linea7,0 AS linea8,0 AS linea9,0 AS linea10,0 AS linea11,0 AS linea12,0 AS linea13,0 AS linea14,0 AS linea15,0 AS linea16,0 AS linea17,0 AS linea18,0 AS linea19,0 AS linea20,0 AS linea21,0 AS linea22,0 AS linea23,0 AS linea24,0 AS linea25,0 AS linea26,0 AS linea27,0 AS linea28,0 AS linea29,0 AS linea30,0 AS linea31,0 AS linea32,0 AS fases, 1 AS tension, 0 AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, 0 AS aux8, 0 AS alim INSERT INTO mNodos SELECT aux, geoname, estado, 0 AS navegado, cant_lineas,ISNULL(linea1, 0) AS linea1,ISNULL(linea2, 0) AS linea2,ISNULL(linea3, 0) AS linea3,ISNULL(linea4, 0) AS linea4,ISNULL(linea5, 0) AS linea5,ISNULL(linea6, 0) AS linea6,ISNULL(linea7, 0) AS linea7,ISNULL(linea8, 0) AS linea8,ISNULL(linea9, 0) AS linea9,ISNULL(linea10, 0) AS linea10,ISNULL(linea11, 0) AS linea11,ISNULL(linea12, 0) AS linea12,ISNULL(linea13, 0) AS linea13,ISNULL(linea14, 0) AS linea14,ISNULL(linea15, 0) AS linea15,ISNULL(linea16, 0) AS linea16,ISNULL(linea17, 0) AS linea17,ISNULL(linea18, 0) AS linea18,ISNULL(linea19, 0) AS linea19,ISNULL(linea20, 0) AS linea20,ISNULL(linea21, 0) AS linea21,ISNULL(linea22, 0) AS linea22,ISNULL(linea23, 0) AS linea23,ISNULL(linea24, 0) AS linea24,ISNULL(linea25, 0) AS linea25,ISNULL(linea26, 0) AS linea26,ISNULL(linea27, 0) AS linea27,ISNULL(linea28, 0) AS linea28,ISNULL(linea29, 0) AS linea29,ISNULL(linea30, 0) AS linea30,ISNULL(linea31, 0) AS linea31,ISNULL(linea32, 0) AS linea32,0 AS fases, tension, elmt AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, 0 AS aux8,  alim FROM (SELECT C.aux, geoname, elmt, estado, tension, numero, linea, cant_lineas, alim FROM (SELECT aux, geoname, elmt, estado, B.tension, 'linea' + LTRIM(STR(ROW_NUMBER() OVER (PARTITION BY aux ORDER BY aux))) AS numero, linea, ISNULL(Alimentadores.Id, 0) AS alim FROM (SELECT Nodos.Aux, Nodos.Geoname, Nodos.Elmt, Nodos.Estado, Nodos.Tension, Lineas.Aux AS linea, nodos.Alimentador FROM dbo.Lineas INNER JOIN dbo.Nodos ON dbo.Lineas.Desde = dbo.Nodos.Geoname UNION SELECT Nodos_1.Aux, Nodos_1.Geoname, Nodos_1.Elmt, Nodos_1.Estado, Nodos_1.Tension, Lineas_1.Aux AS linea, nodos_1.Alimentador FROM dbo.Lineas AS Lineas_1 INNER JOIN dbo.Nodos AS Nodos_1 ON Lineas_1.Hasta = Nodos_1.Geoname) B LEFT JOIN Alimentadores ON B.Alimentador =Alimentadores.Id_Alim) C INNER JOIN (SELECT aux, COUNT(linea) AS cant_lineas FROM (SELECT aux, linea FROM (SELECT Nodos.Aux, Lineas.Aux AS linea FROM dbo.Lineas INNER JOIN dbo.Nodos ON dbo.Lineas.Desde = dbo.Nodos.Geoname UNION SELECT Nodos_1.Aux, Lineas_1.Aux AS linea FROM dbo.Lineas AS Lineas_1 INNER JOIN dbo.Nodos AS Nodos_1 ON Lineas_1.Hasta = Nodos_1.Geoname) D) E GROUP BY aux) A ON C.aux=A.aux WHERE Tension>0 ) Sal PIVOT (SUM(linea) FOR numero IN (linea1,linea2,linea3,linea4,linea5,linea6,linea7,linea8,linea9,linea10,linea11,linea12,linea13,linea14,linea15,linea16,linea17,linea18,linea19,linea20,linea21,linea22,linea23,linea24,linea25,linea26,linea27,linea28,linea29,linea30,linea31,linea32)) Pvt order by aux INSERT INTO mLineas SELECT  0 AS aux, 0 AS geoname, 0 AS desde, 0 AS hasta, 0 AS fuente, 1 AS tension, 0 AS fases, 0 AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, 0 AS alim INSERT INTO mLineas SELECT Lineas.aux, Lineas.geoname, Nodos.Aux AS desde, Nodos_1.Aux AS hasta, 0 AS fuente, Lineas.tension, Lineas.Fase AS fases, 0 AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, Alimentadores.Id AS alim FROM Lineas INNER JOIN Nodos ON Lineas.Desde = Nodos.Geoname INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname LEFT JOIN Alimentadores ON Lineas.Alimentador = Alimentadores.Id_Alim WHERE Lineas.Tension>0 ORDER BY Lineas.Aux UPDATE B SET d=o FROM  (SELECT mNodos.Fases AS d, A.Fases AS o FROM mNodos INNER JOIN (SELECT F.Geoname, MAX(F.Fases) AS Fases FROM (SELECT mNodos.Geoname, CONVERT(SMALLINT, dbo.mLineas.Fases) AS Fases FROM dbo.mLineas INNER JOIN dbo.mNodos ON dbo.mLineas.Desde = dbo.mNodos.Aux UNION SELECT mNodos.Geoname, CONVERT(SMALLINT, dbo.mLineas.Fases) AS Fases FROM dbo.mLineas INNER JOIN	dbo.mNodos ON dbo.mLineas.Hasta = dbo.mNodos.Aux) F GROUP BY F.Geoname) A ON mNodos.Geoname=A.Geoname) B iNSERT INTO mNodos SELECT aux, geoname, estado, 0 AS navegado, 0 AS cant_lineas, 0 AS linea1,0 AS linea2,0 AS linea3,0 AS linea4, 0 AS linea5,0 AS linea6,0 AS linea7,0 AS linea8, 0 AS linea9,0 AS linea10,0 AS linea11,0 AS linea12, 0 AS linea13,0 AS linea14,0 AS linea15,0 AS linea16, 0 AS linea17,0 AS linea18,0 AS linea19,0 AS linea20, 0 AS linea21,0 AS linea22,0 AS linea23,0 AS linea24, 0 AS linea25,0 AS linea26,0 AS linea27,0 AS linea28, 0 AS linea29,0 AS linea30,0 AS linea31,0 AS linea32, 0 AS fases, tension, elmt AS aux2, 0 AS aux3, 0 AS aux4, 0 AS aux5, 0 AS aux6, 0 AS aux7, 0 AS aux8, 0 AS alim FROM Nodos WHERE Tension>0 AND Geoname NOT IN (select Geoname FROM mNodos) END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE PROCEDURE Mover_Area @AREA INT, @VERTICE SMALLINT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @X1 DECIMAL(9,2) DECLARE @Y1 DECIMAL(9,2) DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_par VARCHAR(MAX) DECLARE @str_final VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @k SMALLINT DECLARE @SRID SMALLINT DECLARE @v SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=Areas.obj FROM Areas WHERE Areas.Geoname = @AREA SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @str_final='POLYGON ((' SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=0 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @X1=@X SET @Y1=@Y SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @V=0 WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) IF @VERTICE<>-1 BEGIN SET @V=@v+1 IF @VERTICE=@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END IF @VERTICE<>@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) END END IF @VERTICE=-1 BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=0 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) SET @str_final = @str_final + '))' SET @obj = geometry::STGeomFromText(@str_final, @SRID) SET @obj=@obj.MakeValid() IF @obj.STGeometryType()='Polygon' BEGIN UPDATE Areas SET obj=@obj WHERE Geoname = @AREA END END")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER PROCEDURE Mover_Area @AREA INT, @VERTICE SMALLINT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @X1 DECIMAL(9,2) DECLARE @Y1 DECIMAL(9,2) DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_par VARCHAR(MAX) DECLARE @str_final VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @k SMALLINT DECLARE @SRID SMALLINT DECLARE @v SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=Areas.obj FROM Areas WHERE Areas.Geoname = @AREA SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @str_final='POLYGON ((' SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=0 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @X1=@X SET @Y1=@Y SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @V=0 WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) IF @VERTICE<>-1 BEGIN SET @V=@v+1 IF @VERTICE=@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END IF @VERTICE<>@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) END END IF @VERTICE=-1 BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=0 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) SET @str_final = @str_final + '))' SET @obj = geometry::STGeomFromText(@str_final, @SRID) SET @obj=@obj.MakeValid() IF @obj.STGeometryType()='Polygon' BEGIN UPDATE Areas SET obj=@obj WHERE Geoname = @AREA END END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE PROCEDURE Mover_Eje @EJE INT, @VERTICE SMALLINT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @X1 DECIMAL(9,2) DECLARE @Y1 DECIMAL(9,2) DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_par VARCHAR(MAX) DECLARE @str_final VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @SRID SMALLINT DECLARE @v SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=Ejes.obj FROM Ejes WHERE Ejes.Geoname = @EJE SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '')  SET @str_final='LINESTRING (' SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=1 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @X1=@X SET @Y1=@Y SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) set @str_par = @str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<>1 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) SET @str_final = @str_final + ')' UPDATE Ejes SET obj=geometry::STGeomFromText(@str_final, @SRID) WHERE Geoname = @EJE END")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER PROCEDURE Mover_Eje @EJE INT, @VERTICE SMALLINT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @X1 DECIMAL(9,2) DECLARE @Y1 DECIMAL(9,2) DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_par VARCHAR(MAX) DECLARE @str_final VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @SRID SMALLINT DECLARE @v SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=Ejes.obj FROM Ejes WHERE Ejes.Geoname = @EJE SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '')  SET @str_final='LINESTRING (' SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=1 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @X1=@X SET @Y1=@Y SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) set @str_par = @str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<>1 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) SET @str_final = @str_final + ')' UPDATE Ejes SET obj=geometry::STGeomFromText(@str_final, @SRID) WHERE Geoname = @EJE END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE PROCEDURE Mover_Linea @LINEA INT, @VERTICE SMALLINT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_par VARCHAR(MAX) DECLARE @str_final VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @SRID SMALLINT DECLARE @v SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=Lineas.obj FROM Lineas WHERE Lineas.Geoname = @LINEA SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SET @str_final='LINESTRING (' SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @V=0 WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) IF @VERTICE<>0 BEGIN  SET @V=@v+1 IF @VERTICE=@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END IF @VERTICE<>@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) END END IF @VERTICE=0 BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) SET @str_final = @str_final + ')' UPDATE Lineas SET obj=geometry::STGeomFromText(@str_final, @SRID) WHERE Geoname = @LINEA END")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER PROCEDURE Mover_Linea @LINEA INT, @VERTICE SMALLINT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_par VARCHAR(MAX) DECLARE @str_final VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @SRID SMALLINT DECLARE @v SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=Lineas.obj FROM Lineas WHERE Lineas.Geoname = @LINEA SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SET @str_final='LINESTRING (' SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @V=0 WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) IF @VERTICE<>0 BEGIN  SET @V=@v+1 IF @VERTICE=@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END IF @VERTICE<>@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) END END IF @VERTICE=0 BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) SET @str_final = @str_final + ')' UPDATE Lineas SET obj=geometry::STGeomFromText(@str_final, @SRID) WHERE Geoname = @LINEA END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE PROCEDURE Mover_Nodo @NODO INT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(17,10) DECLARE @Y DECIMAL(17,10) DECLARE @LINEA INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=obj FROM Nodos WHERE Geoname = @NODO SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POINT (','') SET @str_obj = REPLACE(@str_obj, ')','') SELECT @i = CHARINDEX(' ', @str_obj) SET @X = LEFT(@str_obj, @i-1) + @DX SET @Y = RIGHT(@str_obj, LEN(@str_obj)-@i) + @DY SET @str_obj = 'POINT (' + CAST(@X AS VARCHAR) + ' ' +  CAST(@Y AS VARCHAR) + ')' UPDATE Nodos SET XCoord=@X, YCoord=@Y, obj=geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname=@NODO END")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER PROCEDURE Mover_Nodo @NODO INT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(17,10) DECLARE @Y DECIMAL(17,10) DECLARE @LINEA INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=obj FROM Nodos WHERE Geoname = @NODO SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POINT (','') SET @str_obj = REPLACE(@str_obj, ')','') SELECT @i = CHARINDEX(' ', @str_obj) SET @X = LEFT(@str_obj, @i-1) + @DX SET @Y = RIGHT(@str_obj, LEN(@str_obj)-@i) + @DY SET @str_obj = 'POINT (' + CAST(@X AS VARCHAR) + ' ' +  CAST(@Y AS VARCHAR) + ')' UPDATE Nodos SET XCoord=@X, YCoord=@Y, obj=geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname=@NODO END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE PROCEDURE Mover_Parcela @PARCELA INT, @VERTICE SMALLINT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @X1 DECIMAL(9,2) DECLARE @Y1 DECIMAL(9,2) DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_par VARCHAR(MAX) DECLARE @str_final VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @k SMALLINT DECLARE @SRID SMALLINT DECLARE @v SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=Parcelas.obj FROM Parcelas WHERE Parcelas.Geoname = @PARCELA SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @str_final='POLYGON ((' SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=0 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @X1=@X SET @Y1=@Y SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @V=0 WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) IF @VERTICE<>-1 BEGIN SET @V=@v+1 IF @VERTICE=@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END IF @VERTICE<>@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) END END IF @VERTICE=-1 BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=0 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) SET @str_final = @str_final + '))' SET @obj = geometry::STGeomFromText(@str_final, @SRID) SET @obj=@obj.MakeValid() IF @obj.STGeometryType()='Polygon' BEGIN UPDATE Parcelas SET obj=@obj WHERE Geoname = @PARCELA END END")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER PROCEDURE Mover_Parcela @PARCELA INT, @VERTICE SMALLINT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @X1 DECIMAL(9,2) DECLARE @Y1 DECIMAL(9,2) DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_par VARCHAR(MAX) DECLARE @str_final VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @k SMALLINT DECLARE @SRID SMALLINT DECLARE @v SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=Parcelas.obj FROM Parcelas WHERE Parcelas.Geoname = @PARCELA SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @str_final='POLYGON ((' SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=0 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @X1=@X SET @Y1=@Y SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @V=0 WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) IF @VERTICE<>-1 BEGIN SET @V=@v+1 IF @VERTICE=@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END IF @VERTICE<>@V BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) END END IF @VERTICE=-1 BEGIN SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) + @DX SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) + ', ' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) IF @VERTICE<=0 BEGIN SET @X = @X + @DX SET @Y = @Y + @DY END SET @str_final = @str_final + CAST(@X AS varchar) + ' ' + CAST(@Y AS varchar) SET @str_final = @str_final + '))' SET @obj = geometry::STGeomFromText(@str_final, @SRID) SET @obj=@obj.MakeValid() IF @obj.STGeometryType()='Polygon' BEGIN UPDATE Parcelas SET obj=@obj WHERE Geoname = @PARCELA END END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE PROCEDURE Mover_Poste @POSTE INT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(17,10) DECLARE @Y DECIMAL(17,10) DECLARE @LINEA INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=obj FROM Postes WHERE Geoname = @POSTE SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POINT (','') SET @str_obj = REPLACE(@str_obj, ')','') SELECT @i = CHARINDEX(' ', @str_obj) SET @X = LEFT(@str_obj, @i-1) + @DX SET @Y = RIGHT(@str_obj, LEN(@str_obj)-@i) + @DY SET @str_obj = 'POINT (' + CAST(@X AS VARCHAR) + ' ' +  CAST(@Y AS VARCHAR) + ')' UPDATE Postes SET XCoord=@X, YCoord=@Y, obj=geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname=@POSTE END")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER PROCEDURE Mover_Poste @POSTE INT, @DX FLOAT, @DY FLOAT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(17,10) DECLARE @Y DECIMAL(17,10) DECLARE @LINEA INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @obj=obj FROM Postes WHERE Geoname = @POSTE SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POINT (','') SET @str_obj = REPLACE(@str_obj, ')','') SELECT @i = CHARINDEX(' ', @str_obj) SET @X = LEFT(@str_obj, @i-1) + @DX SET @Y = RIGHT(@str_obj, LEN(@str_obj)-@i) + @DY SET @str_obj = 'POINT (' + CAST(@X AS VARCHAR) + ' ' +  CAST(@Y AS VARCHAR) + ')' UPDATE Postes SET XCoord=@X, YCoord=@Y, obj=geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname=@POSTE END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE PROCEDURE Normalizar_Linea @LINEA INT, @SRID SMALLINT AS BEGIN SET NOCOUNT ON DECLARE @X1 DECIMAL(17,10) DECLARE @Y1 DECIMAL(17,10) DECLARE @X2 DECIMAL(17,10) DECLARE @Y2 DECIMAL(17,10) DECLARE @NODO INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT SELECT @X1=Nodos.XCoord, @Y1=Nodos.YCoord, @X2=Nodos_1.XCoord, @Y2=Nodos_1.YCoord, @obj=Lineas.obj FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname WHERE Lineas.Geoname = @LINEA SET @str_obj = @obj.ToString() IF NOT @str_obj IS NULL BEGIN SELECT @i = CHARINDEX(',', @str_obj) SET @str_obj = 'LINESTRING (' + CAST(@X1 AS VARCHAR) + ' ' +  CAST(@Y1 AS VARCHAR) + ',' + RIGHT(@str_obj, LEN(@str_obj)-@i) select @str_obj UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA SET @str_obj = @obj.ToString() SELECT @j = CHARINDEX(',', @str_obj) SET @i=@j WHILE @j<>0 BEGIN SET @i=@j SELECT @j = CHARINDEX(',', @str_obj, @i+1) END SET @str_obj = LEFT(@str_obj, @i-1) + ', ' + CAST(@X2 AS VARCHAR) + ' ' +  CAST(@Y2 AS VARCHAR) select @str_obj UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA END IF @str_obj IS NULL BEGIN SET @str_obj = 'LINESTRING (' + CAST(@X1 AS VARCHAR) + ' ' +  CAST(@Y1 AS VARCHAR) + ',' + CAST(@X2 AS VARCHAR) + ' ' +  CAST(@Y2 AS VARCHAR) + ')' select @str_obj UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA END END")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER PROCEDURE Normalizar_Linea @LINEA INT, @SRID SMALLINT AS BEGIN SET NOCOUNT ON DECLARE @X1 DECIMAL(17,10) DECLARE @Y1 DECIMAL(17,10) DECLARE @X2 DECIMAL(17,10) DECLARE @Y2 DECIMAL(17,10) DECLARE @NODO INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT SELECT @X1=Nodos.XCoord, @Y1=Nodos.YCoord, @X2=Nodos_1.XCoord, @Y2=Nodos_1.YCoord, @obj=Lineas.obj FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname WHERE Lineas.Geoname = @LINEA SET @str_obj = @obj.ToString() IF NOT @str_obj IS NULL BEGIN SELECT @i = CHARINDEX(',', @str_obj) SET @str_obj = 'LINESTRING (' + CAST(@X1 AS VARCHAR) + ' ' +  CAST(@Y1 AS VARCHAR) + ',' + RIGHT(@str_obj, LEN(@str_obj)-@i) select @str_obj UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA SET @str_obj = @obj.ToString() SELECT @j = CHARINDEX(',', @str_obj) SET @i=@j WHILE @j<>0 BEGIN SET @i=@j SELECT @j = CHARINDEX(',', @str_obj, @i+1) END SET @str_obj = LEFT(@str_obj, @i-1) + ', ' + CAST(@X2 AS VARCHAR) + ' ' +  CAST(@Y2 AS VARCHAR) select @str_obj UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA END IF @str_obj IS NULL BEGIN SET @str_obj = 'LINESTRING (' + CAST(@X1 AS VARCHAR) + ' ' +  CAST(@Y1 AS VARCHAR) + ',' + CAST(@X2 AS VARCHAR) + ' ' +  CAST(@Y2 AS VARCHAR) + ')' select @str_obj UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA END END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE PROCEDURE Normalizar_Nodo @NODO INT, @SRID SMALLINT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(17,10) DECLARE @Y DECIMAL(17,10) DECLARE @LINEA INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT SELECT @obj=obj FROM Nodos WHERE Geoname = @NODO SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POINT (','') SET @str_obj = REPLACE(@str_obj, ')','') SELECT @i = CHARINDEX(' ', @str_obj) SET @X = LEFT(@str_obj, @i-1) SET @Y = RIGHT(@str_obj, LEN(@str_obj)-@i) UPDATE Nodos SET XCoord=@X, YCoord=@Y WHERE Geoname=@NODO DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM Lineas WHERE Desde=@NODO OPEN RS FETCH NEXT FROM RS INTO @LINEA, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SELECT @i = CHARINDEX(',', @str_obj) SET @str_obj = 'LINESTRING (' + CAST(@X AS VARCHAR) + ' ' +  CAST(@Y AS VARCHAR) + ',' + RIGHT(@str_obj, LEN(@str_obj)-@i) UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA FETCH NEXT FROM RS INTO @LINEA, @obj END CLOSE RS DEALLOCATE RS DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM Lineas WHERE Hasta=@NODO OPEN RS FETCH NEXT FROM RS INTO @LINEA, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SELECT @j = CHARINDEX(',', @str_obj) SET @i=@j WHILE @j<>0 BEGIN SET @i=@j SELECT @j = CHARINDEX(',', @str_obj, @i+1) END SET @str_obj = LEFT(@str_obj, @i-1) + ', ' + CAST(@X AS VARCHAR) + ' ' +  CAST(@Y AS VARCHAR) + ')' UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA FETCH NEXT FROM RS INTO @LINEA, @obj END CLOSE RS DEALLOCATE RS END")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER PROCEDURE Normalizar_Nodo @NODO INT, @SRID SMALLINT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(17,10) DECLARE @Y DECIMAL(17,10) DECLARE @LINEA INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT SELECT @obj=obj FROM Nodos WHERE Geoname = @NODO SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POINT (','') SET @str_obj = REPLACE(@str_obj, ')','') SELECT @i = CHARINDEX(' ', @str_obj) SET @X = LEFT(@str_obj, @i-1) SET @Y = RIGHT(@str_obj, LEN(@str_obj)-@i) UPDATE Nodos SET XCoord=@X, YCoord=@Y WHERE Geoname=@NODO DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM Lineas WHERE Desde=@NODO OPEN RS FETCH NEXT FROM RS INTO @LINEA, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SELECT @i = CHARINDEX(',', @str_obj) SET @str_obj = 'LINESTRING (' + CAST(@X AS VARCHAR) + ' ' +  CAST(@Y AS VARCHAR) + ',' + RIGHT(@str_obj, LEN(@str_obj)-@i) UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA FETCH NEXT FROM RS INTO @LINEA, @obj END CLOSE RS DEALLOCATE RS DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM Lineas WHERE Hasta=@NODO OPEN RS FETCH NEXT FROM RS INTO @LINEA, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SELECT @j = CHARINDEX(',', @str_obj) SET @i=@j WHILE @j<>0 BEGIN SET @i=@j SELECT @j = CHARINDEX(',', @str_obj, @i+1) END SET @str_obj = LEFT(@str_obj, @i-1) + ', ' + CAST(@X AS VARCHAR) + ' ' +  CAST(@Y AS VARCHAR) + ')' UPDATE Lineas SET obj = geometry::STGeomFromText(@str_obj, @SRID) WHERE Geoname = @LINEA FETCH NEXT FROM RS INTO @LINEA, @obj END CLOSE RS DEALLOCATE RS END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE PROCEDURE Normalizar_Poste @POSTE INT, @SRID SMALLINT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(17,10) DECLARE @Y DECIMAL(17,10) DECLARE @LINEA INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT SELECT @obj=obj FROM Postes WHERE Geoname = @POSTE SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POINT (','') SET @str_obj = REPLACE(@str_obj, ')','') SELECT @i = CHARINDEX(' ', @str_obj) SET @X = LEFT(@str_obj, @i-1) SET @Y = RIGHT(@str_obj, LEN(@str_obj)-@i) UPDATE Postes SET XCoord=@X, YCoord=@Y WHERE Geoname=@POSTE END")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER PROCEDURE Normalizar_Poste @POSTE INT, @SRID SMALLINT AS BEGIN SET NOCOUNT ON DECLARE @X DECIMAL(17,10) DECLARE @Y DECIMAL(17,10) DECLARE @LINEA INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @j SMALLINT SELECT @obj=obj FROM Postes WHERE Geoname = @POSTE SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POINT (','') SET @str_obj = REPLACE(@str_obj, ')','') SELECT @i = CHARINDEX(' ', @str_obj) SET @X = LEFT(@str_obj, @i-1) SET @Y = RIGHT(@str_obj, LEN(@str_obj)-@i) UPDATE Postes SET XCoord=@X, YCoord=@Y WHERE Geoname=@POSTE END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE TRIGGER [Actualizo_Nodos] ON [Nodos] AFTER UPDATE AS BEGIN SET NOCOUNT ON DECLARE @geoname INT DECLARE @estado SMALLINT DECLARE @elmt SMALLINT DECLARE @tension INT DECLARE @x FLOAT DECLARE @y FLOAT DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' IF UPDATE(obj) BEGIN DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname WHILE (@@FETCH_STATUS = 0) BEGIN EXEC dbo.Normalizar_Nodo @geoname, @SRID INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'ACTUALIZO_NODO', NOMBRE + ';' + (CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[XCOORD])) +';'+ CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[YCOORD]))) FROM INSERTED WHERE Geoname = @geoname FETCH NEXT FROM RS INTO @geoname END CLOSE RS DEALLOCATE RS END IF UPDATE(XCOORD) OR UPDATE (YCOORD) BEGIN DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, xcoord, ycoord FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @x, @y WHILE (@@FETCH_STATUS = 0) BEGIN UPDATE Nodos SET obj=geometry::Point(@x, @y, @SRID) WHERE Geoname=@geoname EXEC dbo.Normalizar_Nodo @geoname, @SRID FETCH NEXT FROM RS INTO @geoname, @x, @y END CLOSE RS END IF UPDATE(elmt) OR UPDATE(estado) BEGIN DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, elmt, estado FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @elmt, @estado WHILE (@@FETCH_STATUS = 0) BEGIN IF @estado IS NULL BEGIN SET @estado = @elmt END UPDATE mNodos SET estado=@estado, aux2=@elmt WHERE geoname=@geoname FETCH NEXT FROM RS INTO @geoname, @elmt, @estado END CLOSE RS DEALLOCATE RS END IF UPDATE(tension) BEGIN DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, tension FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @tension WHILE (@@FETCH_STATUS = 0) BEGIN UPDATE mNodos SET tension=@tension WHERE geoname=@geoname FETCH NEXT FROM RS INTO @geoname, @tension END CLOSE RS DEALLOCATE RS END END")
            cursor.execute("ALTER TABLE Nodos ENABLE TRIGGER Actualizo_Nodos")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER TRIGGER [Actualizo_Nodos] ON [Nodos] AFTER UPDATE AS BEGIN SET NOCOUNT ON DECLARE @geoname INT DECLARE @estado SMALLINT DECLARE @elmt SMALLINT DECLARE @tension INT DECLARE @x FLOAT DECLARE @y FLOAT DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' IF UPDATE(obj) BEGIN DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname WHILE (@@FETCH_STATUS = 0) BEGIN EXEC dbo.Normalizar_Nodo @geoname, @SRID INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'ACTUALIZO_NODO', NOMBRE + ';' + (CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[XCOORD])) +';'+ CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[YCOORD]))) FROM INSERTED WHERE Geoname = @geoname FETCH NEXT FROM RS INTO @geoname END CLOSE RS DEALLOCATE RS END IF UPDATE(XCOORD) OR UPDATE (YCOORD) BEGIN DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, xcoord, ycoord FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @x, @y WHILE (@@FETCH_STATUS = 0) BEGIN UPDATE Nodos SET obj=geometry::Point(@x, @y, @SRID) WHERE Geoname=@geoname EXEC dbo.Normalizar_Nodo @geoname, @SRID FETCH NEXT FROM RS INTO @geoname, @x, @y END CLOSE RS END IF UPDATE(elmt) OR UPDATE(estado) BEGIN DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, elmt, estado FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @elmt, @estado WHILE (@@FETCH_STATUS = 0) BEGIN IF @estado IS NULL BEGIN SET @estado = @elmt END UPDATE mNodos SET estado=@estado, aux2=@elmt WHERE geoname=@geoname FETCH NEXT FROM RS INTO @geoname, @elmt, @estado END CLOSE RS DEALLOCATE RS END IF UPDATE(tension) BEGIN DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, tension FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @tension WHILE (@@FETCH_STATUS = 0) BEGIN UPDATE mNodos SET tension=@tension WHERE geoname=@geoname FETCH NEXT FROM RS INTO @geoname, @tension END CLOSE RS DEALLOCATE RS END END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE TRIGGER [Borro_Nodos] ON [Nodos] AFTER DELETE AS BEGIN SET NOCOUNT ON DECLARE @geoname INT DECLARE @nombre VARCHAR(50) DECLARE @elmt SMALLINT DECLARE @tension SMALLINT DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, nombre, elmt, tension FROM DELETED OPEN RS FETCH NEXT FROM RS INTO @geoname, @nombre, @elmt, @tension WHILE (@@FETCH_STATUS = 0) BEGIN IF @tension>0 BEGIN DELETE FROM Lineas WHERE Desde=@geoname OR Hasta=@geoname IF @elmt = 6 BEGIN DELETE FROM Suministros WHERE id_nodo = @geoname END IF @elmt = 4 BEGIN UPDATE Transformadores SET id_ct='', usado=1 WHERE id_ct = @nombre END UPDATE mNodos SET geoname=0,estado=0,navegado=0,cant_lineas=0,linea1=0,linea2=0,linea3=0,linea4=0,linea5=0,linea6=0,linea7=0,linea8=0,linea9=0,linea10=0,linea11=0,linea12=0,linea13=0,linea14=0,linea15=0,linea16=0,linea17=0,linea18=0,linea19=0,linea20=0,linea21=0,linea22=0,linea23=0,linea24=0,linea25=0,linea26=0,linea27=0,linea28=0,linea29=0,linea30=0,linea31=0,linea32=0,fases=0,tension=0,aux2=0,aux3=0,aux4=0,aux5=07,aux6=0,aux7=0,aux8=0,alim=0 WHERE geoname = @geoname INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'BORRO_NODO', NOMBRE + ';' + (CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[XCOORD])) +';'+ CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[YCOORD]))) FROM DELETED WHERE GEONAME = @geoname INSERT INTO Nodos_Borrados SELECT * FROM DELETED WHERE GEONAME = @geoname END FETCH NEXT FROM RS INTO @geoname, @nombre, @elmt, @tension END CLOSE RS DEALLOCATE RS END")
            cursor.execute("ALTER TABLE Nodos ENABLE TRIGGER Borro_Nodos")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER TRIGGER [Borro_Nodos] ON [Nodos] AFTER DELETE AS BEGIN SET NOCOUNT ON DECLARE @geoname INT DECLARE @nombre VARCHAR(50) DECLARE @elmt SMALLINT DECLARE @tension SMALLINT DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, nombre, elmt, tension FROM DELETED OPEN RS FETCH NEXT FROM RS INTO @geoname, @nombre, @elmt, @tension WHILE (@@FETCH_STATUS = 0) BEGIN IF @tension>0 BEGIN DELETE FROM Lineas WHERE Desde=@geoname OR Hasta=@geoname IF @elmt = 6 BEGIN DELETE FROM Suministros WHERE id_nodo = @geoname END IF @elmt = 4 BEGIN UPDATE Transformadores SET id_ct='', usado=1 WHERE id_ct = @nombre END UPDATE mNodos SET geoname=0,estado=0,navegado=0,cant_lineas=0,linea1=0,linea2=0,linea3=0,linea4=0,linea5=0,linea6=0,linea7=0,linea8=0,linea9=0,linea10=0,linea11=0,linea12=0,linea13=0,linea14=0,linea15=0,linea16=0,linea17=0,linea18=0,linea19=0,linea20=0,linea21=0,linea22=0,linea23=0,linea24=0,linea25=0,linea26=0,linea27=0,linea28=0,linea29=0,linea30=0,linea31=0,linea32=0,fases=0,tension=0,aux2=0,aux3=0,aux4=0,aux5=07,aux6=0,aux7=0,aux8=0,alim=0 WHERE geoname = @geoname INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'BORRO_NODO', NOMBRE + ';' + (CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[XCOORD])) +';'+ CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),[YCOORD]))) FROM DELETED WHERE GEONAME = @geoname INSERT INTO Nodos_Borrados SELECT * FROM DELETED WHERE GEONAME = @geoname END FETCH NEXT FROM RS INTO @geoname, @nombre, @elmt, @tension END CLOSE RS DEALLOCATE RS END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE TRIGGER [Creo_Nodos] ON [Nodos] AFTER INSERT AS BEGIN SET NOCOUNT ON DECLARE @aux INT DECLARE @geoname INT DECLARE @elmt SMALLINT DECLARE @tension INT DECLARE @flag_nuevo_aux TINYINT SELECT @geoname = geoname, @elmt = ISNULL(elmt, 0), @tension = tension FROM INSERTED IF @tension>0 BEGIN SELECT @aux = MAX(aux) FROM mNodos WHERE geoname=0 SET @flag_nuevo_aux=0 IF @aux=0 BEGIN SELECT @aux = COUNT(*) FROM mNodos SET @flag_nuevo_aux=1 END IF @flag_nuevo_aux=0 BEGIN UPDATE mNodos SET geoname=@geoname,estado=@elmt,navegado=0,cant_lineas=0,linea1=0,linea2=0,linea3=0,linea4=0,linea5=0,linea6=0,linea7=0,linea8=0,linea9=0,linea10=0,linea11=0,linea12=0,linea13=0,linea14=0,linea15=0,linea16=0,linea17=0,linea18=0,linea19=0,linea20=0,linea21=0,linea22=0,linea23=0,linea24=0,linea25=0,linea26=0,linea27=0,linea28=0,linea29=0,linea30=0,linea31=0,linea32=0,fases=0,tension=@tension,aux2=@elmt,aux3=0,aux4=0,aux5=0,aux6=0,aux7=0,aux8=0,alim=0 WHERE aux=@aux END IF @flag_nuevo_aux=1 BEGIN INSERT INTO mNodos (aux,geoname,estado,navegado,cant_lineas,linea1,linea2,linea3,linea4,linea5,linea6,linea7,linea8,linea9,linea10,linea11,linea12,linea13,linea14,linea15,linea16,linea17,linea18,linea19,linea20,linea21,linea22,linea23,linea24,linea25,linea26,linea27,linea28,linea29,linea30,linea31,linea32,fases,tension,aux2,aux3,aux4,aux5,aux6,aux7,aux8,alim) VALUES (@aux,@geoname,@elmt,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,@tension,@elmt,0,0,0,0,0,0,0) END END END")
            cursor.execute("ALTER TABLE Nodos ENABLE TRIGGER Creo_Nodos")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER TRIGGER [Creo_Nodos] ON [Nodos] AFTER INSERT AS BEGIN SET NOCOUNT ON DECLARE @aux INT DECLARE @geoname INT DECLARE @elmt SMALLINT DECLARE @tension INT DECLARE @flag_nuevo_aux TINYINT SELECT @geoname = geoname, @elmt = ISNULL(elmt, 0), @tension = tension FROM INSERTED IF @tension>0 BEGIN SELECT @aux = MAX(aux) FROM mNodos WHERE geoname=0 SET @flag_nuevo_aux=0 IF @aux=0 BEGIN SELECT @aux = COUNT(*) FROM mNodos SET @flag_nuevo_aux=1 END IF @flag_nuevo_aux=0 BEGIN UPDATE mNodos SET geoname=@geoname,estado=@elmt,navegado=0,cant_lineas=0,linea1=0,linea2=0,linea3=0,linea4=0,linea5=0,linea6=0,linea7=0,linea8=0,linea9=0,linea10=0,linea11=0,linea12=0,linea13=0,linea14=0,linea15=0,linea16=0,linea17=0,linea18=0,linea19=0,linea20=0,linea21=0,linea22=0,linea23=0,linea24=0,linea25=0,linea26=0,linea27=0,linea28=0,linea29=0,linea30=0,linea31=0,linea32=0,fases=0,tension=@tension,aux2=@elmt,aux3=0,aux4=0,aux5=0,aux6=0,aux7=0,aux8=0,alim=0 WHERE aux=@aux END IF @flag_nuevo_aux=1 BEGIN INSERT INTO mNodos (aux,geoname,estado,navegado,cant_lineas,linea1,linea2,linea3,linea4,linea5,linea6,linea7,linea8,linea9,linea10,linea11,linea12,linea13,linea14,linea15,linea16,linea17,linea18,linea19,linea20,linea21,linea22,linea23,linea24,linea25,linea26,linea27,linea28,linea29,linea30,linea31,linea32,fases,tension,aux2,aux3,aux4,aux5,aux6,aux7,aux8,alim) VALUES (@aux,@geoname,@elmt,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,@tension,@elmt,0,0,0,0,0,0,0) END END END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE TRIGGER [Actualizo_Lineas] ON [Lineas] AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @quiebres VARCHAR(255) DECLARE @SRID SMALLINT DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(6,2) DECLARE @ddy DECIMAL(6,2) SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @xant = @X SET @yant = @Y SET @str_quiebres = '' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END UPDATE Lineas SET longitud=obj.STLength(), quiebres=@str_quiebres WHERE Geoname = @geoname INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT @geoname, GETDATE(),'ACTUALIZO_LINEA', @quiebres FROM INSERTED FETCH NEXT FROM RS INTO @geoname, @obj END CLOSE RS DEALLOCATE RS END END")
            cursor.execute("ALTER TABLE Lineas ENABLE TRIGGER Actualizo_Lineas")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER TRIGGER [Actualizo_Lineas] ON [Lineas] AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @quiebres VARCHAR(255) DECLARE @SRID SMALLINT DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(6,2) DECLARE @ddy DECIMAL(6,2) SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @xant = @X SET @yant = @Y SET @str_quiebres = '' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END UPDATE Lineas SET longitud=obj.STLength(), quiebres=@str_quiebres WHERE Geoname = @geoname INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT @geoname, GETDATE(),'ACTUALIZO_LINEA', @quiebres FROM INSERTED FETCH NEXT FROM RS INTO @geoname, @obj END CLOSE RS DEALLOCATE RS END END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE TRIGGER [Borro_Lineas] ON [Lineas] AFTER DELETE AS BEGIN SET NOCOUNT ON DECLARE @aux INT DECLARE @geoname INT DECLARE @desde INT DECLARE @hasta INT DECLARE @aux_desde INT DECLARE @aux_hasta INT DECLARE @tension INT DECLARE @cant_lineas_desde INT DECLARE @cant_lineas_hasta INT DECLARE @str_sql NVARCHAR(MAX) DECLARE @linea1 INT DECLARE @linea2 INT DECLARE @linea3 INT DECLARE @linea4 INT DECLARE @linea5 INT DECLARE @linea6 INT DECLARE @linea7 INT DECLARE @linea8 INT DECLARE @linea9 INT DECLARE @linea10 INT DECLARE @linea11 INT DECLARE @linea12 INT DECLARE @linea13 INT DECLARE @linea14 INT DECLARE @linea15 INT DECLARE @linea16 INT DECLARE @linea17 INT DECLARE @linea18 INT DECLARE @linea19 INT DECLARE @linea20 INT DECLARE @linea21 INT DECLARE @linea22 INT DECLARE @linea23 INT DECLARE @linea24 INT DECLARE @linea25 INT DECLARE @linea26 INT DECLARE @linea27 INT DECLARE @linea28 INT DECLARE @linea29 INT DECLARE @linea30 INT DECLARE @linea31 INT DECLARE @linea32 INT DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @sql_desde VARCHAR(MAX) DECLARE @sql_hasta VARCHAR(MAX) DECLARE @n SMALLINT DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, desde, hasta, tension FROM DELETED OPEN RS FETCH NEXT FROM RS INTO @geoname, @desde, @hasta, @tension WHILE (@@FETCH_STATUS = 0) BEGIN IF @tension>0 BEGIN select @aux = aux FROM mLineas WHERE Geoname = @geoname select @aux_desde=aux,@cant_lineas_desde=cant_lineas,@linea1=linea1,@linea2=linea2,@linea3=linea3,@linea4=linea4,@linea5=linea5,@linea6=linea6,@linea7=linea7,@linea8=linea8,@linea9=linea9,@linea10=linea10,@linea11=linea11,@linea12=linea12,@linea13=linea13,@linea14=linea14,@linea15=linea15,@linea16=linea16,@linea17=linea17,@linea18=linea18,@linea19=linea19,@linea20=linea20,@linea21=linea21,@linea22=linea22,@linea23=linea23,@linea24=linea24,@linea25=linea25,@linea26=linea26,@linea27=linea27,@linea28=linea28,@linea29=linea29,@linea30=linea30,@linea31=linea31,@linea32=linea32 FROM mNodos WHERE Geoname = @desde SET @i=0 IF @linea1=@aux BEGIN SET @i=1 END IF @linea2=@aux BEGIN SET @i=2 END IF @linea3=@aux BEGIN SET @i=3 END IF @linea4=@aux BEGIN SET @i=4 END IF @linea5=@aux BEGIN SET @i=5 END IF @linea6=@aux BEGIN SET @i=6 END IF @linea7=@aux BEGIN SET @i=7 END IF @linea8=@aux BEGIN SET @i=8 END IF @linea9=@aux BEGIN SET @i=9 END IF @linea10=@aux BEGIN SET @i=10 END IF @linea11=@aux BEGIN SET @i=11 END IF @linea12=@aux BEGIN SET @i=12 END IF @linea13=@aux BEGIN SET @i=13 END IF @linea14=@aux BEGIN SET @i=14 END IF @linea15=@aux BEGIN SET @i=15 END IF @linea16=@aux BEGIN SET @i=16 END IF @linea17=@aux BEGIN SET @i=17 END IF @linea18=@aux BEGIN SET @i=18 END IF @linea19=@aux BEGIN SET @i=19 END IF @linea20=@aux BEGIN SET @i=20 END IF @linea21=@aux BEGIN SET @i=21 END IF @linea22=@aux BEGIN SET @i=22 END IF @linea23=@aux BEGIN SET @i=23 END IF @linea24=@aux BEGIN SET @i=24 END IF @linea25=@aux BEGIN SET @i=25 END IF @linea26=@aux BEGIN SET @i=26 END IF @linea27=@aux BEGIN SET @i=27 END IF @linea28=@aux BEGIN SET @i=28 END IF @linea29=@aux BEGIN SET @i=29 END IF @linea30=@aux BEGIN SET @i=30 END IF @linea31=@aux BEGIN SET @i=31 END IF @linea32=@aux BEGIN SET @i=32 END SET @sql_desde='' SET @n=@i IF @n=0 BEGIN SET @n=1 END WHILE @n < 32 BEGIN SET @sql_desde=@sql_desde + ',linea' + CAST(@n AS VARCHAR) + '=linea' + CAST(@n+1 AS VARCHAR) SET @n = @n + 1 END SET @sql_desde=@sql_desde + ',linea32=0' select @aux_hasta=aux,@cant_lineas_hasta=cant_lineas,@linea1=linea1,@linea2=linea2,@linea3=linea3,@linea4=linea4,@linea5=linea5,@linea6=linea6,@linea7=linea7,@linea8=linea8,@linea9=linea9,@linea10=linea10,@linea11=linea11,@linea12=linea12,@linea13=linea13,@linea14=linea14,@linea15=linea15,@linea16=linea16,@linea17=linea17,@linea18=linea18,@linea19=linea19,@linea20=linea20,@linea21=linea21,@linea22=linea22,@linea23=linea23,@linea24=linea24,@linea25=linea25,@linea26=linea26,@linea27=linea27,@linea28=linea28,@linea29=linea29,@linea30=linea30,@linea31=linea31,@linea32=linea32 FROM mNodos WHERE Geoname = @hasta SET @j=0 IF @linea1=@aux BEGIN SET @j=1 END IF @linea2=@aux BEGIN SET @j=2 END IF @linea3=@aux BEGIN SET @j=3 END IF @linea4=@aux BEGIN SET @j=4 END IF @linea5=@aux BEGIN SET @j=5 END IF @linea6=@aux BEGIN SET @j=6 END IF @linea7=@aux BEGIN SET @j=7 END IF @linea8=@aux BEGIN SET @j=8 END IF @linea9=@aux BEGIN SET @j=9 END IF @linea10=@aux BEGIN SET @j=10 END IF @linea11=@aux BEGIN SET @j=11 END IF @linea12=@aux BEGIN SET @j=12 END IF @linea13=@aux BEGIN SET @j=13 END IF @linea14=@aux BEGIN SET @j=14 END IF @linea15=@aux BEGIN SET @j=15 END IF @linea16=@aux BEGIN SET @j=16 END IF @linea17=@aux BEGIN SET @j=17 END IF @linea18=@aux BEGIN SET @j=18 END IF @linea19=@aux BEGIN SET @j=19 END IF @linea20=@aux BEGIN SET @j=20 END IF @linea21=@aux BEGIN SET @j=21 END IF @linea22=@aux BEGIN SET @j=22 END IF @linea23=@aux BEGIN SET @j=23 END IF @linea24=@aux BEGIN SET @j=24 END IF @linea25=@aux BEGIN SET @j=25 END IF @linea26=@aux BEGIN SET @j=26 END IF @linea27=@aux BEGIN SET @j=27 END IF @linea28=@aux BEGIN SET @j=28 END IF @linea29=@aux BEGIN SET @j=29 END IF @linea30=@aux BEGIN SET @j=30 END IF @linea31=@aux BEGIN SET @j=31 END IF @linea32=@aux BEGIN SET @j=32 END SET @sql_hasta='' SET @n=@j IF @n=0 BEGIN SET @n=1 END WHILE @n < 32 BEGIN SET @sql_hasta=@sql_hasta + ',linea' + CAST(@n AS VARCHAR) + '=linea' + CAST(@n+1 AS VARCHAR) SET @n = @n + 1 END SET @sql_hasta=@sql_hasta + ',linea32=0' UPDATE mLineas SET geoname=0,desde=0,hasta=0,fuente=0,tension=0,fases=0 WHERE geoname = @geoname SET @str_sql = 'UPDATE mNodos SET cant_lineas = ' + CAST(@cant_lineas_desde - 1 AS VARCHAR) + @sql_desde + ' WHERE geoname =' + CAST(@desde AS VARCHAR) EXEC sp_executesql @str_sql SET @str_sql = 'UPDATE mNodos SET cant_lineas = ' + CAST(@cant_lineas_hasta - 1 AS VARCHAR) + @sql_hasta + ' WHERE geoname =' + CAST(@hasta AS VARCHAR) EXEC sp_executesql @str_sql UPDATE B SET d=o FROM (SELECT mNodos.Fases AS d, A.Fases AS o FROM mNodos INNER JOIN (SELECT F.Geoname, MAX(F.Fases) AS Fases FROM (SELECT mNodos.Geoname, CONVERT(SMALLINT, dbo.mLineas.Fases) AS Fases FROM dbo.mLineas INNER JOIN dbo.mNodos ON dbo.mLineas.Desde = dbo.mNodos.Aux UNION SELECT mNodos.Geoname, CONVERT(SMALLINT, dbo.mLineas.Fases) AS Fases FROM dbo.mLineas INNER JOIN	dbo.mNodos ON dbo.mLineas.Hasta = dbo.mNodos.Aux) F GROUP BY F.Geoname) A ON mNodos.Geoname=A.Geoname WHERE mNodos.geoname IN (@desde,@hasta)) B INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'BORRO_LINEA',LEFT(CONVERT(VARCHAR,DESDE) + ';' + CONVERT(VARCHAR,HASTA) + ';' + CONVERT(VARCHAR,ELMT) + ';' + QUIEBRES,255) FROM DELETED WHERE GEONAME = @geoname INSERT INTO Lineas_Borradas SELECT * FROM DELETED WHERE GEONAME = @geoname END FETCH NEXT FROM RS INTO @geoname, @desde, @hasta, @tension END CLOSE RS DEALLOCATE RS END")
            cursor.execute("ALTER TABLE Lineas ENABLE TRIGGER Borro_Lineas")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER TRIGGER [Borro_Lineas] ON [Lineas] AFTER DELETE AS BEGIN SET NOCOUNT ON DECLARE @aux INT DECLARE @geoname INT DECLARE @desde INT DECLARE @hasta INT DECLARE @aux_desde INT DECLARE @aux_hasta INT DECLARE @tension INT DECLARE @cant_lineas_desde INT DECLARE @cant_lineas_hasta INT DECLARE @str_sql NVARCHAR(MAX) DECLARE @linea1 INT DECLARE @linea2 INT DECLARE @linea3 INT DECLARE @linea4 INT DECLARE @linea5 INT DECLARE @linea6 INT DECLARE @linea7 INT DECLARE @linea8 INT DECLARE @linea9 INT DECLARE @linea10 INT DECLARE @linea11 INT DECLARE @linea12 INT DECLARE @linea13 INT DECLARE @linea14 INT DECLARE @linea15 INT DECLARE @linea16 INT DECLARE @linea17 INT DECLARE @linea18 INT DECLARE @linea19 INT DECLARE @linea20 INT DECLARE @linea21 INT DECLARE @linea22 INT DECLARE @linea23 INT DECLARE @linea24 INT DECLARE @linea25 INT DECLARE @linea26 INT DECLARE @linea27 INT DECLARE @linea28 INT DECLARE @linea29 INT DECLARE @linea30 INT DECLARE @linea31 INT DECLARE @linea32 INT DECLARE @i SMALLINT DECLARE @j SMALLINT DECLARE @sql_desde VARCHAR(MAX) DECLARE @sql_hasta VARCHAR(MAX) DECLARE @n SMALLINT DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, desde, hasta, tension FROM DELETED OPEN RS FETCH NEXT FROM RS INTO @geoname, @desde, @hasta, @tension WHILE (@@FETCH_STATUS = 0) BEGIN IF @tension>0 BEGIN select @aux = aux FROM mLineas WHERE Geoname = @geoname select @aux_desde=aux,@cant_lineas_desde=cant_lineas,@linea1=linea1,@linea2=linea2,@linea3=linea3,@linea4=linea4,@linea5=linea5,@linea6=linea6,@linea7=linea7,@linea8=linea8,@linea9=linea9,@linea10=linea10,@linea11=linea11,@linea12=linea12,@linea13=linea13,@linea14=linea14,@linea15=linea15,@linea16=linea16,@linea17=linea17,@linea18=linea18,@linea19=linea19,@linea20=linea20,@linea21=linea21,@linea22=linea22,@linea23=linea23,@linea24=linea24,@linea25=linea25,@linea26=linea26,@linea27=linea27,@linea28=linea28,@linea29=linea29,@linea30=linea30,@linea31=linea31,@linea32=linea32 FROM mNodos WHERE Geoname = @desde SET @i=0 IF @linea1=@aux BEGIN SET @i=1 END IF @linea2=@aux BEGIN SET @i=2 END IF @linea3=@aux BEGIN SET @i=3 END IF @linea4=@aux BEGIN SET @i=4 END IF @linea5=@aux BEGIN SET @i=5 END IF @linea6=@aux BEGIN SET @i=6 END IF @linea7=@aux BEGIN SET @i=7 END IF @linea8=@aux BEGIN SET @i=8 END IF @linea9=@aux BEGIN SET @i=9 END IF @linea10=@aux BEGIN SET @i=10 END IF @linea11=@aux BEGIN SET @i=11 END IF @linea12=@aux BEGIN SET @i=12 END IF @linea13=@aux BEGIN SET @i=13 END IF @linea14=@aux BEGIN SET @i=14 END IF @linea15=@aux BEGIN SET @i=15 END IF @linea16=@aux BEGIN SET @i=16 END IF @linea17=@aux BEGIN SET @i=17 END IF @linea18=@aux BEGIN SET @i=18 END IF @linea19=@aux BEGIN SET @i=19 END IF @linea20=@aux BEGIN SET @i=20 END IF @linea21=@aux BEGIN SET @i=21 END IF @linea22=@aux BEGIN SET @i=22 END IF @linea23=@aux BEGIN SET @i=23 END IF @linea24=@aux BEGIN SET @i=24 END IF @linea25=@aux BEGIN SET @i=25 END IF @linea26=@aux BEGIN SET @i=26 END IF @linea27=@aux BEGIN SET @i=27 END IF @linea28=@aux BEGIN SET @i=28 END IF @linea29=@aux BEGIN SET @i=29 END IF @linea30=@aux BEGIN SET @i=30 END IF @linea31=@aux BEGIN SET @i=31 END IF @linea32=@aux BEGIN SET @i=32 END SET @sql_desde='' SET @n=@i IF @n=0 BEGIN SET @n=1 END WHILE @n < 32 BEGIN SET @sql_desde=@sql_desde + ',linea' + CAST(@n AS VARCHAR) + '=linea' + CAST(@n+1 AS VARCHAR) SET @n = @n + 1 END SET @sql_desde=@sql_desde + ',linea32=0' select @aux_hasta=aux,@cant_lineas_hasta=cant_lineas,@linea1=linea1,@linea2=linea2,@linea3=linea3,@linea4=linea4,@linea5=linea5,@linea6=linea6,@linea7=linea7,@linea8=linea8,@linea9=linea9,@linea10=linea10,@linea11=linea11,@linea12=linea12,@linea13=linea13,@linea14=linea14,@linea15=linea15,@linea16=linea16,@linea17=linea17,@linea18=linea18,@linea19=linea19,@linea20=linea20,@linea21=linea21,@linea22=linea22,@linea23=linea23,@linea24=linea24,@linea25=linea25,@linea26=linea26,@linea27=linea27,@linea28=linea28,@linea29=linea29,@linea30=linea30,@linea31=linea31,@linea32=linea32 FROM mNodos WHERE Geoname = @hasta SET @j=0 IF @linea1=@aux BEGIN SET @j=1 END IF @linea2=@aux BEGIN SET @j=2 END IF @linea3=@aux BEGIN SET @j=3 END IF @linea4=@aux BEGIN SET @j=4 END IF @linea5=@aux BEGIN SET @j=5 END IF @linea6=@aux BEGIN SET @j=6 END IF @linea7=@aux BEGIN SET @j=7 END IF @linea8=@aux BEGIN SET @j=8 END IF @linea9=@aux BEGIN SET @j=9 END IF @linea10=@aux BEGIN SET @j=10 END IF @linea11=@aux BEGIN SET @j=11 END IF @linea12=@aux BEGIN SET @j=12 END IF @linea13=@aux BEGIN SET @j=13 END IF @linea14=@aux BEGIN SET @j=14 END IF @linea15=@aux BEGIN SET @j=15 END IF @linea16=@aux BEGIN SET @j=16 END IF @linea17=@aux BEGIN SET @j=17 END IF @linea18=@aux BEGIN SET @j=18 END IF @linea19=@aux BEGIN SET @j=19 END IF @linea20=@aux BEGIN SET @j=20 END IF @linea21=@aux BEGIN SET @j=21 END IF @linea22=@aux BEGIN SET @j=22 END IF @linea23=@aux BEGIN SET @j=23 END IF @linea24=@aux BEGIN SET @j=24 END IF @linea25=@aux BEGIN SET @j=25 END IF @linea26=@aux BEGIN SET @j=26 END IF @linea27=@aux BEGIN SET @j=27 END IF @linea28=@aux BEGIN SET @j=28 END IF @linea29=@aux BEGIN SET @j=29 END IF @linea30=@aux BEGIN SET @j=30 END IF @linea31=@aux BEGIN SET @j=31 END IF @linea32=@aux BEGIN SET @j=32 END SET @sql_hasta='' SET @n=@j IF @n=0 BEGIN SET @n=1 END WHILE @n < 32 BEGIN SET @sql_hasta=@sql_hasta + ',linea' + CAST(@n AS VARCHAR) + '=linea' + CAST(@n+1 AS VARCHAR) SET @n = @n + 1 END SET @sql_hasta=@sql_hasta + ',linea32=0' UPDATE mLineas SET geoname=0,desde=0,hasta=0,fuente=0,tension=0,fases=0 WHERE geoname = @geoname SET @str_sql = 'UPDATE mNodos SET cant_lineas = ' + CAST(@cant_lineas_desde - 1 AS VARCHAR) + @sql_desde + ' WHERE geoname =' + CAST(@desde AS VARCHAR) EXEC sp_executesql @str_sql SET @str_sql = 'UPDATE mNodos SET cant_lineas = ' + CAST(@cant_lineas_hasta - 1 AS VARCHAR) + @sql_hasta + ' WHERE geoname =' + CAST(@hasta AS VARCHAR) EXEC sp_executesql @str_sql UPDATE B SET d=o FROM (SELECT mNodos.Fases AS d, A.Fases AS o FROM mNodos INNER JOIN (SELECT F.Geoname, MAX(F.Fases) AS Fases FROM (SELECT mNodos.Geoname, CONVERT(SMALLINT, dbo.mLineas.Fases) AS Fases FROM dbo.mLineas INNER JOIN dbo.mNodos ON dbo.mLineas.Desde = dbo.mNodos.Aux UNION SELECT mNodos.Geoname, CONVERT(SMALLINT, dbo.mLineas.Fases) AS Fases FROM dbo.mLineas INNER JOIN	dbo.mNodos ON dbo.mLineas.Hasta = dbo.mNodos.Aux) F GROUP BY F.Geoname) A ON mNodos.Geoname=A.Geoname WHERE mNodos.geoname IN (@desde,@hasta)) B INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'BORRO_LINEA',LEFT(CONVERT(VARCHAR,DESDE) + ';' + CONVERT(VARCHAR,HASTA) + ';' + CONVERT(VARCHAR,ELMT) + ';' + QUIEBRES,255) FROM DELETED WHERE GEONAME = @geoname INSERT INTO Lineas_Borradas SELECT * FROM DELETED WHERE GEONAME = @geoname END FETCH NEXT FROM RS INTO @geoname, @desde, @hasta, @tension END CLOSE RS DEALLOCATE RS END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE TRIGGER [Creo_Lineas] ON [Lineas] AFTER INSERT AS BEGIN SET NOCOUNT ON DECLARE @aux INT DECLARE @geoname INT DECLARE @fases SMALLINT DECLARE @fases_desde SMALLINT DECLARE @fases_hasta SMALLINT DECLARE @desde INT DECLARE @hasta INT DECLARE @aux_desde INT DECLARE @aux_hasta INT DECLARE @cant_lineas_desde INT DECLARE @cant_lineas_hasta INT DECLARE @tension INT DECLARE @flag_nuevo_aux TINYINT DECLARE @str_sql NVARCHAR(MAX) DECLARE @obj GEOMETRY SELECT @geoname = geoname, @fases = fase, @desde = desde, @hasta = hasta, @tension = tension, @obj=obj FROM INSERTED IF @tension>0 BEGIN IF NOT (SELECT TOP 1 geoname FROM Lineas WHERE (desde=@desde AND hasta=@hasta OR desde=@hasta and hasta=@desde) AND geoname<>@geoname) IS NULL BEGIN RAISERROR ('Ya existe una linea entre esos dos nodos', 16, 1) END ELSE BEGIN SELECT @aux = MAX(aux) FROM mLineas WHERE geoname=0 SET @flag_nuevo_aux=0 IF @aux=0 BEGIN SELECT @aux = COUNT(*) FROM mLineas SET @flag_nuevo_aux=1 END select @aux_desde = aux, @cant_lineas_desde = cant_lineas + 1, @fases_desde=fases FROM mNodos WHERE Geoname = @desde select @aux_hasta = aux, @cant_lineas_hasta = cant_lineas + 1, @fases_hasta=fases FROM mNodos WHERE Geoname = @hasta IF @flag_nuevo_aux=0 BEGIN UPDATE mLineas SET geoname=@geoname,desde=@aux_desde,hasta=@aux_hasta,fuente=0,tension=@tension,fases=@fases WHERE aux=@aux END IF @flag_nuevo_aux=1 BEGIN INSERT INTO mLineas (aux,geoname,desde,hasta,fuente,tension,fases,aux2,aux3,aux4,aux5,aux6,aux7) VALUES (@aux,@geoname,@aux_desde,@aux_hasta,0,@tension,@fases,0,0,0,0,0,0) END SET @fases = dbo.MAXIMO(@fases,@fases_desde) SET @fases = dbo.MAXIMO(@fases,@fases_hasta) SET @str_sql = 'UPDATE mNodos SET cant_lineas = ' + CAST(@cant_lineas_desde AS VARCHAR) + ', linea' + CAST(@cant_lineas_desde AS VARCHAR) + '=' + CAST(@aux AS VARCHAR) + ', fases = ' + CAST(@fases AS VARCHAR) + ' WHERE geoname =' + CAST(@desde AS VARCHAR) EXEC sp_executesql @str_sql SET @str_sql = 'UPDATE mNodos SET cant_lineas = ' + CAST(@cant_lineas_hasta AS VARCHAR) + ', linea' + CAST(@cant_lineas_hasta AS VARCHAR) + '=' + CAST(@aux AS VARCHAR) + ', fases = ' + CAST(@fases AS VARCHAR) + ' WHERE geoname =' + CAST(@hasta AS VARCHAR) EXEC sp_executesql @str_sql DECLARE @quiebres VARCHAR(255) DECLARE @SRID SMALLINT DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(6,2) DECLARE @ddy DECIMAL(6,2) SELECT geoname, obj FROM INSERTED SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @xant = @X SET @yant = @Y SET @str_quiebres = '' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END UPDATE Lineas SET quiebres=@str_quiebres WHERE Geoname = @geoname INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT @geoname, GETDATE(),'ACTUALIZO_LINEA', @quiebres FROM INSERTED END END END")
            cursor.execute("ALTER TABLE Lineas ENABLE TRIGGER Creo_Lineas")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER TRIGGER [Creo_Lineas] ON [Lineas] AFTER INSERT AS BEGIN SET NOCOUNT ON DECLARE @aux INT DECLARE @geoname INT DECLARE @fases SMALLINT DECLARE @fases_desde SMALLINT DECLARE @fases_hasta SMALLINT DECLARE @desde INT DECLARE @hasta INT DECLARE @aux_desde INT DECLARE @aux_hasta INT DECLARE @cant_lineas_desde INT DECLARE @cant_lineas_hasta INT DECLARE @tension INT DECLARE @flag_nuevo_aux TINYINT DECLARE @str_sql NVARCHAR(MAX) DECLARE @obj GEOMETRY SELECT @geoname = geoname, @fases = fase, @desde = desde, @hasta = hasta, @tension = tension, @obj=obj FROM INSERTED IF @tension>0 BEGIN IF NOT (SELECT TOP 1 geoname FROM Lineas WHERE (desde=@desde AND hasta=@hasta OR desde=@hasta and hasta=@desde) AND geoname<>@geoname) IS NULL BEGIN RAISERROR ('Ya existe una linea entre esos dos nodos', 16, 1) END ELSE BEGIN SELECT @aux = MAX(aux) FROM mLineas WHERE geoname=0 SET @flag_nuevo_aux=0 IF @aux=0 BEGIN SELECT @aux = COUNT(*) FROM mLineas SET @flag_nuevo_aux=1 END select @aux_desde = aux, @cant_lineas_desde = cant_lineas + 1, @fases_desde=fases FROM mNodos WHERE Geoname = @desde select @aux_hasta = aux, @cant_lineas_hasta = cant_lineas + 1, @fases_hasta=fases FROM mNodos WHERE Geoname = @hasta IF @flag_nuevo_aux=0 BEGIN UPDATE mLineas SET geoname=@geoname,desde=@aux_desde,hasta=@aux_hasta,fuente=0,tension=@tension,fases=@fases WHERE aux=@aux END IF @flag_nuevo_aux=1 BEGIN INSERT INTO mLineas (aux,geoname,desde,hasta,fuente,tension,fases,aux2,aux3,aux4,aux5,aux6,aux7) VALUES (@aux,@geoname,@aux_desde,@aux_hasta,0,@tension,@fases,0,0,0,0,0,0) END SET @fases = dbo.MAXIMO(@fases,@fases_desde) SET @fases = dbo.MAXIMO(@fases,@fases_hasta) SET @str_sql = 'UPDATE mNodos SET cant_lineas = ' + CAST(@cant_lineas_desde AS VARCHAR) + ', linea' + CAST(@cant_lineas_desde AS VARCHAR) + '=' + CAST(@aux AS VARCHAR) + ', fases = ' + CAST(@fases AS VARCHAR) + ' WHERE geoname =' + CAST(@desde AS VARCHAR) EXEC sp_executesql @str_sql SET @str_sql = 'UPDATE mNodos SET cant_lineas = ' + CAST(@cant_lineas_hasta AS VARCHAR) + ', linea' + CAST(@cant_lineas_hasta AS VARCHAR) + '=' + CAST(@aux AS VARCHAR) + ', fases = ' + CAST(@fases AS VARCHAR) + ' WHERE geoname =' + CAST(@hasta AS VARCHAR) EXEC sp_executesql @str_sql DECLARE @quiebres VARCHAR(255) DECLARE @SRID SMALLINT DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(6,2) DECLARE @ddy DECIMAL(6,2) SELECT geoname, obj FROM INSERTED SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @xant = @X SET @yant = @Y SET @str_quiebres = '' set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END UPDATE Lineas SET quiebres=@str_quiebres WHERE Geoname = @geoname INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT @geoname, GETDATE(),'ACTUALIZO_LINEA', @quiebres FROM INSERTED END END END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE TRIGGER Actualizo_Postes ON Postes AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname WHILE (@@FETCH_STATUS = 0) BEGIN EXEC dbo.Normalizar_Poste @geoname, @SRID FETCH NEXT FROM RS INTO @geoname END CLOSE RS DEALLOCATE RS INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'ACTUALIZO_POSTE',(CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),XCOORD)) +';'+ CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),YCOORD))) FROM INSERTED END END")
            cursor.execute("ALTER TABLE Postes ENABLE TRIGGER Actualizo_Postes")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER TRIGGER Actualizo_Postes ON Postes AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname WHILE (@@FETCH_STATUS = 0) BEGIN EXEC dbo.Normalizar_Poste @geoname, @SRID FETCH NEXT FROM RS INTO @geoname END CLOSE RS DEALLOCATE RS INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'ACTUALIZO_POSTE',(CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),XCOORD)) +';'+ CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),YCOORD))) FROM INSERTED END END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE TRIGGER Borro_Postes ON Postes AFTER DELETE AS BEGIN SET NOCOUNT ON INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'BORRO_POSTE',(CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),XCOORD)) +';'+ CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),YCOORD))) FROM DELETED END")
            cursor.execute("ALTER TABLE Postes ENABLE TRIGGER Borro_Postes")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER TRIGGER Borro_Postes ON Postes AFTER DELETE AS BEGIN SET NOCOUNT ON INSERT INTO LOGS (GEONAME, FECHA, TIPO, VALOR) SELECT GEONAME, GETDATE(),'BORRO_POSTE',(CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),XCOORD)) +';'+ CONVERT(VARCHAR,CONVERT(DECIMAL(9,2),YCOORD))) FROM DELETED END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE TRIGGER Actualizo_Areas ON Areas AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @Xc DECIMAL(9,2) DECLARE @Yc DECIMAL(9,2) DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(9,2) DECLARE @ddy DECIMAL(9,2) DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @Xc = @obj.STCentroid().STX SET @Yc = @obj.STCentroid().STY SET @xant = @Xc SET @yant = @Yc SET @str_quiebres = '' SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) UPDATE Areas SET xcoord=@Xc, ycoord=@Yc, quiebres=@str_quiebres WHERE Geoname = @geoname FETCH NEXT FROM RS INTO @geoname, @obj END CLOSE RS DEALLOCATE RS END END")
            cursor.execute("ALTER TABLE Areas ENABLE TRIGGER Actualizo_Areas")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER TRIGGER Actualizo_Areas ON Areas AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @Xc DECIMAL(9,2) DECLARE @Yc DECIMAL(9,2) DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(9,2) DECLARE @ddy DECIMAL(9,2) DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @Xc = @obj.STCentroid().STX SET @Yc = @obj.STCentroid().STY SET @xant = @Xc SET @yant = @Yc SET @str_quiebres = '' SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) UPDATE Areas SET xcoord=@Xc, ycoord=@Yc, quiebres=@str_quiebres WHERE Geoname = @geoname FETCH NEXT FROM RS INTO @geoname, @obj END CLOSE RS DEALLOCATE RS END END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE TRIGGER Creo_Areas ON  Areas AFTER INSERT AS BEGIN SET NOCOUNT ON DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @Xc DECIMAL(9,2) DECLARE @Yc DECIMAL(9,2) DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(9,2) DECLARE @ddy DECIMAL(9,2) DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @geoname=geoname, @obj=obj FROM INSERTED SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @Xc = @obj.STCentroid().STX SET @Yc = @obj.STCentroid().STY SET @xant = @Xc SET @yant = @Yc SET @str_quiebres = '' SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) UPDATE Areas SET xcoord=@Xc, ycoord=@Yc, quiebres=@str_quiebres WHERE Geoname = @geoname END")
            cursor.execute("ALTER TABLE Areas ENABLE TRIGGER Creo_Areas")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER TRIGGER Creo_Areas ON  Areas AFTER INSERT AS BEGIN SET NOCOUNT ON DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @Xc DECIMAL(9,2) DECLARE @Yc DECIMAL(9,2) DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(9,2) DECLARE @ddy DECIMAL(9,2) DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @geoname=geoname, @obj=obj FROM INSERTED SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @Xc = @obj.STCentroid().STX SET @Yc = @obj.STCentroid().STY SET @xant = @Xc SET @yant = @Yc SET @str_quiebres = '' SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) UPDATE Areas SET xcoord=@Xc, ycoord=@Yc, quiebres=@str_quiebres WHERE Geoname = @geoname END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE TRIGGER Actualizo_Parcelas ON Parcelas AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @Xc DECIMAL(9,2) DECLARE @Yc DECIMAL(9,2) DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(9,2) DECLARE @ddy DECIMAL(9,2) DECLARE @SRID SMALLINT 	 SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @Xc = @obj.STCentroid().STX SET @Yc = @obj.STCentroid().STY SET @xant = @Xc SET @yant = @Yc SET @str_quiebres = '' SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) UPDATE Parcelas SET xcoord=@Xc, ycoord=@Yc, quiebres=@str_quiebres WHERE Geoname = @geoname FETCH NEXT FROM RS INTO @geoname, @obj END CLOSE RS DEALLOCATE RS END END")
            cursor.execute("ALTER TABLE Parcelas ENABLE TRIGGER Actualizo_Parcelas")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER TRIGGER Actualizo_Parcelas ON Parcelas AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @Xc DECIMAL(9,2) DECLARE @Yc DECIMAL(9,2) DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(9,2) DECLARE @ddy DECIMAL(9,2) DECLARE @SRID SMALLINT 	 SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @Xc = @obj.STCentroid().STX SET @Yc = @obj.STCentroid().STY SET @xant = @Xc SET @yant = @Yc SET @str_quiebres = '' SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) UPDATE Parcelas SET xcoord=@Xc, ycoord=@Yc, quiebres=@str_quiebres WHERE Geoname = @geoname FETCH NEXT FROM RS INTO @geoname, @obj END CLOSE RS DEALLOCATE RS END END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE TRIGGER Creo_Parcelas ON  Parcelas AFTER INSERT AS BEGIN SET NOCOUNT ON DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @Xc DECIMAL(9,2) DECLARE @Yc DECIMAL(9,2) DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(9,2) DECLARE @ddy DECIMAL(9,2) DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @geoname=geoname, @obj=obj FROM INSERTED SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @Xc = @obj.STCentroid().STX SET @Yc = @obj.STCentroid().STY SET @xant = @Xc SET @yant = @Yc SET @str_quiebres = '' SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) UPDATE Parcelas SET xcoord=@Xc, ycoord=@Yc, quiebres=@str_quiebres WHERE Geoname = @geoname END")
            cursor.execute("ALTER TABLE Parcelas ENABLE TRIGGER Creo_Parcelas")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER TRIGGER Creo_Parcelas ON  Parcelas AFTER INSERT AS BEGIN SET NOCOUNT ON DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @str_obj VARCHAR(MAX) DECLARE @str_quiebres VARCHAR(MAX) DECLARE @X DECIMAL(9,2) DECLARE @Y DECIMAL(9,2) DECLARE @str_par VARCHAR(MAX) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @Xc DECIMAL(9,2) DECLARE @Yc DECIMAL(9,2) DECLARE @xant DECIMAL(9,2) DECLARE @yant DECIMAL(9,2) DECLARE @ddx DECIMAL(9,2) DECLARE @ddy DECIMAL(9,2) DECLARE @SRID SMALLINT SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' SELECT @geoname=geoname, @obj=obj FROM INSERTED SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SET @Xc = @obj.STCentroid().STX SET @Yc = @obj.STCentroid().STY SET @xant = @Xc SET @yant = @Yc SET @str_quiebres = '' SET @str_obj = REPLACE(@str_obj, 'POLYGON ((', '') SET @str_obj = REPLACE(@str_obj, '))', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y SET @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) WHILE @i<>0 BEGIN SET @str_par = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) set @str_obj = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_par)-2) SELECT @i = CHARINDEX(',', @str_obj) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) SET @xant = @X SET @yant = @Y END SET @str_par=@str_obj SELECT @k = CHARINDEX(' ', @str_par) SET @X = CAST(LEFT(@str_par, @k-1) AS decimal(9,2)) SET @Y = CAST(RIGHT(@str_par, LEN(@str_par)-@k) AS decimal(9,2)) SET @ddx = @X-@xant SET @ddy = @Y-@yant SET @str_quiebres = @str_quiebres + ';' + CAST(@ddx AS varchar) + ';' + CAST(@ddy AS varchar) UPDATE Parcelas SET xcoord=@Xc, ycoord=@Yc, quiebres=@str_quiebres WHERE Geoname = @geoname END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("CREATE TRIGGER Actualizo_Ejes ON Ejes AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @SRID SMALLINT DECLARE @str_obj VARCHAR(MAX) DECLARE @str_izquierda VARCHAR(50) DECLARE @str_derecha VARCHAR(50) DECLARE @X1 DECIMAL(9,2) DECLARE @Y1 DECIMAL(9,2) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @X2 DECIMAL(9,2) DECLARE @Y2 DECIMAL(9,2) SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_izquierda = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_izquierda) SET @X1 = CAST(LEFT(@str_izquierda, @k-1) AS decimal(9,2)) SET @Y1 = CAST(RIGHT(@str_izquierda, LEN(@str_izquierda)-@k) AS decimal(9,2)) set @str_derecha = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_izquierda)-2) SELECT @k = CHARINDEX(' ', @str_obj) SET @X2 = CAST(LEFT(@str_derecha, @k-1) AS decimal(9,2)) SET @Y2 = CAST(RIGHT(@str_derecha, LEN(@str_derecha)-@k) AS decimal(9,2)) UPDATE Ejes SET X1=@X1, y1=@y1, X2=@X2, Y2=@Y2 WHERE Geoname = @geoname FETCH NEXT FROM RS INTO @geoname, @obj END CLOSE RS DEALLOCATE RS END END")
            cursor.execute("ALTER TABLE Ejes ENABLE TRIGGER Actualizo_Ejes")
            cnn.commit()
        except:
            cnn.rollback()
            try:
                cursor.execute("ALTER CREATE TRIGGER Actualizo_Ejes ON Ejes AFTER UPDATE AS BEGIN SET NOCOUNT ON IF UPDATE(obj) BEGIN DECLARE @geoname INT DECLARE @obj GEOMETRY DECLARE @SRID SMALLINT DECLARE @str_obj VARCHAR(MAX) DECLARE @str_izquierda VARCHAR(50) DECLARE @str_derecha VARCHAR(50) DECLARE @X1 DECIMAL(9,2) DECLARE @Y1 DECIMAL(9,2) DECLARE @i SMALLINT DECLARE @k SMALLINT DECLARE @X2 DECIMAL(9,2) DECLARE @Y2 DECIMAL(9,2) SELECT @SRID = Valor FROM Configuracion WHERE Variable = 'SRID' DECLARE RS CURSOR STATIC LOCAL FORWARD_ONLY FOR SELECT geoname, obj FROM INSERTED OPEN RS FETCH NEXT FROM RS INTO @geoname, @obj WHILE (@@FETCH_STATUS = 0) BEGIN SET @str_obj = @obj.ToString() SET @str_obj = REPLACE(@str_obj, 'LINESTRING (', '') SET @str_obj = REPLACE(@str_obj, ')', '') SELECT @i = CHARINDEX(',', @str_obj) SET @str_izquierda = LEFT(@str_obj, @i-1) SELECT @k = CHARINDEX(' ', @str_izquierda) SET @X1 = CAST(LEFT(@str_izquierda, @k-1) AS decimal(9,2)) SET @Y1 = CAST(RIGHT(@str_izquierda, LEN(@str_izquierda)-@k) AS decimal(9,2)) set @str_derecha = RIGHT(@str_obj, LEN(@str_obj)-LEN(@str_izquierda)-2) SELECT @k = CHARINDEX(' ', @str_obj) SET @X2 = CAST(LEFT(@str_derecha, @k-1) AS decimal(9,2)) SET @Y2 = CAST(RIGHT(@str_derecha, LEN(@str_derecha)-@k) AS decimal(9,2)) UPDATE Ejes SET X1=@X1, y1=@y1, X2=@X2, Y2=@Y2 WHERE Geoname = @geoname FETCH NEXT FROM RS INTO @geoname, @obj END CLOSE RS DEALLOCATE RS END END")
                cnn.commit()
            except:
                cnn.rollback()
        try:
            cursor.execute("UPDATE Configuracion SET Valor='" + self.version + "' WHERE Variable='Version'")
            cnn.commit()
            QMessageBox.information(None, 'EnerGis 5', "Se actualizó la DB a la versión " + self.version)
        except:
            cnn.rollback()

    def crear_red(self):
        cnn = self.conn
        cursor = cnn.cursor()
        try:
            cursor.execute("crear_red")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.information(None, 'EnerGis 5', "No se pudo crear la Red !")

    def red_a_estado_normal(self):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE nodos SET estado=elmt WHERE (elmt=2 OR elmt=3) AND estado<>elmt")
        self.conn.commit()
        self.crear_red
        QMessageBox.information(None, 'EnerGis 5', "Red en Estado Normal")

    def establecer_estado_normal(self):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE nodos SET elmt=estado WHERE (elmt=2 OR elmt=3) AND estado<>elmt")
        self.conn.commit()
        QMessageBox.information(None, 'EnerGis 5', "Se estableció la Configuración de Red como Estado Normal")

    def exportar_shp(self):
        if os.path.isdir('c:/gis/energis5/QField/')==False:
            os.mkdir('c:/gis/energis5/QField/')

        mapCanvas = self.iface.mapCanvas()
        n = mapCanvas.layerCount()
        layers = [mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Temp':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/QField/" + lyr.name() + ".shp", "", lyr.crs(), "ESRI Shapefile")
            if lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Temp':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/QField/" + lyr.name() + ".shp", "", lyr.crs(), "ESRI Shapefile")
            if lyr.name()[:6] == 'Postes':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/QField/" + lyr.name() + ".shp", "", lyr.crs(), "ESRI Shapefile")
        QMessageBox.information(None, 'EnerGis 5', "Exportado")

    def exportar_tab(self):
        if os.path.isdir('c:/gis/energis5/MapInfo/')==False:
            os.mkdir('c:/gis/energis5/MapInfo/')

        mapCanvas = self.iface.mapCanvas()
        n = mapCanvas.layerCount()
        layers = [mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Temp':
                #QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/MapInfo/" + self.nombre_modelo.lower() + lyr.name().replace('Nodos ','_no_') + ".tab", "", lyr.crs(), "MapInfo File", symbologyExport=QgsVectorFileWriter.FeatureSymbology)
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/MapInfo/" + self.nombre_modelo + ' ' + lyr.name() + ".tab", "", lyr.crs(), "MapInfo File")
            if lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Temp':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/MapInfo/" + self.nombre_modelo + ' ' + lyr.name() + ".tab", "", lyr.crs(), "MapInfo File")
            if lyr.name()[:6] == 'Postes':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis5/MapInfo/" + self.nombre_modelo + ' ' + lyr.name() + ".tab", "", lyr.crs(), "MapInfo File")
        QMessageBox.information(None, 'EnerGis 5', "Exportado")

    def h_verificar_red(self):
        #QMessageBox.information(None, 'EnerGis 5', 'Inicio')
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
        try:
            cursor.execute("DELETE FROM Alimentadores WHERE Id_Alim NOT IN (SELECT Val1 FROM Nodos WHERE Nodos.Tension>0 AND elmt=8)")
            cursor.execute("INSERT INTO Alimentadores (Id_Alim,Tension,Cd,SSEE) SELECT DISTINCT LEFT(Val1,15) AS Id_Alim, Tension,'0' AS Cd,'0' AS SSEE FROM Nodos WHERE Nodos.Tension>0 AND elmt=8 AND LEFT(Val1,15) NOT IN (SELECT Id_Alim FROM Alimentadores)")
            cursor.execute("UPDATE Alimentadores SET ssee='0' WHERE ssee IS NULL")
            cursor.execute("UPDATE Alimentadores SET cd='0' WHERE cd IS NULL")
            cursor.commit()
        except:
            cursor.rollback()
            QMessageBox.information(None, 'EnerGis 5', "No se pudieron actualizar Alimentadores !")

        for fuente in fuentes:
            #QMessageBox.information(None, 'Navego Fuente', str(fuente[0]))
            r = navegar_compilar_red(self, self.mnodos, self.mlineas, self.monodos, fuente[0])
            if str(r) != 'Red Navegada':
                QMessageBox.information(None, 'EnerGis 5', str(r))
                return

        cursor = self.conn.cursor()
        cursor.execute("SELECT count(*) FROM mNodos WHERE geoname<>0 AND tension>0 AND cant_lineas=0")
        aislados = cursor.fetchall()
        cursor.close()
        nodos_aislados=aislados[0][0]

        self.seleccion_n = []
        for m in range(1, len(self.mnodos)):
            if self.mnodos[m][3] == 0 and self.mnodos[m][1] != 0 and self.mnodos[m][38] > 0:
                self.seleccion_n.append(self.mnodos[m][1])
        nodos_desconectados=len(self.seleccion_n)

        self.seleccion_l = []
        for n in range (1, len(self.mlineas)):
            if self.mlineas[n][4] == 0 and self.mlineas[n][1] != 0 and self.mlineas[n][5] > 0:
                self.seleccion_l.append(self.mlineas[n][1])
        lineas_desconectadas=len(self.seleccion_l)

        #self.mnodos_secc=deepcopy(self.mnodos)
        #self.mlineas_secc=deepcopy(self.mlineas)
        #nodos_por_seccionador(self, self.conn, self.mnodos_secc, self.mlineas_secc)

        self.mnodos_sal=deepcopy(self.mnodos)
        self.mlineas_sal=deepcopy(self.mlineas)
        nodos_por_salida(self, self.conn, self.mnodos_sal, self.mlineas_sal)

        #Verificar Red
        str_sql= "SELECT DISTINCT 'Lineas' AS Elemento,'lineas con iguales nodo desde/hasta' AS Problema,Max(A.Geoname) AS Geoname,'Linea' AS Nombre FROM (SELECT Geoname,Desde,Hasta FROM Lineas WHERE Lineas.Tension>0 UNION SELECT Geoname,Hasta,Desde FROM Lineas WHERE Lineas.Tension>0) AS A GROUP BY A.Desde, A.Hasta HAVING Count(A.Geoname)>1"
        str_sql= str_sql + " UNION SELECT 'Lineas' AS Elemento,'lineas con longitud menor a cero' AS Problema,Geoname,'Linea' AS Nombre FROM Lineas WHERE Lineas.Tension>0 AND Lineas.Tension>0 AND Longitud<=0"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores sin nombre' AS Problema,Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND (Elmt = 2 OR Elmt = 3) AND ((Nombre) Is null OR Nombre = '')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores con nombre repetido' AS Problema,Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND Nodos.Tension>0 AND (Elmt = 2 OR Elmt = 3) GROUP BY Geoname, Nombre HAVING Count(Nodos.Geoname)>1"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'CTs con nombre repetido' AS Problema,Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND Elmt = 4 GROUP BY Geoname, Nombre HAVING Count(Nodos.Geoname)>1"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'salidas de alimentador sin código de alimentador' AS Problema,Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND Elmt = 8 AND ((Val1) Is null OR Val1 = '')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'fuentes con errores de tensión' AS Problema,Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND Elmt = 1 AND Val1 IS NULL"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'fuentes con mas de una línea' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND Nodos.estado=1 AND cant_lineas>1"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores con mas de dos líneas' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND (Nodos.estado=2 OR Nodos.estado=3) AND cant_lineas>2"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'CTs con mas de dos líneas' AS Problema,Nodos.Geoname, Nodos.Nombre as Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND Nodos.estado=4 AND cant_lineas>2"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'CTs con usuarios y sin máquina' AS Problema,Nodos.Geoname, Nodos.Nombre FROM (Nodos INNER JOIN ((Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s) ON Nodos.Geoname = Suministros_Trafos.Geoname_t) LEFT JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct WHERE Nodos.Tension>0 AND Nodos.elmt = 4 AND Usuarios.[ES] = 1 AND Transformadores.Id_trafo Is Null GROUP BY Nodos.Geoname, Nodos.Nombre HAVING Count(Usuarios.id_usuario)>0"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'transformadores con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Transformadores INNER JOIN Nodos ON Transformadores.Id_ct = Nodos.Nombre INNER JOIN mNodos ON Nodos.Geoname = mNodos.Geoname WHERE ((mNodos.fases IN (1,2,3) AND Transformadores.Conexionado <> 'M') OR (mNodos.fases IN ('12','23','13') AND Transformadores.Conexionado NOT IN ('M','B'))) AND Nodos.Elmt=4 GROUP BY nodos.Geoname, nodos.Nombre"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'usuarios con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo WHERE Nodos.Tension>0 AND Usuarios.fase='123' GROUP BY nodos.Geoname, nodos.Nombre HAVING MIN(fase) IN ('1','2','3','12','23','13')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'nodos con inconsistencias de tarifas' AS Problema,A.Geoname, A.Nombre FROM (SELECT Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro GROUP BY Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension) AS A GROUP BY A.Geoname, A.Nombre HAVING Count(A.Nivel_Tension)>1"
        str_sql= str_sql + " UNION SELECT DISTINCT 'Nodos' AS Elemento,'nodos con inconsistencias de tarifas' AS Problema,Nodos.Geoname, Usuarios.tarifa AS Nombre FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE (((Nodos.Tension)>1000) AND ((Tarifas.Nivel_Tension)='BT')) OR (((Nodos.Tension)<1000) AND ((Tarifas.Nivel_Tension)='MT'))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'usuarios con tarifas erroneas' AS Problema,Nodos.Geoname, CAST(Usuarios.id_usuario AS varchar) + '->'+ Usuarios.Tarifa AS Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo WHERE Nodos.Tension>0 AND (((Usuarios.[ES])=1) AND ((Usuarios.tarifa) Is Null)) OR (((Usuarios.tarifa) Not In (select tarifa FROM tarifas)))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'alimentadores sin nombre' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos WHERE Nodos.Tension>0 AND Elmt = 8 AND (Val1='' OR Val1 IS NULL)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'cambios de tension sin trafos' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta WHERE (Nodos.Tension>0 AND Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Tension>0 AND Nodos.Elmt=5 AND Lineas.Tension>0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'cambios de tension sin trafos' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE (Nodos.Tension>0 AND Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Tension>0 AND Nodos.Elmt=5 AND Lineas.Tension>0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'nodos con inconsistencia de fases' AS Problema,nodos.geoname, Nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta INNER JOIN mNodos ON Nodos.Geoname = mNodos.geoname WHERE Nodos.Tension>0 AND (LEN(mNodos.fases)<>LEN(Lineas.Fase) AND mNodos.fases<>Lineas.Fase AND mNodos.fases<>123 AND Lineas.Fase<>123) AND (LEN(mNodos.fases)=2 AND CHARINDEX(Lineas.Fase, mNodos.fases, 0)=0 OR LEN(Lineas.Fase)=2 AND CHARINDEX(CONVERT(VARCHAR,mNodos.Fases), Lineas.fase, 0)=0)"

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

    def h_desconectados(self):
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

        for fuente in fuentes:
            #QMessageBox.information(None, 'Navego Fuente', str(fuente[0]))
            r = navegar_compilar_red(self, self.mnodos, self.mlineas, self.monodos, fuente[0])
            if str(r) != 'Red Navegada':
                QMessageBox.information(None, 'EnerGis 5', str(r))
                return

        self.seleccion_n = []
        for m in range(1, len(self.mnodos)):
            if self.mnodos[m][3] == 0 and self.mnodos[m][1]!=0:
                self.seleccion_n.append(self.mnodos[m][1])
        nodos_desconectados=len(self.seleccion_n)

        self.seleccion_l = []
        for n in range (1, len(self.mlineas)):
            if self.mlineas[n][4] == 0 and self.mlineas[n][1]!=0:
                self.seleccion_l.append(self.mlineas[n][1])
        lineas_desconectadas=len(self.seleccion_l)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText('Análisis de la Red')
        msg.setInformativeText('Desconectados')
        msg.setWindowTitle('EnerGis 5')
        msg.setDetailedText(str(nodos_desconectados) + ' nodos desconectados, ' + str(lineas_desconectadas) + ', lineas desconectadas')
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

    def h_aislados(self):
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

        self.seleccion_n = []

        for n in range (0, len(self.mnodos)):
            if self.mnodos[n][1]!=0 and self.mnodos[n][4] == 0:
                self.seleccion_n.append(self.mnodos[n][1])

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText('Análisis de la Red')
        msg.setInformativeText('Aislados')
        msg.setWindowTitle('EnerGis 5')
        msg.setDetailedText(str(len(self.seleccion_n)) + ' nodos marcados')
        msg.exec_()
        if len(self.seleccion_n)==0:
            return

        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Temp':
                lyr.select(self.seleccion_n)

        self.h_elementos_seleccionados()
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

    def h_buscar_direccion(self):
        from .frm_buscar_direccion import frmBuscarDireccion
        mapCanvas = self.iface.mapCanvas()
        self.dialogo = frmBuscarDireccion(mapCanvas, self.conn)
        self.dialogo.show()
        pass

    def h_usuarios_nuevos(self):
        from .frm_usuarios_nuevos import frmUsuariosNuevos
        mapCanvas = self.iface.mapCanvas()
        self.dialogo = frmUsuariosNuevos(mapCanvas, self.conn)
        self.dialogo.show()
        pass

    def h_electrodependientes(self):
        from qgis.core import QgsVectorLayer, QgsFeature, QgsPoint
        from PyQt5.QtGui import QColor

        b_estado=False

        for action in self.actions:
            if str(action.text())=='Usuarios Electrodependientes':
                b_estado = action.isChecked()

        b_existe = False
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyrCRS = lyr.crs().authid()
            if lyr.name() == 'Electrodependientes':
                b_existe = True
                self.electrodependientes = lyr
                if not self.electrodependientes.isEditable():
                    self.electrodependientes.startEditing()
                    for f in lyr.getFeatures():
                        lyr.deleteFeature(f.id())
                    self.electrodependientes.commitChanges()

        if b_estado==True:

            if b_existe == False:
                self.electrodependientes = QgsVectorLayer("Point?crs=" + lyrCRS, "Electrodependientes", "memory")
                QgsProject.instance().addMapLayer(self.electrodependientes)
                self.electrodependientes.renderer().symbol().setOpacity(1)
                self.electrodependientes.renderer().symbol().symbolLayer(0).setShape(QgsSimpleMarkerSymbolLayerBase.CrossFill)
                self.electrodependientes.renderer().symbol().symbolLayer(0).setSize(4)
                self.electrodependientes.renderer().symbol().symbolLayer(0).setColor(QColor("red"))

            electrodependientes_data = self.electrodependientes.dataProvider()

            cursor = self.conn.cursor()
            cursor.execute("SELECT Usuarios.id_usuario, Usuarios.Nombre, Usuarios.Calle, Usuarios.Altura, Nodos.XCoord, Nodos.YCoord FROM Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE Usuarios.electrodependiente='S'")
            #convierto el cursor en array
            electrodependientes = tuple(cursor)
            cursor.close()

            for e in range (0, len(electrodependientes)):
                pt =  QgsPoint(electrodependientes[e][4],electrodependientes[e][5])
                ftr = QgsFeature()
                ftr.setGeometry(pt)
                electrodependientes_data.addFeatures([ftr])
                self.electrodependientes.triggerRepaint()
        else:
            if b_existe == True:
                QgsProject.instance().removeMapLayer(self.electrodependientes.id())
        pass

    def h_datos_seleccion(self):
        from .frm_datos_seleccion import frmDatosSeleccion
        mapCanvas = self.iface.mapCanvas()
        self.dialogo = frmDatosSeleccion(self.tipo_usuario, mapCanvas, self.conn)
        self.dialogo.show()
        pass

    def h_seleccion(self):
        tool = herrSeleccion(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.iface, self.conn, self.mnodos, self.mlineas, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion.png'))
        seleccion_px.setMask(seleccion_px.mask())
        seleccion_cursor = QtGui.QCursor(seleccion_px)
        self.mapCanvas.setCursor(seleccion_cursor)
        pass

    def h_seleccionar_ejes(self):
        tool = herrSeleccionEjes(self.tipo_usuario, self.iface.mapCanvas(), self.iface, self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion_ejes.png'))
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
        tool = herrNodo(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.mapCanvas.setCursor(curNodo)
        pass
        
    def h_linea(self):
        self.tension = self.cmbTension.currentText()
        #QMessageBox.information(None, 'h_linea', str(tension))
        tool = herrLinea(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.mapCanvas.setCursor(curLinea)
        pass
        
    def h_eje(self):
        tool = herrEje(self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punEje = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punEje.setMask(punEje.mask())
        curEje = QtGui.QCursor(punEje)
        self.mapCanvas.setCursor(curEje)
        pass

    def h_agregar_vertice(self):
        tool = herrAgregarVertice(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.mapCanvas.setCursor(curNodo)
        pass

    def h_quitar_vertice(self):
        tool = herrQuitarVertice(self.iface.mapCanvas(), self.conn)
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
        tool = herrPoste(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punPoste = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punPoste.setMask(punPoste.mask())
        curPoste = QtGui.QCursor(punPoste)
        self.mapCanvas.setCursor(curPoste)
        pass

    def h_mover(self):
        tool = herrMover(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punMover = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_mover.png'))
        punMover.setMask(punMover.mask())
        curMover = QtGui.QCursor(punMover)
        self.mapCanvas.setCursor(curMover)
        pass

    def h_rotar(self):
        tool = herrRotar(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punRotar = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_rotar.png'))
        punRotar.setMask(punRotar.mask())
        curRotar = QtGui.QCursor(punRotar)
        self.mapCanvas.setCursor(curRotar)
        pass

    def h_mover_ejes(self):
        tool = herrMoverEjes(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punMover = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_mover.png'))
        punMover.setMask(punMover.mask())
        curMover = QtGui.QCursor(punMover)
        self.mapCanvas.setCursor(curMover)
        pass

    def h_rotar_ejes(self):
        tool = herrRotarEjes(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punRotar = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_rotar.png'))
        punRotar.setMask(punRotar.mask())
        curRotar = QtGui.QCursor(punRotar)
        self.mapCanvas.setCursor(curRotar)
        pass

    def h_conectar(self):
        tool = herrConectar(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punConectar = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_conectar.png'))
        punConectar.setMask(punConectar.mask())
        curConectar = QtGui.QCursor(punConectar)
        self.mapCanvas.setCursor(curConectar)
        pass
        
    def h_area(self):
        #QMessageBox.information(None, 'h_nodo', str(tension))
        tool = herrArea(self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.mapCanvas.setCursor(curLinea)
        pass

    def h_parcela(self):
        #QMessageBox.information(None, 'h_nodo', str(tension))
        tool = herrParcela(self.tipo_usuario, self.iface.mapCanvas(), self.conn)
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
        capas = []
        mapCanvas = self.iface.mapCanvas()
        n = mapCanvas.layerCount()
        layers = [mapCanvas.layer(i) for i in range(n)]
        str_nodos = '0'
        str_lineas = '0'
        str_postes = '0'
        str_areas = '0'
        str_parcelas = '0'
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                for ftr in lyr.selectedFeatures():
                    ftrs_nodos.append(ftr.id())
                    str_nodos = str_nodos + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
                for ftr in lyr.selectedFeatures():
                    ftrs_lineas.append(ftr.id())
                    str_lineas = str_lineas + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name()[:6] == 'Postes':
                for ftr in lyr.selectedFeatures():
                    ftrs_postes.append(ftr.id())
                    str_postes = str_postes + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name() == 'Areas':
                for ftr in lyr.selectedFeatures():
                    ftrs_areas.append(ftr.id())
                    str_areas = str_areas + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name() == 'Parcelas':
                for ftr in lyr.selectedFeatures():
                    ftrs_parcelas.append(ftr.id())
                    str_parcelas = str_parcelas + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)

        if len(ftrs_nodos) + len(ftrs_lineas) + len(ftrs_postes) + len(ftrs_areas) + len(ftrs_parcelas) > 0:
            if len(capas)==1:
                reply = QMessageBox.question(None, 'EnerGis', 'Desea borrar los elementos seleccionados ?', QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
                layers = [self.mapCanvas.layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Lineas WHERE Geoname IN (" + str_lineas + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Lineas !")
                        lyr.triggerRepaint()
                    elif lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Nodos WHERE Geoname IN (" + str_nodos + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Nodos !")
                        lyr.triggerRepaint()
                    elif lyr.name()[:6] == 'Postes':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Postes WHERE Geoname IN (" + str_postes + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Postes !")
                        lyr.triggerRepaint()
                    elif lyr.name() == 'Areas':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Areas WHERE Geoname IN (" + str_areas + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Areas !")
                        lyr.triggerRepaint()
                    elif lyr.name() == 'Parcelas':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Parcelas WHERE Geoname IN (" + str_parcelas + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Parcelas !")
                        lyr.triggerRepaint()
                    else:
                        #lyr.triggerRepaint()
                        pass
            else:
                from .frm_borrar import frmBorrar
                dialogo = frmBorrar(capas)
                dialogo.exec()
                capas=dialogo.capas
                dialogo.close()

                if len(capas)==0:
                    return

                layers = [self.mapCanvas.layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas_Temp':
                        for capa in capas:
                            if capa==lyr.name():
                                str_tension = lyr.name() [7 - len(lyr.name()):]
                                if str_tension.strip() == 'Proyectos':
                                    str_tension='0'
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Lineas WHERE Tension=" + str_tension + " AND Geoname IN (" + str_lineas + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Lineas !")
                                lyr.triggerRepaint()
                    elif lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos_Temp':
                        for capa in capas:
                            if capa==lyr.name():
                                str_tension = lyr.name() [6 - len(lyr.name()):]
                                if str_tension.strip() == 'Proyectos':
                                    str_tension='0'
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Nodos WHERE Tension=" + str_tension + " AND Geoname IN (" + str_nodos + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Nodos !")
                                lyr.triggerRepaint()
                    elif lyr.name()[:6] == 'Postes':
                        for capa in capas:
                            if capa==lyr.name():
                                str_tension = lyr.name() [7 - len(lyr.name()):]
                                if str_tension.strip() == 'Proyectos':
                                    str_tension='0'
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Postes WHERE Tension=" + str_tension + " AND Geoname IN (" + str_postes + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Postes !")
                                lyr.triggerRepaint()
                    elif lyr.name() == 'Areas':
                        for capa in capas:
                            if capa=='Areas':
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Areas WHERE Geoname IN (" + str_areas + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Areas !")
                                lyr.triggerRepaint()
                    elif lyr.name() == 'Parcelas':
                        for capa in capas:
                            if capa=='Parcelas':
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Parcelas WHERE Geoname IN (" + str_parcelas + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Parcelas !")
                                lyr.triggerRepaint()
                    else:
                        #lyr.triggerRepaint()
                        pass
            return
        pass


    def h_datos_eje(self):
        mapCanvas = self.iface.mapCanvas()
        n = mapCanvas.layerCount()
        layers = [mapCanvas.layer(i) for i in range(n)]
        str_ejes = '0'
        for lyr in layers:
            if lyr.name() == 'Ejes de Calle':
                for ftr in lyr.selectedFeatures():
                    #ftrs_ejes.append(ftr.id())
                    str_ejes = str_ejes + ',' + str(ftr.id())

        if str_ejes != '0':
            from .frm_datos_ejes import frmDatosEjes
            self.dialogo = frmDatosEjes(self.tipo_usuario, self.conn, str_ejes)
            self.dialogo.show()

        pass

    def h_borrar_ejes(self):
        ftrs_ejes = []
        mapCanvas = self.iface.mapCanvas()
        n = mapCanvas.layerCount()
        layers = [mapCanvas.layer(i) for i in range(n)]
        str_ejes = '0'
        for lyr in layers:
            if lyr.name() == 'Ejes de Calle':
                for ftr in lyr.selectedFeatures():
                    ftrs_ejes.append(ftr.id())
                    str_ejes = str_ejes + ',' + str(ftr.id())

        if len(ftrs_ejes) > 0:
            reply = QMessageBox.question(None, 'EnerGis', 'Desea borrar los ejes seleccionados ?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Ejes de Calle':
                    cursor = self.conn.cursor()
                    try:
                        cursor.execute("DELETE FROM Ejes WHERE Geoname IN (" + str_ejes + ")")
                        self.conn.commit()
                    except:
                        self.conn.rollback()
                        QMessageBox.information(None, 'EnerGis 5', "No se pudieron borrar Ejes !")
                    lyr.triggerRepaint()
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

    def h_crear_proyecto(self):
        text, ok = QInputDialog.getText(None, 'Ingreso de Datos', 'Nombre del Proyecto:')
        if ok:
            nuevo_proyecto = str(text)
        else:
            return
        if nuevo_proyecto=='':
            return
        for i in range (0, self.cmbProyecto.count()):
            if self.cmbProyecto.itemText(i) == nuevo_proyecto:
                QMessageBox.information(None, 'EnerGis 5', 'Ya existe un proyecto con ese nombre')
                return

        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO Proyectos (nombre, descripcion, fecha) VALUES ('" + nuevo_proyecto + "', '', GETDATE())")
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.information(None, 'EnerGis 5', "No se pudo agregar el Proyecto !")

        QMessageBox.information(None, 'EnerGis 5', 'Proyecto Creado')
        self.cmbProyecto.addItem(nuevo_proyecto)
        self.cmbProyecto.setCurrentIndex(self.cmbProyecto.count() - 1)
        self.proyecto = ''

        pass

    def elijo_proyecto(self):
        if self.cmbProyecto.currentText()=='<Proyecto>':
            for action in self.actions:
                if str(action.text())=='Modificar Proyecto':
                    action.setEnabled(False)
        else:
            for action in self.actions:
                if str(action.text())=='Modificar Proyecto':
                    action.setEnabled(True)
        pass

    def h_borrar_proyecto(self):
        reply = QMessageBox.question(None, 'EnerGis', 'Desea eliminar definitivamente el proyecto ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        self.borro_proyecto()

    def borro_proyecto(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM proyectos WHERE nombre='" + self.cmbProyecto.currentText() + "'")
            cursor.execute("DELETE FROM Nodos WHERE Tension=0 AND Alimentador='" + self.cmbProyecto.currentText() + "'")
            cursor.execute("DELETE FROM Lineas WHERE Tension=0 AND Alimentador='" + self.cmbProyecto.currentText() + "'")
            cursor.execute("DELETE FROM Postes WHERE Tension=0 AND Descripcion = '" + self.cmbProyecto.currentText() + "'")
            self.conn.commit()
        except:
            self.conn.rollback()

        self.cmbProyecto.removeItem(self.cmbProyecto.currentIndex())
        QMessageBox.information(None, 'EnerGis 5', "Proyecto Borrado !")
        self.proyecto = ''

        self.cmbProyecto.setCurrentIndex(0)
        for action in self.actions:
            if str(action.text())=='Modificar Proyecto':
                action.setChecked(True)
            if str(action.text())=='Nuevo Proyecto':
                action.setEnabled(True)
            if str(action.text())=='Incorporar Proyecto':
                action.setEnabled(False)
            if str(action.text())=='Borrar Proyecto':
                action.setEnabled(False)
        self.cmbProyecto.setEnabled(True)

    def h_editar_proyecto(self):
        b_estado=False
        #QMessageBox.information(None, 'EnerGis 5', '"Alimentador" = ' + "''")
        self.h_seleccion()
        if self.cmbProyecto.currentText()=='<Proyecto>':
            for action in self.actions:
                if str(action.text())=='Modificar Proyecto':
                    QMessageBox.information(None, 'EnerGis 5', 'Debe elegir un proyecto')
                    action.setChecked(False)
                if str(action.text())=='Nuevo Proyecto':
                    action.setEnabled(True)
                if str(action.text())=='Incorporar Proyecto':
                    action.setEnabled(False)
                if str(action.text())=='Borrar Proyecto':
                    action.setEnabled(False)
            return

        for action in self.actions:
            if str(action.text())=='Modificar Proyecto':
                b_estado = action.isChecked()

        self.cmbProyecto.setEnabled(True)

        if b_estado==True:
            self.proyecto = self.cmbProyecto.currentText()
            self.h_seleccion()
            for action in self.actions:
                if str(action.text())=='Nuevo Proyecto':
                    action.setEnabled(False)
                if str(action.text())=='Incorporar Proyecto':
                    action.setEnabled(True)
                if str(action.text())=='Borrar Proyecto':
                    action.setEnabled(True)

            self.cmbProyecto.setEnabled(False)
            n = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Postes Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'" + self.proyecto + "'")
                    lyr.triggerRepaint()
                if lyr.name() == 'Lineas Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'" + self.proyecto + "'")
                    lyr.triggerRepaint()
                if lyr.name() == 'Nodos Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'" + self.proyecto + "'")
                    lyr.triggerRepaint()
        else:
            self.proyecto = ''
            self.h_seleccion()
            for action in self.actions:
                if str(action.text())=='Nuevo Proyecto':
                    action.setEnabled(True)
                if str(action.text())=='Incorporar Proyecto':
                    action.setEnabled(False)
                if str(action.text())=='Borrar Proyecto':
                    action.setEnabled(False)

            n = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Nodos Proyectos' or lyr.name() == 'Lineas Proyectos' or lyr.name() == 'Postes Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'@@'")
                    lyr.triggerRepaint()
            self.cmbProyecto.setCurrentIndex(0)
        pass

    def h_incorporar_proyecto(self):
        reply = QMessageBox.question(None, 'EnerGis', 'Desea incorporar el proyecto al modelo ?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE Nodos SET Tension=CAST(subzona AS SMALLINT) WHERE Tension=0 AND Alimentador='" + self.proyecto + "'")
            cursor.execute("UPDATE Lineas SET Tension=CAST(exp AS SMALLINT) WHERE Tension=0 AND Alimentador='" + self.proyecto + "'")
            cursor.execute("UPDATE Postes SET Tension=CAST(profundidad AS SMALLINT) WHERE Tension=0 AND Descripcion='" + self.proyecto + "'")
            self.conn.commit()
            QMessageBox.information(None, 'EnerGis 5', "Proyecto Incorporado !")

            self.borro_proyecto()

        except:
            self.conn.rollback()
            QMessageBox.information(None, 'EnerGis 5', "No se pudo incorporar el Proyecto !")
        pass
