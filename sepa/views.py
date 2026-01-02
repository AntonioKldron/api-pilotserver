from rest_framework import viewsets,status
from rest_framework.views import APIView
from rest_framework.response import Response
from isapilib.external.connection       import add_conn

def conectarapiintelisis(sucursal):
    external_db = None
    try:
        Branch_Api = BranchAPI.objects.get(id=id_branch)
        print(Branch_Api)
        User_Api = UserAPI.objects.get(branch=Branch_Api.id)
        print(User_Api)
        external_db = add_conn(User_Api, Branch_Api)
    except ObjectDoesNotExist as e:
        print(f"ERROR: Configuración no encontrada para la sucursal ID {id_branch}. Detalle: {e}")
    except Exception as e:
        print(f"ERROR CRÍTICO DE CONEXIÓN: Falló la conexión a la DB externa. Detalle: {e}")
    return external_db

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
