from rest_framework import viewsets,status
from rest_framework.views import APIView
from rest_framework.response import Response

def conectarapiintelisis(sucursal):
    try:
        with in_database('default'):
            branch = sepa_branch.objects.filter(id=sucursal).values('id','id_company','clave','nombre','telefono','correo','fecha_creacion','fecha_actualizacion','conf_ip_ext','conf_ip_int','conf_user','conf_pass','conf_db','conf_port','id_intelisis','empresa_intelisis','foto','foto_alt','eliminado','direccion','latitud','longitud','gwmbac','id_district','fotos_recepcion','db_recepcion')[0]
            external_db = {
                'ENGINE': 'mssql',
                'NAME': branch["conf_db"],
                'USER': branch["conf_user"],
                'PASSWORD': branch["conf_pass"],
                'HOST': branch[profilecode()],
                'PORT': xstr(branch["conf_port"]),
                'OPTIONS': {
                    'driver': 'ODBC Driver 17 for SQL Server',
                }
            }
            external_recepcion_db = {
                'ENGINE': 'mssql',
                'NAME': branch["db_recepcion"],
                'USER': branch["conf_user"],
                'PASSWORD': branch["conf_pass"],
                'HOST': branch[profilecode()],
                'PORT': xstr(branch["conf_port"]),
                'OPTIONS': {
                    'driver': 'ODBC Driver 17 for SQL Server',
                }
            }
            crm_old_db = {
                'ENGINE': 'mssql',
                'NAME': "CRM_FAME",
                'USER': branch["conf_user"],
                'PASSWORD': "123456Qwerty",
                'HOST': "10.255.0.20",
                'PORT': "",
                'OPTIONS': {
                    'driver': 'ODBC Driver 17 for SQL Server',
                }
            }
            return {'dbprofilename': branch["empresa_intelisis"] + '_' + str(branch["id"]),'dbprofilenamerecepcion': branch["db_recepcion"],'dbprofiledata':external_db,'dbprofiledatarecepcion':external_recepcion_db,'dbprofiledatacrmold':crm_old_db}
    except Exception as e:
        print(str(e))
        return None

#Function for save data into log table
def loggeractions(cliente,branch,tipo_movimiento,tabla,device,connection,post,url,sql,origen=None):
    poststr = str(post)
    sqlstr = json.dumps(sql)
    with in_database("default", write=True):
        historico = sepa_log.objects.create(id_branch_id = branch,id_usuario_id = cliente)
        historico.tipo_movimiento = tipo_movimiento
        historico.tabla = tabla
        historico.url = url
        historico.post = poststr
        historico.sql_query = sqlstr
        if origen != None and origen != "None":
            historico.origen = origen
        if(device!=None and device!="None"):
            isDevice = "Si" if device["isDevice"] else "No"
            if SepaDevice.objects.filter(isDevice=isDevice,brand=device["brand"],manufacturer=device["manufacturer"],modelName=device["modelName"],modelId=device["modelId"],designName=device["designName"],productName=device["productName"],deviceYearClass=device["deviceYearClass"],totalMemory=device["totalMemory"],supportedCpuArchitectures=device["supportedCpuArchitectures"][0],osName=device["osName"],osBuildId=device["osBuildId"],osInternalBuildId=device["osInternalBuildId"],osBuildFingerprint=device["osBuildFingerprint"],platformApiLevel=device["platformApiLevel"],deviceName=device["deviceName"]).exists():
                objdevice = SepaDevice.objects.filter(isDevice=isDevice,brand=device["brand"],manufacturer=device["manufacturer"],modelName=device["modelName"],modelId=device["modelId"],designName=device["designName"],productName=device["productName"],deviceYearClass=device["deviceYearClass"],totalMemory=device["totalMemory"],supportedCpuArchitectures=device["supportedCpuArchitectures"][0],osName=device["osName"],osBuildId=device["osBuildId"],osInternalBuildId=device["osInternalBuildId"],osBuildFingerprint=device["osBuildFingerprint"],platformApiLevel=device["platformApiLevel"],deviceName=device["deviceName"])[0]
            else:
                objdevice = SepaDevice.objects.create()
                objdevice.isDevice = isDevice
                objdevice.brand = device["brand"]
                objdevice.manufacturer = device["manufacturer"]
                objdevice.modelName = device["modelName"]
                objdevice.modelId = device["modelId"]
                objdevice.designName = device["designName"]
                objdevice.productName = device["productName"]
                objdevice.deviceYearClass = device["deviceYearClass"]
                objdevice.totalMemory = device["totalMemory"]
                objdevice.supportedCpuArchitectures = device["supportedCpuArchitectures"][0]
                objdevice.osName = device["osName"]
                objdevice.osBuildId = device["osBuildId"]
                objdevice.osInternalBuildId = device["osInternalBuildId"]
                objdevice.osBuildFingerprint = device["osBuildFingerprint"]
                objdevice.platformApiLevel = device["platformApiLevel"]
                objdevice.deviceName = device["deviceName"]
                objdevice.save()
            historico.idDevice = objdevice.Id
        if(connection!=None and connection!="None"):
            if "strength" in connection["details"]:
                strength = connection["details"]["strength"]
            else:
                strength = ""
            if "ssid" in connection["details"]:
                ssid = connection["details"]["ssid"]
            else:
                ssid = ""
            if "ipAddress" in connection["details"]:
                ipAddress = connection["details"]["ipAddress"]
            else:
                ipAddress = ""
            if "subnet" in connection["details"]:
                subnet = connection["details"]["subnet"]
            else:
                subnet = ""
            wifiisConnectionExpensive = "Si" if connection["details"]["isConnectionExpensive"] else "No"
            if(connection["type"]=="wifi"):
                if SepaConnection.objects.filter(connectiontype=connection["type"],detailswifiisConnectionExpensive=wifiisConnectionExpensive,detailswifissid=ssid,detailswifistrength=strength,detailswifiipAddress=ipAddress,detailswifisubnet=subnet).exists():
                    objconnection = SepaConnection.objects.filter(connectiontype=connection["type"],detailswifiisConnectionExpensive=wifiisConnectionExpensive,detailswifissid=ssid,detailswifistrength=strength,detailswifiipAddress=ipAddress,detailswifisubnet=subnet)[0]
                else:
                    objconnection = SepaConnection.objects.create()
                    objconnection.connectiontype = connection["type"]
                    objconnection.detailswifissid = ssid
                    objconnection.detailswifistrength = strength
                    objconnection.detailswifiipAddress = ipAddress
                    objconnection.detailswifisubnet = subnet
                    objconnection.detailswifiisConnectionExpensive = wifiisConnectionExpensive
                    objconnection.save()
            else:
                objconnection = SepaConnection.objects.create()
                objconnection.connectiontype = connection["type"]
                objconnection.save()
            historico.idConnection = objconnection.Id
        historico.save()

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]
