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

from PyQt5.QtWidgets import QMessageBox
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

#Nodos                          Lineas
#39:aux2:elm                    7:aux2:
#40:aux3:alimentador            8:aux3:
#41:aux4:trafo                  9:aux4:
#43:aux6:nodo_padre            10:aux5:nodo_padre
#44:aux7:seccionador           11:aux6:seccionador
#45:aux8:marca_reducciones     12:aux7:marca_reducciones

def __init__(self):
    self.lineas_del_nodo=[]
    self.proximos_nodos=[]
    pass

def navegar_compilar_red(self, mnodos, mlineas, monodos, fuente_navegada):
    #--------------------------------------------------------------------------------------
    #esta rutina navega la red desde una fuente y marca el camino que recorre .
    #--------------------------------------------------------------------------------------
    k = 0
    l = 0
    m = 0
    n = 0
    nodo = 0
    trafo_navegado = 0
    i_orden = 0
    #****************************************
    nodo = fuente_navegada
    pendientes = []
    seccionador = 0
    nodo_padre = nodo
    repetir = True
    accion = 'Navegar Fuente'
    #****************************************
    try:
        mnodos[fuente_navegada][3] = fuente_navegada
        while repetir == True:
            repetir = False
            if nodo == 0:
                #me fijo si me quedo algun seccionador abierto sin ordenar, se pone al final
                for n in range (0, len(mnodos)):
                    if mnodos[n][2] == 3: #es un seccionador abierto
                        k = 0
                        for m in range (0, len(mnodos)):
                            if monodos[m]==n:
                                k = 1
                                m = len(mnodos)
                            elif monodos[m]==0:
                                l = m
                        if k==0:
                            monodos[l] = n
                repetir = True
            else:
                m = 0
                for n in range (0, len(mnodos)):
                    if monodos[n]==nodo:
                        m = 1
                        n = len(mnodos)
                if m==0:
                    accion = 'Ordenando Nodos'
                    i_orden = i_orden + 1
                    monodos[i_orden] = nodo
                #****************************************
                mnodos[nodo][3] = fuente_navegada
                mnodos[nodo][41] = trafo_navegado
                #****************************************
                #al trafo le dejo el id del trafo aguas arriba y a partir de aca el id es este
                accion = 'Asignar Transformador'
                if mnodos[nodo][2]==4:
                    trafo_navegado = nodo
                #****************************************
                accion = 'Buscar Lineas'
                cant_lineas_del_nodo = buscar_lineas_segun_nodo(self, mnodos, mlineas, nodo)
                #****************************************
                for n in range (0, cant_lineas_del_nodo):
                    if mnodos[self.proximos_nodos[n]][2] == 3:
                        #como el ultimo nodo de cada spur
                        mlineas[self.lineas_del_nodo[n]][4] = fuente_navegada
                        mnodos[self.proximos_nodos[n]][3] = fuente_navegada
                        mnodos[self.proximos_nodos[n]][41] = trafo_navegado
                        if mnodos[self.proximos_nodos[n]][43] == 0:
                            mnodos[self.proximos_nodos[n]][43] = nodo
                        if mnodos[self.proximos_nodos[n]][44] == 0:
                            mnodos[self.proximos_nodos[n]][44] = seccionador
                        if mlineas[self.lineas_del_nodo[n]][10] == 0:
                            mlineas[self.lineas_del_nodo[n]][10] = nodo
                        if mlineas[self.lineas_del_nodo[n]][11] == 0:
                            mlineas[self.lineas_del_nodo[n]][11] = seccionador
                        #aca no dejo pendientes porque se trata de una seccionador abierto
            #****************************************
            if mnodos[nodo][2]==3:
                #como el ultimo nodo de cada spur
                #Aca esta suponiendo que el seccionador abierto tiene una sola línea que le llega, pero esta mal
                #hay que marcar la linea del lado que venia navegando.
                mlineas[mnodos[nodo][5]][4] = fuente_navegada
                if mlineas[mnodos[nodo][5]][10] == 0:
                    mlineas[mnodos[nodo][5]][10] = nodo_padre
                if mlineas[mnodos[nodo][5]][11] == 0:
                    mlineas[mnodos[nodo][5]][11] = seccionador
                #si cambia la tension del pendiente blanqueo el ultimo trafo navegado
                    #eso falta
                #paso al nodo siguiente
                if len(pendientes) > 0:
                    nodo = pendientes[len(pendientes) - 1] #tomo el nodo del ultimo valor de la lista
                    pendientes.pop() #elimino el ultimo valor de la lista
                    nodo_padre = mnodos[nodo][43]
                    seccionador = mnodos[nodo][44]
                    #repetir = True
            if repetir==False: #si repetir=True voy hasta el fondo para iterar
                accion = 'Buscar lineas del nodo'
                #****************************************
                cant_lineas_del_nodo = buscar_lineas_segun_nodo(self, mnodos, mlineas, nodo)
                #****************************************
                camino = -1
                #escojo el primer camino aún no recorrido
                accion = 'Escoger Camino'
                for n in range (0, cant_lineas_del_nodo):
                    if mlineas[self.lineas_del_nodo[n]][4] == 0:
                        camino = n
                        n = cant_lineas_del_nodo + 1
                linea_navegando = self.lineas_del_nodo[camino]
                mlineas[linea_navegando][4] = fuente_navegada
                if mlineas[linea_navegando][10] == 0:
                    mlineas[linea_navegando][10] = nodo
                if mlineas[linea_navegando][11] == 0:
                    mlineas[linea_navegando][11] = seccionador
                #****************************************
                #agrego los caminos pendientes que aún no estan pendientes
                accion = 'Agregar Pendientes'
                for n in range (0, cant_lineas_del_nodo):
                    if camino!=n:
                        if mlineas[self.lineas_del_nodo[n]][4] == 0:
                            pendientes.append(self.proximos_nodos[n])
                            if mnodos[self.proximos_nodos[n]][43] == 0:
                                mnodos[self.proximos_nodos[n]][43] = nodo
                            if mnodos[self.proximos_nodos[n]][44] == 0:
                                mnodos[self.proximos_nodos[n]][44] = seccionador
                            if mlineas[self.lineas_del_nodo[n]][10] == 0:
                                mlineas[self.lineas_del_nodo[n]][10] = nodo
                            if mlineas[self.lineas_del_nodo[n]][11] == 0:
                                mlineas[self.lineas_del_nodo[n]][11] = seccionador
                if camino!=-1:
                    #si cambia la tension del pendiente blanqueo el ultimo trafo navegado
                        #eso falta
                    #paso al nodo siguiente
                    nodo_padre = nodo
                    if mnodos[nodo][2]==2:
                        seccionador = nodo
                    #****************************************
                    accion = 'Elegir Pemdiemte'
                    nodo = self.proximos_nodos[camino]
                    mnodos[nodo][3] = fuente_navegada
                else:
                    if mnodos[nodo][4]==1: #ultimo nodo (de cada spur)
                        accion = 'Spur'
                        mlineas[mnodos[nodo][5]][4] = fuente_navegada
                        if mlineas[mnodos[nodo][5]][10] == 0:
                            mlineas[mnodos[nodo][5]][10] = nodo_padre
                        if mlineas[mnodos[nodo][5]][11] == 0:
                            mlineas[mnodos[nodo][5]][11] = seccionador
                    #si cambia la tension del pendiente blanqueo el ultimo trafo navegado
                        #eso falta
                    #paso al nodo siguiente
                    if len(pendientes)==0:
                        return 'Red Navegada'
                    accion = 'Tomar Pemdiemte'
                    nodo = pendientes[len(pendientes) - 1] #tomo el nodo del ultimo valor de la lista
                    pendientes.pop() #elimino el ultimo valor de la lista
                    nodo_padre = mnodos[nodo][43]
                    seccionador = mnodos[nodo][44]
            repetir = True
            nodo_padre = nodo
            if mnodos[nodo][2]==2:
                seccionador = nodo
        return 'Verificar Navegacion'
    except:
        return 'Navegacion - Verificar nodo - en ' + accion + ': ' + str(mnodos[nodo][1])

