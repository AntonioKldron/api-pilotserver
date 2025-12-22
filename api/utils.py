from isapilib.api.models                import BranchAPI, UserAPI
from isapilib.external.connection       import add_conn
from django.core.exceptions             import ObjectDoesNotExist
from rest_framework 				    import status
from django.conf 						import settings
from rest_framework.response 		    import Response
import requests
import json 
import re
import jwt
import os
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'api_sepa_branch_details.json')
def load_credentials():
    """Carga las credenciales desde el archivo JSON."""
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Archivo de credenciales no encontrado en: {CREDENTIALS_FILE}")
        return []
CREDENTIALS_DATA = load_credentials()

def get_branch_db_connection(id_branch):
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

def get_ip_info(request):
    ip_result = ''
    geolocation_data = "\"No IP information available.\""
    try:
        proxy_header = request.META.get('HTTP_X_FORWARDED_FOR')
        if proxy_header:
            client_ip = proxy_header.split(',')[0].strip()
        else:
            client_ip = request.META.get('REMOTE_ADDR')
        ip_result = client_ip
        origin_key = request.META.get('HTTP_ORIGIN')
        if origin_key is None:
            origin_key = client_ip
        api_url = f"https://ipinfo.io/{client_ip}/json"
        response = requests.get(api_url)
        if response.status_code == 200:
            geolocation_data = response.json()
        if isinstance(geolocation_data, str):
            formatted_data = json.dumps(geolocation_data)
        else:
            formatted_data = json.dumps(geolocation_data)
        ip_result = f'{{"{origin_key}":{formatted_data}}}'
    except Exception:
        ip_result = 'No fue posible obtener la información de la IP'
    return ip_result

def validar_token(app_tk):
	try:
		status = False
		m = re.search('(Bearer)(\s)(.*)', app_tk)
		app_tk = m.group(3)
		# user = Token.objects.get(key=app_tk).user
		user = jwt.decode(app_tk, settings.SECRET_KEY, algorithms="HS256")
		if(user != False):
			status = True
			message = 'Credenciales validas.'
	except Exception as e:
		message = 'El token no es valido o ya caduco, vuelve a iniciar sesión'
	return {'valid': status, 'message': message}

def check_token(token):
	tokenValido = None
	statusResponse = status.HTTP_401_UNAUTHORIZED
	try:
		tokenValido = validar_token(token)
		if tokenValido['valid'] != False:
			tokenValido = True
			statusResponse = status.HTTP_200_OK
	except Exception as e:
		tokenValido = False
		print(e)
		statusResponse = status.HTTP_401_UNAUTHORIZED
	return Response({'token_valido' : tokenValido}, statusResponse)

def getUser_token(req):
	try:
		if isinstance(req, str):
			app_tk = req
		else:
			app_tk = req.META["HTTP_AUTHORIZATION"]
		m = re.search('(Bearer)(\s)(.*)', app_tk)
		app_tk = m.group(3)
		user = jwt.decode(app_tk, settings.SECRET_KEY, algorithms="HS256")
		return user
	except Exception as e:
		return False

def get_token_pilot(username, password):
	token = ''
	try:
		responsePilot = requests.get(f'https://api.pilotsolution.net/v1/users/auth.php?username={username}&password={password}')
		result = responsePilot.json()
		token = result['result']['entitydata']
	except:
		token = 'NA'
	return token

def error_pilot_integracion(username, password, id_pilot, mensaje_error):
		responsePilot = requests.get(f'https://api.pilotsolution.net/v1/users/auth.php?username={username}&password={password}')
		if responsePilot:
			result = responsePilot.json()
			params = {
				"data": {
					"id": id_pilot,
					"status_code": "error_integracion"
				},
				"header": {
					"FlowName": "sales_change_status",
					"SequenceId": 2,
					"TimeStamp": 1248377,
					"TrackingId": "55A6BCD4-0857-4A86-85FB-09A228B641B4",
					"access_token": result['result']['entitydata']
				}
			}
			responsePilot = requests.post('https://api.pilotsolution.net/v1/sales/change_status.php', json=params)
			params = {
				"data": {
					"sale_id": id_pilot,
					"comment": mensaje_error
				},
				"header": {
					"FlowName": "sale_comment",
					"SequenceId": 2,
					"TimeStamp": 1248377,
					"TrackingId": "55A6BCD4-0857-4A86-85FB-09A228B641B4",
					"access_token": result['result']['entitydata']
				}
			}
			responsePilot = requests.post('https://api.pilotsolution.net/v1/sales/comments/create.php', json=params)

