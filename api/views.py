from dynamic_db_router 						import in_database
from rest_framework_simplejwt.serializers 	import TokenObtainPairSerializer
from rest_framework_simplejwt.views 		import TokenObtainPairView
from rest_framework 						import status
from rest_framework.views 					import APIView, View
from rest_framework_simplejwt.tokens 		import RefreshToken
from rest_framework.response 				import Response
from rest_framework.decorators 				import action,api_view
from django.contrib.auth.hashers 			import check_password
from django.contrib.auth 					import authenticate, login
from django.http 							import QueryDict
from django.shortcuts 						import render, redirect
from django.conf 							import settings
import re
import jwt
import requests
from sepa.views 							import conectarapiintelisis, loggeractions
from sepa.models 							import sepa_branch_details, sepa_log
from .models 								import pilot
from isapilib.api.models					import BranchAPI,UserAPI

# ================================================================================================
# 										API
# ================================================================================================

class _token(APIView):
	# todo unir las dos funciones de validar token en una sola
	# Valida token bearer devolviendo mensaje y bool
	def validar(app_tk):
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

	# Valida token devolviendo solo bool
	def check(token):
		tokenValido = None
		statusResponse = status.HTTP_401_UNAUTHORIZED
		try:
			tokenValido = _token.validar(token)
			if tokenValido['valid'] != False:
				tokenValido = True
				statusResponse = status.HTTP_200_OK
		except Exception as e:
			tokenValido = False
			print(e)
			statusResponse = status.HTTP_401_UNAUTHORIZED
		return Response({'token_valido' : tokenValido}, statusResponse)
	# Devuelve el usuario al que corresponde un token
	def getUser(req):
		try:
			if isinstance(req, str):
				app_tk = req
			else:
				app_tk = req.META["HTTP_AUTHORIZATION"]
			m = re.search('(Bearer)(\s)(.*)', app_tk)
			app_tk = m.group(3)
			# user = Token.objects.get(key=app_tk).user
			user = jwt.decode(app_tk, settings.SECRET_KEY, algorithms="HS256")
			return user
		except Exception as e:
			return False
	# Solicitudes para check o validar
	@action(detail=True, methods=['POST'])
	def post(self, request, format=None):
		action = request.POST['action']
		token = request.POST['token']
		if action == 'check':
			resp = _token.check(token)
		elif action == 'validar':
			statusResponse = status.HTTP_200_OK
			try:
				tokenValido = _token.validar(token)
				if tokenValido != False:
					tokenValido = True
			except Exception as e:
				tokenValido = False
				statusResponse = status.HTTP_400_BAD_REQUEST
				print('_token Post:')
				print(e)
			return Response({'token_valido' : tokenValido}, status = statusResponse)
		else:
			resp = False
		return resp