def buscar_loops(self, mnodos, mlineas):
    #reduccion de matrices de nodos y lineas
    cant_spurs = 1
    while cant_spurs != 0:
        cant_spurs = 0
        for n in range (0, len(mnodos)):
            mnodos[n][45] = 1
            if mnodos[n][4]==0:
                mnodos[n][45] = 0
            if mnodos[n][1]!=0 and (mnodos[n][4]==1 or mnodos[n][2]==3) and mnodos[n][2]!=1:
                cant_spurs = cant_spurs + 1
                cant_lineas_del_nodo = buscar_lineas_segun_nodo(self, mnodos, mlineas, n)
                for i in range (0, cant_lineas_del_nodo):
                    id = self.lineas_del_nodo[i]
                    pf = mlineas[id][2]
                    pt = mlineas[id][3]
                    mlineas[id][1] = 0
                    mlineas[id][2] = 0
                    mlineas[id][3] = 0
                    mlineas[id][4] = 0
                    mlineas[id][5] = 0
                    mlineas[id][6] = 0
                    mlineas[id][12] = 0
                    mnodos[pf][4] = mnodos[pf][4] - 1
                    for v in range (1, 32):
                        if mnodos[pf][4 + v] == id:
                            for m in range (v, 31):
                                mnodos[pf][4 + m] = mnodos[pf][4 + m + 1]
                            mnodos[pf][4 + 32] = 0
                            v = 32
                    mnodos[pt][4] = mnodos[pt][4] - 1
                    for v in range (1, 32):
                        if mnodos[pt][4 + v] == id:
                            for m in range (v, 31):
                                mnodos[pt][4 + m] = mnodos[pt][4 + m + 1]
                            mnodos[pt][4 + 32] = 0
                            v = 32
                mnodos[n][1] = 0
                mnodos[n][45] = 0

    for n in range (0, len(mlineas)):
        if mlineas[n][1]!=0:
            mlineas[n][12] = 1
    pass