def get_sale_details_pilot(id_branch, pilot_id):
	pilot = {}
	if isinstance(id_branch, dict):
		pilot = id_branch
	else:
		User_Api = UserAPI.objects.get(branch=id_branch)
		pilot['username'] = User_Api.username
		pilot['password'] = User_Api.password
	token = get_token_pilot(pilot['username'], pilot['password'])
	params = {
		"data": {
			"id": pilot_id
		},
		"header": {
			"FlowName": "sales_read",
			"SequenceId": 2,
			"TimeStamp": 1248377,
			"TrackingId": "55A6BCD4-0857-4A86-85FB-09A228B641B4",
			"access_token": token
		}
	}
	responsePilot = requests.post('https://api.pilotsolution.net/v1/sales/read.php', json=params)
	return responsePilot.json()

def get_credentials_by_header(req):
    username = req.GET.get('username', 'api.intelisis@myworkplace.com.ar')
    credentials = next(
        (cred for cred in CREDENTIALS_DATA if cred['username'] == username), 
        [] # Retorna [] si no encuentra ninguna coincidencia
    )
    return credentials
 
def validaciones_webhook(request):
		mensaje_error = ''
		status_response = status.HTTP_200_OK
		response = {}
		valid = True
		user = getUser_token(request)
		if user == False:
				mensaje_error += 'Pilot: Token no válido\n'
				response = {'detail':[],'status':'error', 'code':401,'message':mensaje_error}
				status_response = status.HTTP_401_UNAUTHORIZED
				valid = False
		# Se obtienen los datos del usuario que llega por la url
		credentials = get_credentials_by_header(request)
		
		if credentials == []:
			response = {'Instancia no encontrada para el username proporcionado'}
			status_response = status.HTTP_400_BAD_REQUEST
		else:
			username = credentials.username
			password = credentials.password

		ip = get_ip_info(request)
		
		if 'topic' in request.data:
				topic=request.data['topic']
		else:
			mensaje_error += 'Pilot: topic faltante\n'
			response = {'detail':[],'status':'error', 'code':400,'message':mensaje_error}
			status_response = status.HTTP_400_BAD_REQUEST
			valid = False
		if 'event' in request.data:
				event=request.data['event']
		else:
			mensaje_error += 'Pilot: event faltante\n'
			response = {'detail':[],'status':'error', 'code':400,'message':mensaje_error}
			status_response = status.HTTP_400_BAD_REQUEST
			valid = False
		if 'id' in request.data:
				id_pilot=request.data['id']
		else:
			mensaje_error += 'Pilot: id faltante\n'
			response = {'detail':[],'status':'error', 'code':400,'message':mensaje_error}
			status_response = status.HTTP_400_BAD_REQUEST
			valid = False
		if topic != 'sales':
			mensaje_error += "Pilot: topic distinto de 'sales'\n"
			response = {'detail':[],'status':'error', 'code':400,'message':mensaje_error}
			status_response = status.HTTP_400_BAD_REQUEST
			valid = False
		if event != 'create':
			mensaje_error += "Pilot: event distinto de 'create'\n"
			response = {'detail':[],'status':'error', 'code':400,'message':mensaje_error}
			status_response = status.HTTP_400_BAD_REQUEST
			valid = False
		if sale_validate(str(id_pilot)) == False:
			mensaje_error += 'Pilot: id en formato no válido\n'
			response = {'detail':[],'status':'error', 'code':400,'message':mensaje_error}
			status_response = status.HTTP_400_BAD_REQUEST
			valid = False
		token = get_token_pilot(username, password)

		if token == 'NA':
			mensaje_error += 'Pilot: No fue posible obtener el token de Pilot\n'
			response = {'detail': [], 'status':'error', 'code':401, 'message': mensaje_error}
			status_response = status.HTTP_400_BAD_REQUEST
			valid = False
		
		return {
				'mensaje_error': 	mensaje_error, 
				'response': 		response, 
				'status_response': 	status_response, 
				'valid': 			valid,
				'id_pilot': 		id_pilot,
				'event': 			event,
				'topic': 			topic,
				'ip': 				ip,
				'username':			username,
				'pass': 			password,
				'token':			token
				}
  
def sale_validate(id):
	UUID_PATTERN = re.compile(r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$', re.IGNORECASE)
	if UUID_PATTERN.match(id):
		return True
	else:
		return False

"""
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
"""