# Venta Pilot cuando llega por la integracion
class webhook(APIView):
	def getIpInfo(request):
		ip = ''
		try:
			origin = ""
			data_ip = "\"Sin información de la IP.\""
			x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
			origin = request.META.get('HTTP_ORIGIN')

			if x_forwarded_for:
				ip = x_forwarded_for.split(',')[0]
			else:
				ip = request.META.get('REMOTE_ADDR')
			url = "https://ipinfo.io/" + ip + "/json"
			response = requests.get(url)
			if origin == None:
				origin = ip
			if response:
				data_ip = response.json()
			ip = "{"+f"\"{origin}\":{data_ip}"+"}"
		except:
			ip = 'No fue posible obtener la información de la IP'
		return ip
	
	def validaciones(request):
		# validar token de llegada -> request
		mensaje_error = ''
		status_response = status.HTTP_200_OK
		response = {}
		valid = True
		user = _token.getUser(request)
		if user == False:
				mensaje_error += 'Pilot: Token no válido\n'
				response = {'detail':[],'status':'error', 'code':401,'message':mensaje_error}
				status_response = status.HTTP_401_UNAUTHORIZED
				valid = False
		# Se obtienen los datos del usuario que llega por la url
		credentials = sale.getCredentialsByHeader(request)
		
		if credentials == []:
			response = {'Instancia no encontrada para el username proporcionado'}
			status_response = status.HTTP_400_BAD_REQUEST
		else:
			username = credentials.username
			password = credentials.password

		ip = webhook.getIpInfo(request)
		
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
		if sale.validate(str(id_pilot)) == False:
			mensaje_error += 'Pilot: id en formato no válido\n'
			response = {'detail':[],'status':'error', 'code':400,'message':mensaje_error}
			status_response = status.HTTP_400_BAD_REQUEST
			valid = False
		token = sale.getToken(username, password)

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

	@action(detail=True, methods=['POST'])
	def post(self, request, format=None):
		default_branch = 310#219
		ip = None
		try:
			venta = {}
			status_response = status.HTTP_200_OK

			resp = webhook.validaciones(request)
			
			mensaje_error	= 	resp['mensaje_error']
			response		= 	resp['response']
			status_response	= 	resp['status_response']
			valid			= 	resp['valid']
			id_pilot		= 	resp['id_pilot']
			event			= 	resp['event']
			topic			= 	resp['topic']
			ip				= 	resp['ip']
			username		= 	resp['username']
			password		= 	resp['pass']
			
			if(valid == False):
				sale.errorIntegracion(username, password, id_pilot, mensaje_error)
				loggeractions(2,default_branch,"PilotWebhook","pilot",None,None,request.data,"webhookpilot/",response)
				return Response(response,status=status_response)

			datos = []
			datos.append({'topic': topic, 'event': event, 'id':id_pilot})
			response = {'detail': datos, 'status':'success', 'code':200, 'message':'Datos recibidos correctamente en el webhook'}
			# Obtiene el json de la venta que se esta procesando
			responsePilot = sale.read({'username': username, 'password': password}, id_pilot)

			if responsePilot['result']['status'] != 'success':
				mensaje_error += 'Pilot: ID Pilot no válido\n'
				valid = False
				response = {'detail': [], 'status':'error', 'code':400, 'message':mensaje_error}
				status_response = status.HTTP_400_BAD_REQUEST
			elif 'code' not in responsePilot['result']['entitydata']['branch']:
				mensaje_error += 'Pilot: owner_branch_code no válido en la venta de pilot\n'
				valid = False
				response = {'detail': [], 'status':'error', 'code':400, 'message':mensaje_error}
				status_response = status.HTTP_400_BAD_REQUEST
			
			if(valid == False):
				sale.errorIntegracion(username, password, id_pilot, mensaje_error)
				loggeractions(2,default_branch,"PilotWebhook","pilot",None,None,request.data,"webhookpilot/",response)
				return Response(response,status=status_response)

			branch_code = responsePilot['result']['entitydata']['branch']['code']
			
			if 1 in range(0,len(branch_code.split('-'))):
				sucursal_int = branch_code.split('-')[1]
			else:
				sucursal_int = BranchAPI.objects.get(gwmbac=branch_code)
				sucursal_int = sucursal_int.id_intelisis
			# Se almacena el branch_id para que quede registrado si falla la conexion con la bd
			tamp_branch = BranchAPI.objects.get(gwmbac=branch_code)
			default_branch = tamp_branch.id 

			venta = request.data
			if isinstance(venta, QueryDict):
				venta = venta.dict()

			venta['sucursal'] =  sucursal_int

			with in_database("default"):
				if BranchAPI.objects.filter(gwmbac=branch_code).exists() != True:
					mensaje_error += 'Intelisis: la sucursal no existe\n'
					valid = False
					response = {'data':[], 'status': '0', 'message':mensaje_error}
				if valid == True:
					default_branch = BranchAPI.objects.get(gwmbac=branch_code)
					default_branch = default_branch.id
					# Inicia la ejecucion del procedimiento webhook
					response = sale.execute(venta, default_branch)

			if(valid == False):
				sale.errorIntegracion(username, password, id_pilot, mensaje_error)
			loggeractions(2,response['branch_id'],"PilotWebhook","pilot",None,None,venta,"webhookpilot/",response['info'],ip)
			return Response(response,status=status.HTTP_200_OK)

		except Exception as e:
			msj = 'Ocurrio un error al conectar con la base de datos' if 'SQL Server' in str(e) else str(e) 
			response = {'detail':[],'status':'error', 'code':400,'message':msj}
			loggeractions(2,default_branch,"PilotWebhook","pilot",None,None,venta,"webhookpilot/",response,ip)
			return Response(response,status=status.HTTP_400_BAD_REQUEST)

# Venta Pilot de forma manual
class executeGuid(APIView):
	#todo Pantalla en donde soporte va a ejecutar guid de forma manual
	@action(detail=True, methods=['GET'])
	def get(self, request):
		return render(request, 'pilot/executeGuid.html')
	# todo Metodos para que se realice la ejecucion de la venta