def navegar_a_las_fuentes(self, mnodos, mlineas, geoname):
    #reduccion de matrices de nodos y lineas
    cant_spurs = 1
    while cant_spurs != 0:
        cant_spurs = 0
        for n in range (0, len(mnodos)):
            mnodos[n][45] = 1
            if mnodos[n][4]==0:
                mnodos[n][45] = 0
            if mnodos[n][1]!=0 and (mnodos[n][4]==1 or mnodos[n][2]==3) and mnodos[n][2]!=1 and mnodos[n][1]!=geoname:
                cant_spurs = cant_spurs + 1
                cant_lineas_del_nodo = buscar_lineas_segun_nodo(self, mnodos, mlineas, n)
                for i in range (0, cant_lineas_del_nodo):
                    try:
                        id = self.lineas_del_nodo[i]
                    except:
                        QMessageBox.information(None, "Mensaje", "Error en Nodo : " + str(mnodos[n][1]))
                        return
                    pf = mlineas[id][2]
                    pt = mlineas[id][3]
                    mlineas[id][1] = 0
                    mlineas[id][12] = 0
                    mnodos[pf][4] = mnodos[pf][4] - 1
                    for v in range (1, 32):
                        if mnodos[pf][4 + v] == id:
                            for m in range (v, 31):
                                mnodos[pf][4 + m] = mnodos[pf][4 + m + 1]
                            mnodos[pf][4 + 32] = 0
                            v = 32
                    mnodos[pt][4] = mnodos[pt][4] - 1
                    for v in range (1, 32):
                        if mnodos[pt][4 + v] == id:
                            for m in range (v, 31):
                                mnodos[pt][4 + m] = mnodos[pt][4 + m + 1]
                            mnodos[pt][4 + 32] = 0
                            v = 32
                mnodos[n][1] = 0
                mnodos[n][45] = 0
    for n in range (0, len(mlineas)):
        if mlineas[n][1]!=0:
            mlineas[n][12] = 1
    pass

