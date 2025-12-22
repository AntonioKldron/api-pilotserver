from django.urls import path
from .views import *

urlpatterns = [
    # path('', include(router.urls)), # Eliminado si no se usa
    path('webhookpilot/',webHookPilot.as_view(),name='webhook'),
]