# Log del api webhook 
class logWebhook(APIView):
	# Carga la vista del log del webhook, trata todas las sucursales
	@action(detail=True, methods=['GET'])
	def get(self, request):
		response = {}
		response["code_enviroment"] = settings.CODE_ENVIROMENT
		return render(request, 'pilot/logPilot.html', response)
	
	# Obtiene los registros del logWebhook en base a un id especifico
	@action(detail=True, methods=['POST'])
	def post(self, request, format=None):
		id_sucursal = request.POST['id'] if 'id' in request.POST else -1
		response = sucursal.getLog(id_sucursal)
		return Response(response,status=status.HTTP_200_OK)

class checkConnections(APIView):
	# En base al usuario Pilot que llega indica las configuraciones para realizar la conexion con Pilot desde el Api 
	@action(detail=True, methods=['POST'])
	def post(self, request, format=None):
		response        = {}
		status_response = status.HTTP_200_OK
		detail          = []
		credentials     = []
		code = 200
		try:
			username    = ""
			password    = ""
			message     = ""
			branch      = ""
			token_valid = _token.validar(request.META["HTTP_AUTHORIZATION"])
			credentials = sale.getCredentialsByHeader(request)
			if token_valid['valid'] != True:
				code    = 401
				message = 'Acceso denegado'
				status_response = status.HTTP_401_UNAUTHORIZED	
			elif credentials == []:
				code    = 404
				message = 'Instancia no encontrada para el username proporcionado'
				status_response = status.HTTP_404_NOT_FOUND
			else:
				username      = credentials.username
				password      = credentials.password
				branch        = credentials.branch_id
				responsePilot = requests.get(f'https://api.pilotsolution.net/v1/users/auth.php?username={username}&password={password}')
				if responsePilot:
					detail  = responsePilot.json()
					message = 'Token obtenido correctamente.'
				else:
					message = 'Login fallido.'
		except Exception as e:
			status_response = status.HTTP_500_INTERNAL_SERVER_ERROR
			message = str(e)
		finally:
			finalStatus = 'Success' if code == 200 else 'Error'
			detail   = {'credentials':{'username': username, 'password': password, 'branch_id': branch}, 'pilot': detail}
			response = {'detail':detail if code == 200 else '','status':finalStatus, 'code':code,'message':message}
			return Response(response, status=status_response)

class checkConnectionsDB(APIView):
	# Devuelve la vista de la checkConnections para Pilot
	@action(detail=True, methods=['GET'])
	def get(self, request):
		response = {}
		superUser = False
		if 'sup' in request.GET:
			tkn = _token.getUser('Bearer '+request.GET['sup'])
			usr = UserAPI.objects.get(id=tkn['user_id'])
			superUser = usr.is_superuser
		response["data"] = BranchAPI.objects.filter(gwmbac__in=['M3037','M3037B','M2695','M1027','M1777','M2079','M2078','M2017','M2688','M1509','M1059','M1511','M3101','M2046','M2334','M2268','M2043','M2047','M3787','M2453'])
		response["code_enviroment"] = settings.CODE_ENVIROMENT
		response["super"] = superUser
		archivo = 'pilot/checkConnectionsDB.html'
		return render(request, archivo, response)
	
	# Recibe id_sucursal y prueba la conexion
	@action(detail=True, methods=['POST'])
	def post(self, request, format=None):
		response = sucursal.checkConnection(request.META["HTTP_AUTHORIZATION"], request.POST["sucursal"], request.POST["tiempo_espera"])
		statusResponse = status.HTTP_200_OK
		return Response(response, status=statusResponse)

class infoSucursal(APIView):
	@action(detail=True, methods=['GET'])
	def get(self, request):
		return Response(sucursal.getInfo(request.GET['id']))