def navegar_a_nodo(self, mnodos, mlineas, desde, hasta):
    #reduccion de matrices de nodos y lineas
    cant_spurs = 1
    while cant_spurs != 0:
        cant_spurs = 0
        for n in range (0, len(mnodos)):
            mnodos[n][45] = 1
            if mnodos[n][4]==0:
                mnodos[n][45] = 0
            if mnodos[n][1]!=0 and mnodos[n][2]==3 and mnodos[n][1]!=geoname:
                cant_spurs = cant_spurs + 1
                cant_lineas_del_nodo = buscar_lineas_segun_nodo(self, mnodos, mlineas, n)
                for i in range (0, cant_lineas_del_nodo):
                    id = self.lineas_del_nodo[i]
                    pf = mlineas[id][2]
                    pt = mlineas[id][3]
                    mlineas[id][1] = 0
                    mlineas[id][2] = 0
                    mlineas[id][3] = 0
                    mlineas[id][4] = 0
                    mlineas[id][5] = 0
                    mlineas[id][6] = 0
                    mlineas[id][12] = 0
                    mnodos[pf][4] = mnodos[pf][4] - 1
                    for v in range (1, 32):
                        if mnodos[pf][4 + v] == id:
                            for m in range (v, 31):
                                mnodos[pf][4 + m] = mnodos[pf][4 + m + 1]
                            mnodos[pf][4 + 32] = 0
                            v = 32
                    mnodos[pt][4] = mnodos[pt][4] - 1
                    for v in range (1, 32):
                        if mnodos[pt][4 + v] == id:
                            for m in range (v, 31):
                                mnodos[pt][4 + m] = mnodos[pt][4 + m + 1]
                            mnodos[pt][4 + 32] = 0
                            v = 32
                mnodos[n][1] = 0
                mnodos[n][45] = 0
    for n in range (0, len(mlineas)):
        if mlineas[n][1]!=0:
            mlineas[n][12] = 1
    pass

def buscar_lineas_segun_nodo(self, mnodos, mlineas, nodo_buscado):
    #--------------------------------------------------------------------------------------
    #esta función devuelve una lista de lineas que tocan a un nodo (hasta 32), la cantidad
    #y la lista de nodos a los que se dirigen esas lineas, y ordenados como las mismas
    #--------------------------------------------------------------------------------------
    cant_lineas_del_nodo = 0
    self.lineas_del_nodo=[]
    self.proximos_nodos=[]
    try:
        cant_lineas_del_nodo = mnodos[nodo_buscado][4]
        for m in range (0, cant_lineas_del_nodo):
            linea = mnodos[nodo_buscado][m + 5]
            self.lineas_del_nodo.append(linea)
            if nodo_buscado == mlineas[linea][3]:
                self.proximos_nodos.append(mlineas[linea][2])
            elif nodo_buscado == mlineas[linea][2]:
                self.proximos_nodos.append(mlineas[linea][3])
            else:
                return cant_lineas_del_nodo
        return cant_lineas_del_nodo
    except:
        return cant_lineas_del_nodo

