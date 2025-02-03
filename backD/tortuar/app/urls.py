# urls.py

from django.urls import path
from .views import  CustomLoginView,CustomEstado
from . import views
from .views import create_siniestro, get_siniestro, get_poliza, get_Vehiculo, get_Estado, get_Tipo,get_siniestro_id, tipoSiniestro, createVehiculo, getPatente, getMarca, getModelo, DireccionesView, recibir_direcciones, obtenerVehiculo
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
schema_view = get_schema_view(
    openapi.Info(
        title="Tu API",
        default_version='v1',
        description="Documentación de la API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@tuapi.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [ 
    path('login/', CustomLoginView.as_view(), name='login'),  # Usa CustomLoginView para manejar el inicio de sesión
    path('patente',CustomEstado.as_view(),name='patente'),
    path('siniestro/', views.create_siniestro, name='create_siniestro'),
    path('siniestro/<int:user_id>/', get_siniestro, name='get_siniestro'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('poliza/<int:user_id>/', get_poliza, name='get_poliza'),
    path('vehiculo/<int:id>/', get_Vehiculo, name='get_Vehiculo'),
    path('estado/<int:id>/', get_Estado, name='get_Estado'),
    path('tipo/<int:id>/', get_Tipo, name='get_Tipo'),
    path('siniestroo/<int:siniestro_id>/', get_siniestro_id, name='get_siniestro_id'),
    path('siniestroTipo/',tipoSiniestro , name='verTipo'),
    path('vehiculoTercero/',createVehiculo , name='createVehiculo'),
    path('patenteTercero',getPatente , name='getPatente'),
    path('marcaTercero',getMarca , name='getMarca'),
    path('modeloTercero/<int:marca_id>',getModelo , name='getModelo'),
    path('direcciones/<int:user_id>/', DireccionesView.as_view(), name='direcciones'),
    path('recibir-direcciones/', recibir_direcciones, name='recibir_direcciones'),
    path('obtener/<int:id>/', obtenerVehiculo),
]