class vehicle():
	@api_view(('GET',))
	def getVehicleHistory(request):
		status = False
		resp = {}
		resp['historico'] = ''
		statusActualPilot = ''
		vehicleGuid = ''
		try:
			token_valid = _token.validar(request.META["HTTP_AUTHORIZATION"])
			if token_valid['valid'] == True:
				regex_guid = r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$'
				regex_vin = r'^[A-HJ-NPR-Z0-9]{17}$'
				idVehicle = request.GET['id']
				branch = BranchAPI.objects.get(id=request.GET['branch'])
				branch = branch.id

				if re.match(regex_guid, idVehicle):
					vehicleData = vehicle.readGuid(idVehicle, branch)
					vehicleData = vehicleData['data']['result']
					vehicleGuid = idVehicle
				elif re.match(regex_vin, idVehicle):
					data = vehicle.readVin(idVehicle, branch)
					vehicleData = data['data'][0]
					vehicleGuid = data['data'][0]['id']
				else:
					return Response(data = {'error': True, 'message': 'Identificador del vehiculo invalido', 'data': {}})
				statusActualPilot = vehicleData['entitydata']['availability_status']['name']
				external_db = conectarapiintelisis(branch)
				resp = pilot.objects.getVehicleHistory(external_db, vehicleGuid)

				status = True
			else:
				status = False
				resp['historico'] = 'Token no valido.'

		except Exception as e :
			print(str(e))
			if str(e) == "'HTTP_AUTHORIZATION'":
				resp['historico'] = 'Token invalido'
			elif(str(e) == "'entitydata'"):
				resp['historico'] = 'No se encontraron registros '
			else:
				resp['historico'] = 'Ocurrió un error al consultar el historico de la venta.'
			
		data = {'status': status, 'data': resp['historico'], 'statusIntelisis': resp['statusIntelisis'], 'statusPilot': statusActualPilot}
		return Response(data)

	@api_view(('GET',))
	def read(request):
		try:
			idVehicle = request.GET['id']
			branch = BranchAPI.objects.get(id=request.GET['branch'])
			regex_guid = r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$'
			regex_vin = r'^[A-HJ-NPR-Z0-9]{17}$'
			if re.match(regex_guid, idVehicle):
				data = vehicle.readGuid(idVehicle, branch)
			elif re.match(regex_vin, idVehicle):
				data = vehicle.readVin(idVehicle, branch)
			else:
				data = {'error': True, 'message': 'Identificador del vehiculo invalido', 'data': {}}
		except	Exception as e : 
				data = {'error': True, 'message': 'Ocurrio un error al procesar la solicitud', 'data': {}}
				print(str(e))

		return Response(data)

	def readVin(vin, branch):
		user = sepa_branch_details.objects.filter(branch_id=branch).first()
		username = user.username
		password = user.password
		responsePilot = requests.get(f'https://api.pilotsolution.net/v1/users/auth.php?username={username}&password={password}')
		if responsePilot:
			result = responsePilot.json()
			params = {
					"data": {
						"limit": 25,
						"page": 1,
						"filters": [
									{
										"field": "vin",
										"operation": "=",
										"value": vin
									}
								]
					},
					"header": {
						"FlowName": "stock_list",
						"SequenceId": 2,
						"TimeStamp": 1248377,
						"TrackingId": "55A6BCD4-0857-4A86-85FB-09A228B641B4",
						"access_token": result['result']['entitydata']
					}
				}
			responsePilot = requests.post('https://api.pilotsolution.net/v1/stock/list.php', json=params)
		return {'error': False, 'message': 'OK', 'data': responsePilot.json()['result']['entitydata']}

	def readGuid(guid, branch):
		user = sepa_branch_details.objects.filter(branch_id=branch).first()
		username = user.username
		password = user.password
		responsePilot = requests.get(f'https://api.pilotsolution.net/v1/users/auth.php?username={username}&password={password}')
		if responsePilot:
			result = responsePilot.json()
			params = {
					"data": {
						"id":guid
					},
					"header": {
						"FlowName": "stock_read",
						"SequenceId": 2,
						"TimeStamp": 1248377,
						"TrackingId": "55A6BCD4-0857-4A86-85FB-09A228B641B4",
						"access_token": result['result']['entitydata']
					}
				}
			responsePilot = requests.post('https://api.pilotsolution.net/v1/stock/read.php', json=params)
		return {'error': False, 'message': 'OK', 'data': responsePilot.json()}

# ================================================================================================
# 										Funcionalidades 
# ================================================================================================