def caida_tension(self, mnodos, mlineas, geoname):
    #reduccion de matrices de nodos y lineas
    nodos_asociados = [[]]

    for n in range (0, len(mnodos)):
        nodos_asociados.append([])

    cant_spurs = 1
    iteracion = 0
    while cant_spurs != 0:
        cant_spurs = 0

        iteracion = iteracion + 1
        #QMessageBox.information(None, "Mensaje", "Iteracion: " + str(iteracion))

        for n in range (0, len(mnodos)):
            mnodos[n][45] = 1
            if mnodos[n][4]==0:
                #si no tiene lineas
                mnodos[n][45] = 0 #no navegado

            if mnodos[n][1]!=0 and (mnodos[n][4]==1 or mnodos[n][2]==3) and mnodos[n][2]!=1 and mnodos[n][1]!=geoname:
                #si (geoname no es cero) y (tiene una sola linea o es un NA) y (no es fuente) y (no es el nodo inicial)

                #el listado de asociaciones es el del nodo n
                na = nodos_asociados[n]
                if mnodos[n][2]==6 or mnodos[n][2]==4: #si es trafo o suministro
                    na.append(mnodos[n][1])
                    nodos_asociados[n] = na

                #reduzco el nodo n al otro nodo de la línea
                cant_spurs = cant_spurs + 1 #sumo uno solo para el while
                cant_lineas_del_nodo = buscar_lineas_segun_nodo(self, mnodos, mlineas, n)
                for i in range (0, cant_lineas_del_nodo):
                    #pueden ser una o dos lineas si es nodo o NA
                    id = self.lineas_del_nodo[i]
                    pf = mlineas[id][2]
                    pt = mlineas[id][3]

                    #detecto proximos nodos asi les puedo pasar los nodos asociados
                    #al proximo nodo le transmito los asociados del actual
                    if pf==n:
                        na = nodos_asociados[pt]
                        for j in range (0, len(nodos_asociados[n])):
                            na.append(nodos_asociados[n][j])
                        nodos_asociados[pt] = na
                    elif pt==n:
                        na = nodos_asociados[pf]
                        for j in range (0, len(nodos_asociados[n])):
                            na.append(nodos_asociados[n][j])
                        nodos_asociados[pf] = na
                    else:
                        QMessageBox.information(None, "Mensaje", "Error en línea : " + str(mlineas[id][1]))

                    #elimino la linea del spur
                    mlineas[id][1] = 0
                    mlineas[id][12] = 0

                    #le saco el proximo nodo al nodo desde de la linea
                    mnodos[pf][4] = mnodos[pf][4] - 1
                    for v in range (1, 32):
                        if mnodos[pf][4 + v] == id:
                            for m in range (v, 31):
                                mnodos[pf][4 + m] = mnodos[pf][4 + m + 1]
                            mnodos[pf][4 + 32] = 0
                            v = 32

                    #le saco el proximo nodo al nodo hasta de la linea
                    mnodos[pt][4] = mnodos[pt][4] - 1
                    for v in range (1, 32):
                        if mnodos[pt][4 + v] == id:
                            for m in range (v, 31):
                                mnodos[pt][4 + m] = mnodos[pt][4 + m + 1]
                            mnodos[pt][4 + 32] = 0
                            v = 32
                #elimino el nodo
                mnodos[n][1] = 0
                mnodos[n][45] = 0

    #f = open(os.path.join(basepath,"salidas", 'salida_navegacion.txt'), 'w')
    #f.write('\n' + 'Nodo analizado = ' + str(geoname))
    #for n in range (0, len(mnodos)):
    #    if mnodos[n][1]!=0:
    #        f.write('\n' + str(mnodos[n][1]) + chr(9) + str(n) + chr(9) + str(nodos_asociados[n]))
    #f.close()

    for n in range (0, len(mlineas)):
        if mlineas[n][1]!=0:
            mlineas[n][12] = 1

    #QMessageBox.information(None, "Mensaje", "Fin - Salida a txt")
    pass

def nodos_por_seccionador(self, conn, mnodos, mlineas):
    #ver en nodos_por_salida
    #reduccion de matrices de nodos y lineas
    nodos_asociados = [[]]
    nodos_geoname = []
    for n in range (0, len(mnodos)):
        nodos_asociados.append([])
        nodos_geoname.append(mnodos[n][1])
    cant_spurs = 1
    #ver en nodos_por_salida
    while cant_spurs != 0:
        cant_spurs = 0
        for n in range (0, len(mnodos)):
            mnodos[n][45] = 1
            if mnodos[n][4]==0:
                mnodos[n][45] = 0
            if mnodos[n][1]!=0 and (mnodos[n][4]==1 or mnodos[n][2]==3) and mnodos[n][2]!=1:
                #ver en nodos_por_salida
                pass
    #cursor = conn.cursor()
    #cursor.execute("TRUNCATE TABLE nodos_seccionador")
    #for n in range (0, len(self.mnodos_secc)):
    #    if self.mnodos_secc[n][39]==2:
    #        cursor.execute("INSERT INTO nodos_seccionador (geoname, nodos) VALUES (" + str(nodos_geoname[n]) + ",'" + str(nodos_asociados[n]).replace('[','').replace(']','') + "')")
    #conn.commit()

