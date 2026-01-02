from django.urls import path, include
from rest_framework import routers
from .views import webhook, logWebhook, checkConnections, checkConnectionsDB, log, _login, CustomTokenObtainPairView, _token, infoSucursal, sale, vehicle

router = routers.DefaultRouter()

urlpatterns = [
    ##path('', include(router.urls)),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('webhookpilot/',           webhook.as_view(),                      name='webhook'),
    path('log/',                    logWebhook.as_view(),                   name='log'),
    path('checkConnections/',       checkConnections.as_view(),             name='checkConnections'),
    path('authJWT/',                CustomTokenObtainPairView.as_view(),    name='token_obtain_pair'),
    path('monitor/',                checkConnectionsDB.as_view(),           name='checkConnectionsDB'),
    path('logSucursal/',            log.as_view(),                          name='log'),
    path('loginPilot/',             _login.as_view(),                       name='loginPilot'),
    path('webhookById/',            logWebhook.as_view(),                   name='webhookById'),
    path('validateToken/',          _token().as_view(),                     name='validateToken'),
    path('infoSucursal/',           infoSucursal().as_view(),               name='infoSucursal'),
    path('enviarVenta/',            sale().as_view(),                       name='guid'),
    path('vehicle/read/',           vehicle.read,                           name='readVehicle'),
    path('sale/read/',              sale.getSale,                           name='readSale'),
    path('sale/getSalesHistory/',   sale.getSalesHistory,                   name='getSalesHistory'),
    path('sale/getVehicleHistory/', vehicle.getVehicleHistory,              name='getVehicleHistory')
]