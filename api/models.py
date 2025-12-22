from datetime import date
from django.db import models
from django.db import connections
from sepa.views import dictfetchall
import pyodbc
import time



class pilotManager(models.Manager):

    def getMovID(self, database, id):
        connections.databases[database["dbprofilename"]] = database["dbprofiledata"]
        with connections[database].cursor() as cursor:
            cursor.execute("select movid from venta where id = "+ str(id))
            result = dictfetchall(cursor)
        if result == []:
            return False
        return result[0]['movid']

    def insertLogWebhook(self, database, datos):
        connections.databases[database["dbprofilename"]] = database["dbprofiledata"]
        with  connections[database["dbprofilename"]].cursor() as cursor:
            cursor.execute("INSERT INTO CA_LogWebhook(IDPilot,Topic,Event) VALUES(%s,%s,%s);", [datos['id'], datos['topic'], datos['event']])
            cursor.execute("DECLARE @ok INT, @okRef VARCHAR(255); exec xpCA_FordPilotWebhook %s, %s, @ok output, @okRef output; SELECT @ok AS error, @okRef AS comment", [datos['id'], int(datos['sucursal'])])
            result = dictfetchall(cursor)
            return result

    def testDbConnection (self, database, timeOut):
        respuesta = {}
        #* Establecer el tiempo de inicio.
        start_time = time.time()
        datosDB = database["dbprofiledata"]
        if datosDB["PORT"] != '':
            datosDB["HOST"] += ','+datosDB["PORT"]
        #* La conexión se realiza de esta forma para que la prueba sea mas rapida
        connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={datosDB["HOST"]};DATABASE={datosDB["NAME"]};UID={datosDB["USER"]};PWD={datosDB["PASSWORD"]}'
        try:
            #* Intentar la conexión a la base de datos.
            connection = pyodbc.connect(connection_string, timeout=timeOut)
            connection.cursor()
            connection.close()
            respuesta["Mensaje"] = (f'Conexión exitosa.')
            respuesta["Estatus"] = True
        except Exception as e:
            respuesta["Estatus"] = False
            respuesta["Mensaje"] = (f'No fue posible realizar la conexión: {e}')
        #* Calcular el tiempo de ejecución.
        elapsed_time = time.time() - start_time
        respuesta["tiempo"] = elapsed_time
        return respuesta

    def getSalesHistory(self, database, idVentaPilot):
        response = {}
        response['status'] = False
        try:
            connections.databases[database["dbprofilename"]] = database["dbprofiledata"]
            with connections[database["dbprofilename"]].cursor() as cursor:
                cursor.execute("""
                SELECT 
                    l.ID,
                    ld.Response, 
                    l.Tipo, 
                    l.Estatus,
                    l.FechaEnvio
                FROM 
                    CA_LogMovimientosInterfaz l
                JOIN 
                    CA_LogMovimientosInterfazD ld on l.ID = ld.logID
                WHERE 
                    Interfaz = 'FordPilot'
                    AND ld.Response LIKE %s
                    AND l.TIPO IN ('ventaMOVID', 'notificaFactura', 'anularUFACT','notificaEntrega', 'asignacionVIN', 'asignacionClienteVenta')
                ORDER BY ID DESC
                """, ['%' + idVentaPilot + '%'])
                response['historico'] = dictfetchall(cursor)
                if response['historico'] != []:
                    response['status'] = True
        except Exception as e:
            response['details'] = e
            response['historico'] = {}

        return response

    def getVehicleHistory(self, database, idVehiclePilot):
        response = {}
        response['status'] = False
        try:
            connections.databases[database["dbprofilename"]] = database["dbprofiledata"]
            with connections[database["dbprofilename"]].cursor() as cursor:
                cursor.execute("""
                SELECT
                    l.ID,
                    ld.Response, 
                    l.Tipo, 
                    l.Estatus,
                    l.FechaEnvio
                FROM 
                    CA_LogMovimientosInterfaz l
                JOIN 
                    CA_LogMovimientosInterfazD ld on l.ID = ld.logID
                WHERE 
                    Interfaz = 'FordPilot'
                    AND (ld.Response LIKE %s
                        OR  l.Request LIKE %s)
                AND l.TIPO IN ('createStock', 'asignacionVIN', 'anularUFACT','actualizaDatosFACT','actualizaFechaEntrega', 'liberarUni')
                ORDER BY ID DESC
                """, ['%' + idVehiclePilot + '%','%' + idVehiclePilot + '%'])
                response['historico'] = dictfetchall(cursor)
                cursor.execute("select estatus FROM CA_VIN CV JOIN VIN V ON V.VIN = CV.VIN where IdInterfaz = %s", [idVehiclePilot])
                response['statusIntelisis'] = cursor.fetchone()[0]
                if response['historico'] != [] and response['statusIntelisis'] != []:
                    response['status'] = True
        except Exception as e:
            response['details'] = e
            response['historico'] = {}

        return response

    def getLogSucursal (self, database, id_intelisis):
        datos = {}
        datos['status'] = True
        datos['details'] = '-'
        try:
            connections.databases[database["dbprofilename"]] = database["dbprofiledata"]
            with connections[database["dbprofilename"]].cursor() as cursor:
                cursor.execute("SELECT TOP 100 l.id,l.Estatus, l.FechaEnvio,l.Tipo,l.Request,ld.Response, ld. Descripcion FROM CA_LogMovimientosInterfaz as l INNER JOIN CA_LogMovimientosInterfazD as ld on l.id = ld.logID WHERE Interfaz = 'FordPilot' AND l.Sucursal = %s ORDER BY id DESC", [id_intelisis])
                datos['data'] = dictfetchall(cursor)
                if datos['data'] == []:
                    datos['status'] = False
        except Exception as e :
            datos['status'] = False
            datos['details'] = e
            datos['data'] = '-'
        return datos

    #TODO Restructurar para mejorar la query y manejar correctamente los estatus que se generan 
    def getBranchInfo (self, database, id_intelisis):
        data = {}
        status = False
        try:
            # Suponiendo que 'cursor' es tu objeto de cursor previamente configurado
            connections.databases[database["dbprofilename"]] = database["dbprofiledata"]
            with  connections[database["dbprofilename"]].cursor() as cursor:

                cursor.execute("SELECT valor FROM CA_CatParametrosSucursal WHERE Clave = 'HabilitarPilot' AND Sucursal = %s", [id_intelisis])
                data['habilitado'] = cursor.fetchone()

                cursor.execute("SELECT valor FROM CA_CatParametrosSucursal WHERE Clave = 'UsuarioPilot' AND Sucursal = %s", [id_intelisis])
                data['usuario'] = cursor.fetchone()

                cursor.execute("SELECT valor FROM CA_CatParametrosSucursal WHERE Clave = 'IdInstanciaPilot' AND Sucursal = %s", [id_intelisis])
                data['instancia'] = cursor.fetchone()

                cursor.execute("SELECT nombre FROM Sucursal WHERE Sucursal = %s", [id_intelisis])
                data['nombre'] = cursor.fetchone()

                cursor.execute("SELECT COUNT(*) FROM ca_venta cv JOIN Venta v ON v.id = cv.IdVenta WHERE IdVentaPilot IS NOT NULL AND (IdVenta = IdVentaCopiaOrigen OR IdVentaCopiaOrigen IS NULL) AND v.Sucursal = %s", [id_intelisis])
                data['cantidadVentas'] = cursor.fetchone()
            status = True
        except Exception as e :
            data['error'] = e

        return {'data' : data, 'status': status}
class pilot(models.Model):
    objects = pilotManager()