def nodos_por_salida(self, conn, mnodos, mlineas):
    #reduccion de matrices de nodos y lineas
    nodos_asociados = [[]]
    nodos_geoname = []
    #armo un array vacio con una columna por nodo para alojar a los nodos asociados a cada uno
    for n in range (0, len(mnodos)):
        nodos_asociados.append([])
        nodos_geoname.append(mnodos[n][1])
    #vaciamos la tabla que guarda los nodos por alimentador (geoname, id)
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE Nodos_Alimentador")
        conn.commit()
    except:
        conn.rollback()
    #f = open(os.path.join(basepath,"salidas", 'salidas_nodos.txt'), 'w')
    #f.write('\n' + 'salidas_nodos')
    #f.close()
    #Reduccion de Red por niveles de salidas de alimentador
    #Se utiliza el elemento y no el estado de los mismos
    #Se recorre el array de nodos, se le va asignando geoname=0 para anularlos
    #Con un máximo de 10 niveles se pretende encontrar los nodos por salida
    nivel = 1
    #Arranque
    seguir = 1
    #Se seguirá siempre y cuando queden salidas por recorrer
    while seguir == 1:
        #Arranque
        cant_spurs = 1
        #Se seguirá siempre y cuando existan spurs
        while cant_spurs != 0:
            #Blanqueo cantidad de spurs
            cant_spurs = 0
            #Se recorre el array de nodos tratando de agrupar para este nivel todos los nodos hacia la salida
            for n in range (0, len(mnodos)):
                #si es aislado lo desmarco
                if mnodos[n][4]==0:
                    mnodos[n][45] = 0
                else:
                    #Marco el nodo que analizo en posicion 45
                    mnodos[n][45] = 1
                #Si no esta borrado y (es spur o es SA) y no es fuente
                if mnodos[n][1]!=0 and (mnodos[n][4]==1 or mnodos[n][39]==3) and mnodos[n][2]!=1:
                    #Si no es salida de alimentador:
                    if mnodos[n][2]!=8:
                        #sumo uno a la lista de spurs para continuar intentando reducir
                        cant_spurs = cant_spurs + 1
                        #El listado de asociaciones inicial es el que tenia el nodo al momento de consultarlo
                        na = nodos_asociados[n]
                        #Al listado de asociados que posee este nodo (que ahora es spur) le agrego este mismo
                        na.append(mnodos[n][1])
                        #Ahora el listado de asociados a este nodo es la lista total
                        nodos_asociados[n] = na
                        #Busco LA LINEA del nodo
                        cant_lineas_del_nodo = buscar_lineas_segun_nodo(self, mnodos, mlineas, n)
                        for i in range (0, cant_lineas_del_nodo):
                            #Para cada una de las lineas del nodo, obtenemos desde y hasta
                            id = self.lineas_del_nodo[i]
                            pf = mlineas[id][2]
                            pt = mlineas[id][3]
                            #Detecto el próximo nodo asi le puedo pasar los nodos asociados del actual
                            #Tienen que ser nodos aguas arriba, o sea que no tienen que estar marcados
                            #Si el nodo desde es n, el proximo setá el hasta
                            if pf==n:
                                #El nodo a asocial es el hasta
                                p = pt
                            elif pt==n:
                                #El nodo a asocial es el desde
                                p = pf
                            else: #Si no encuentro desde ni hasta hay un error
                                QMessageBox.information(None, "Mensaje", "Error en línea : " + str(mlineas[id][1]))

                            if mnodos[p][0]!=0:
                                na = nodos_asociados[p]
                                for j in range (0, len(nodos_asociados[n])):
                                    na.append(nodos_asociados[n][j])
                                nodos_asociados[p] = na

                            #Borro existencia de la linea
                            mlineas[id][1] = 0
                            mlineas[id][2] = 0
                            mlineas[id][3] = 0
                            mlineas[id][4] = 0
                            mlineas[id][5] = 0
                            mlineas[id][6] = 0
                            mlineas[id][12] = 0

                            #Al proximo nodo le quito a n como proximo nodo
                            mnodos[p][4] = mnodos[p][4] - 1
                            for v in range (1, 32):
                                if mnodos[p][4 + v] == id:
                                    for m in range (v, 31):
                                        mnodos[p][4 + m] = mnodos[p][4 + m + 1]
                                    mnodos[p][4 + 32] = 0
                                    v = 32

                        #Anulo el nodo que ya navegué
                        mnodos[n][1] = 0
                        mnodos[n][45] = 0

                    else: #Si el spur es una salida de alimentador:
                        #Si posee nodos asociados los paso a la base
                        if len(nodos_asociados[n])>0:

                            #f = open(os.path.join(basepath,"salidas", 'salidas_nodos.txt'), 'a')
                            #f.write('\n' + str(nodos_geoname[n]) + chr(9) + str(n) + chr(9) + str(nodos_asociados[n]))
                            #f.close()

                            cursor = conn.cursor()
                            try:
                                cursor.execute("INSERT INTO Nodos_Alimentador SELECT geoname, " + str(nodos_geoname[n]) + " FROM Nodos WHERE Nodos.Tension>0 AND geoname IN (" + str(nodos_geoname[n]) + "," + str(nodos_asociados[n]).replace('[','').replace(']','') + ")")
                                conn.commit()
                            except:
                                conn.rollback()
                            #Ya grabados los nodos asociados a la salida, desasociamos los nodos para que no pasen aguas arriba
                            nodos_asociados[n] = []
                            #nodos_asociados[n].append(0)
                            #Convierto a la salida en un nodo comun para poder seguir aguas arriba
                            mnodos[n][2] = 0

        #si tengo todavia salidas para navegar, sumo un nivel
        existe=0
        for n in range (0, len(mnodos)):
            if mnodos[n][1]!=0 and mnodos[n][2]==8:
                existe=1
                #QMessageBox.information(None, "Mensaje", "Salida : " + str(mnodos[n][1]))
                n = len(mnodos)

        if existe==1:
            nivel = nivel + 1
            #QMessageBox.information(None, "Mensaje", "Nivel : " + str(nivel))
            seguir = 1
            if nivel > 10:
                seguir = 0
        else:
            seguir = 0

    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE A SET d=o FROM (SELECT Nodos.Alimentador AS d, Nodos_1.Val1 AS o FROM Nodos_Alimentador INNER JOIN Nodos ON Nodos_Alimentador.Geoname = Nodos.Geoname INNER JOIN Nodos AS Nodos_1 ON Nodos_Alimentador.Id = Nodos_1.Geoname AND Nodos.Alimentador <> Nodos_1.Val1 WHERE (Nodos.Elmt <> 8)) A")
        cursor.execute("UPDATE A SET d=o FROM (SELECT Lineas.Alimentador AS d, Nodos.Alimentador AS o FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde AND Nodos.Alimentador <> Lineas.Alimentador INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname AND Nodos.Alimentador = Nodos_1.Alimentador) A")
        cursor.execute("UPDATE A SET d=o FROM (SELECT Lineas.Alimentador AS d, Nodos.Alimentador AS o FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde AND Nodos.Alimentador <> Lineas.Alimentador INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname WHERE (Nodos_1.Estado = 3)) A")
        cursor.execute("UPDATE A SET d=o FROM (SELECT Lineas.Alimentador AS d, Nodos.Alimentador AS o FROM Nodos INNER JOIN Lineas ON Nodos.Alimentador <> Lineas.Alimentador AND Nodos.Geoname = Lineas.Hasta INNER JOIN Nodos AS Nodos_1 ON Lineas.Desde = Nodos_1.Geoname WHERE (Nodos_1.Estado = 3)) A")
        conn.commit()
    except:
        conn.rollback()
        QMessageBox.information(None, 'EnerGis 5', "No se pudo incroporar el Proyecto !")

    pass