class sucursal(View):
	def getLogWebhook(id_sucursal):
		data = []
		if id_sucursal == -1:
			logs = sepa_log.objects.select_related('id_branch').filter(tipo_movimiento='PilotWebhook').order_by('-id')[:300]
		else:
			logs = sepa_log.objects.select_related('id_branch').filter(tipo_movimiento='PilotWebhook', id_branch = id_sucursal).order_by('-id')[:300]
		logs = reversed(logs)
		for f in logs:
			branch = f.id_branch
			data.append({'id': f.id, 'branch': branch.nombre, 'tipo': f.tipo_movimiento, 'response': f.sql_query, 'data': f.post, 'fecha': f.fecha_creacion.strftime('%d/%m/%Y %I:%M:%S %p'), 'origen': f.origen})
		return data

	def getInfo(id_sucursal):
		external_db = conectarapiintelisis(id_sucursal)
		sucursal = BranchAPI.objects.get(id=id_sucursal)
		response = pilot.objects.getBranchInfo(external_db, sucursal.id_intelisis)
		return response

	def checkConnection(token, id_sucursal, timeOut):
		resp = {}
		try:
			if _token.validar(token) != False :
				#* Se obtienen los datos de conexion de la sucursal
				external_db = conectarapiintelisis(id_sucursal)
				#* Funcion que prueba la conexión con la base de la agencia 
				resp = pilot.objects.testDbConnection(external_db, int(timeOut))
				resp['branch'] = external_db["dbprofiledata"]["NAME"]
			else:
				resp['Estatus'] = False
				resp['Mensaje'] = 'No autorizado'
				resp['tiempo'] = 0
				resp['branch'] = 'NA'
		except Exception :
				resp['Estatus'] = False
				resp['Mensaje'] = 'No autorizado'
				resp['tiempo'] = 0
				resp['branch'] = 'NA'

		#* Estructura la respuesta que se va a enviar
		response = {'status': resp["Estatus"] , 'message':str(resp["Mensaje"]), 'time': resp["tiempo"], 'branch': resp["branch"]}
		return response

	# Obtiene el historico de Pilot en la sucursal que se indica
	def getLog(id_sucursal):
		try:
			data = []
			resp = {}
			data = sucursal.getLogWebhook(id_sucursal)
			if len(data) > 0:
				resp = {'data': data, 'status': 'success', 'message': str(len(data))+' Peticiones registradas.'}
			else:
				resp = {'data': data, 'status': 'success', 'message':'Sin Peticiones registradas.'}
		except:
			resp = {'data': None, 'status': 'error', 'message':'Ocurrio un error al procesar la solicitud.'}
			
		return resp

