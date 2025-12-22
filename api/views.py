from rest_framework 				import status
from rest_framework.views 			import APIView
from rest_framework.response 		import Response
from django.http 					import QueryDict
from isapilib.api.models 			import BranchAPI, UserAPI
from rest_framework.decorators 		import action,api_view
from .utils							import get_branch_db_connection,get_ip_info,error_pilot_integracion,get_sale_details_pilot,validaciones_webhook


class webHookPilot(APIView):
      
	@action(detail=True, methods=['POST'])
	def post(self, request, format=None):
		default_branch = 310#219
		ip = None
		try:			
			status_response = status.HTTP_200_OK
			resp = validaciones_webhook(request)
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


		except Exception as e:
			msj = 'Ocurrio un error al conectar con la base de datos' if 'SQL Server' in str(e) else str(e) 
			response = {'detail':[],'status':'error', 'code':400,'message':msj}
			return Response(response,status=status.HTTP_400_BAD_REQUEST)

     