class sale(APIView):
	@api_view(('GET',))
	def getSalesHistory(request):
		status = False
		resp = {}
		resp['historico'] = ''
		statusActualPilot = ''
		try:
			token_valid = _token.validar(request.META["HTTP_AUTHORIZATION"])
			if token_valid['valid'] == True:
				id_sucursal = request.GET['sucursal']
				idVentaPilot = request.GET['guid']

				external_db = conectarapiintelisis(id_sucursal)
				resp = pilot.objects.getSalesHistory(external_db, idVentaPilot)

				usr = sepa_branch_details.objects.filter(branch_id=id_sucursal).first()

				token = sale.getToken(usr.username, usr.password)
				params = {
					"data": {
						"id": idVentaPilot
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
				responsePilot = responsePilot.json() 
				if responsePilot['result']['status'] == 'success':
					statusActualPilot = responsePilot['result']['entitydata']['status']['name']
				else:
					statusActualPilot = responsePilot['result']['message']
				status = True
			else:
				status = False
				resp['historico'] = 'Token no valido.'

		except Exception as e :
			print('Este es el error al obtener el estatus de una venta')
			print(str(e))
			if str(e) == "'HTTP_AUTHORIZATION'":
				resp['historico'] = 'Token invalido'
			elif(str(e) == "'entitydata'"):
				resp['historico'] = 'No se encontraron registros '
			else:
				resp['historico'] = 'Ocurrió un error al consultar el historico de la venta.'
			
		data = {'status': status, 'data': resp['historico'], 'statusPilot': statusActualPilot}
		return Response(data)


	def execute(data, branch_id):
		response = {}
		external_db=conectarapiintelisis(branch_id)
		folio = pilot.objects.insertLogWebhook(external_db, data)
		response['info'] = {'data': folio, 'status': 'success', 'message':'Datos recibidos correctamente en el webhook'}
		response['branch_id'] = branch_id
		return response

	def validate(id):
		UUID_PATTERN = re.compile(r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$', re.IGNORECASE)
		if UUID_PATTERN.match(id):
			return True
		else:
			return False

	def errorIntegracion(username, password, id_pilot, mensaje_error):
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

	def getCredentialsByHeader(req):
		username = 'api.intelisis@myworkplace.com.ar'
		if 'username' in req.GET:
			username = req.GET["username"]
		if sepa_branch_details.objects.filter(username=username).exists():
			credentials = sepa_branch_details.objects.filter(username=username).first()
		else:
			credentials = []
		return credentials

	@api_view(('GET',))
	def getSale(request):
		try:
			error = False
			message = 'Lectura de la venta exitosa.'
			data_sale = sale.read(request.GET['branch'], request.GET['sale_id'])
		except Exception as e :
			error = True
			message = 'Ocurrio un error al leer la venta en Pilot'
			data_sale = {}
		data = {'error': error, 'message': message, 'data': data_sale}
		return Response(data)

	def read(branch, sale_id):
		# Si entra por webhook ya vienen los datos, si viene por lectura se recuperan de la bd
		usrPilot = {}
		if isinstance(branch, dict):
			usrPilot = branch
		else:
			usr = sepa_branch_details.objects.filter(branch_id=branch).first()
			usrPilot['username'] = usr.username
			usrPilot['password'] = usr.password

		token = sale.getToken(usrPilot['username'], usrPilot['password'])
		params = {
			"data": {
				"id": sale_id
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

	def getToken(username, password):
		token = ''
		try:
			responsePilot = requests.get(f'https://api.pilotsolution.net/v1/users/auth.php?username={username}&password={password}')
			result = responsePilot.json()
			token = result['result']['entitydata']
		except:
			token = 'NA'
		return token
#Login para aplicacion Pilot

class _login(APIView):
	@action(detail=True, methods=["GET"])
	def get(self, request):
		response = {}
		return render(request, "pilot/loginPilot.html", response)		

	@action(detail=True, methods=["POST"])
	def post(self, request, format=None):
		estatus = False
		token = None
		statusCode = status.HTTP_200_OK
		#todo verificar como simplificar la asignacion de la url
		url = ("https://isapi.intelisis-solutions.com/pilot/authJWT/" if settings.CODE_ENVIROMENT == "production" else "http://localhost:8000/pilot/authJWT/")
		try:
			# * Se recuperan los datos que se enviaron por la solicitud
			usuario = request.POST["usuario"]
			password = request.POST["password"]
			# * Verificamos que el usuario si exista
			objUsuario = UserAPI.objects.get(usuario=usuario)

			datos = {"usuario": usuario, "password": password}
			_user = authenticate(request, username=usuario, password=password)
			if _user is not None and check_password(password, objUsuario.password) == True:
				# Redirect to a success page.
				response = requests.post(url, data=datos)
				if response.status_code == 200:
					tokens = response.json()
					access_token = tokens["access_token"]
					token = "Bearer " + access_token
					request.session["token"] = token
					tokenValido = _token.validar(token)
					mensaje = tokenValido['message']
					estatus = tokenValido['valid']
					tipo = objUsuario.is_superuser
				else:
					estatus = False
					mensaje = "Autenticación fallida."
			else:
				estatus = False
				mensaje = "Datos incorrectos1"
		except Exception as e:
			print(e)
			estatus = False
			mensaje = "Datos incorrectos0"
		
		if tipo == 1:
			respuesta = {"status": estatus, "mensaje": mensaje, "token": token, "super": tipo}
		else:
			respuesta = {"status": estatus, "mensaje": mensaje, "token": token}
		return Response(respuesta, status=statusCode)

class log(APIView):
	@action(detail=True, methods=['GET'])
	def get(self, request):
		id_sucursal = request.GET['sucursal']
		external_db = conectarapiintelisis(id_sucursal)
		sucursal = BranchAPI.objects.get(id=id_sucursal)
		response = pilot.objects.getLogSucursal(external_db, sucursal.id_intelisis)            
		return Response({'data': response['data'], 'status': response['status'], 'details': str(response['details'])}, status=status.HTTP_200_OK)
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
	def validate(self, attrs):
		try:
			# The default result (access/refresh tokens)
			data = super(CustomTokenObtainPairSerializer, self).validate(attrs)
			# Custom data you want to include
			data.update({'refresh_token': data['refresh']})
			data.update({'access_token': data['access']})
			data.pop('refresh')
			data.pop('access')
		except Exception as e:
			print(str(e))
		return data
	
class CustomTokenObtainPairView(TokenObtainPairView):
	# Replace the serializer with your custom
	serializer_class = CustomTokenObtainPairSerializer
