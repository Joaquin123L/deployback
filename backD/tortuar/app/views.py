# Importa render para renderizar plantillas HTML
from django.shortcuts import render
import secrets
from django.http import JsonResponse
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
# Importa generics para vistas basadas en clases de Django REST Framework
from rest_framework import generics
# Importa Response para construir respuestas HTTP y status para códigos de estado HTTP
from rest_framework.response import Response
from rest_framework import status
# Importa funciones para autenticar usuarios y manejar el inicio de sesión
from django.contrib.auth import authenticate, login
# Importa el serializador para validar los datos del login
from .serializers import LoginSerializer 
from .serializers import EstadoSerializer , MarcaSerializer, VehiculoCreateSerializer, ModeloSerializer, DireccionSerializer
from .serializers import PolizaSerializer, VehiculoSerializer,EstadoSerializer, TipoSerializer, EstadoPolizaSerializer, SiniestroCreateSerializer
from rest_framework.decorators import api_view
from .models import Poliza, Persona, Vehiculo, EstadoPoliza, Tipo, Marca, Uso, Modelo
from .models import Siniestro, ChoqueObjeto, ChoquePersona, ChoqueVehiculo, Robo, RoboParcial, Incendio, Poliza, InformeHeridos
from .serializers import (
    SiniestroSerializer, ChoqueObjetoSerializer, ChoquePersonaSerializer, 
    ChoqueVehiculoSerializer, RoboSerializer, RoboParcialSerializer, IncendioSerializer
)
from django.views.decorators.csrf import csrf_exempt
from .models import TipoSiniestroEnum
from .libreria import concaten
import requests
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from datetime import timedelta
from django.utils import timezone
from .dtos import SiniestroDTO
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

class CustomLoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Valida los datos de entrada
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extrae los datos del serializer
        username = serializer.validated_data.get("username")
        password = serializer.validated_data.get("password")

        # Autentica al usuario
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Crear un objeto de token para el usuario autenticado
            refresh = RefreshToken.for_user(user)
            
            # Devolver los tokens (access y refresh)
            return Response({
                "message": "Login successful",
                "token": str(refresh.access_token),  # El access token
                "token refresh": str(refresh),  # El refresh token
                "user_id": user.id,
            }, status=status.HTTP_200_OK)
        else:
            # Si las credenciales son incorrectas
            return Response({
                "message": "Invalid credentials"
            }, status=status.HTTP_401_UNAUTHORIZED)

class CustomEstado(generics.GenericAPIView):
    serializer_class = EstadoPolizaSerializer
    permission_classes = [AllowAny]

    # Maneja solicitudes POST para verificar el estado de la póliza
    def post(self, request, *args, **kwargs):
        # Valida los datos enviados usando el serializador
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extrae la patente validada del serializador
        patente = serializer.validated_data.get("patente")

        # Intenta obtener la póliza correspondiente a la patente proporcionada
        try:
            poliza = Poliza.objects.get(vehiculo__patente=patente)
            if poliza.estado.nombre == "Activa":
                # Si la póliza está activa, devuelve una respuesta exitosa
                return Response({"message": "Póliza activa"}, status=status.HTTP_200_OK)
            else:
                # Si la póliza no está activa, devuelve un mensaje de póliza inactiva
                return Response({"message": "Póliza inactiva"}, status=status.HTTP_200_OK)
        except Poliza.DoesNotExist:
            # Si no se encuentra ninguna póliza asociada a la patente, devuelve un error
            return Response({"message": "Póliza no encontrada"}, status=status.HTTP_404_NOT_FOUND)


def obtener_descripcion_herido(dni_herido):
    # Simulamos un archivo JSON con las descripciones
    ambulancia_data = {
        "20345678": "Fractura en el brazo derecho",
        "11223344": "Contusión leve en la pierna izquierda"
    }
    
    return ambulancia_data.get(dni_herido, "Descripción no disponible")

@api_view(['POST'])
@transaction.atomic
def create_siniestro(request):
    try:
        # Validar tipo de siniestro
        tipo_siniestro = request.data.get('tipo_siniestro')
        if not tipo_siniestro:
            return Response(
                {'error': 'El tipo de siniestro es obligatorio.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if tipo_siniestro not in [t.value for t in TipoSiniestroEnum]:
            return Response(
                {
                    'error': 'Tipo de siniestro no válido.',
                    'tipos_validos': [t.value for t in TipoSiniestroEnum]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar el conductor por DNI
        dni_conductor = request.data.get('conductor')
        if not dni_conductor:
            return Response(
                {'error': 'El DNI del conductor es obligatorio.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            conductor = Persona.objects.get(dni=dni_conductor)
        except Persona.DoesNotExist:
            return Response(
                {'error': 'Conductor no encontrado con el DNI proporcionado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar el vehículo por ID
        id_vehiculo = request.data.get('vehiculo')
        if not id_vehiculo:
            return Response(
                {'error': 'El ID del vehículo es obligatorio.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vehiculo = Vehiculo.objects.get(id=id_vehiculo)
        except Vehiculo.DoesNotExist:
            return Response(
                {'error': 'Vehículo no encontrado con el ID proporcionado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener el titular del vehículo
        titular = vehiculo.titular

        # Crear el siniestro principal
        with transaction.atomic():
            siniestro_data = request.data.copy()
            siniestro_data['titular'] = titular.id
            siniestro_data['conductor'] = conductor.id
            siniestro_data['vehiculo'] = vehiculo.id

            # Validar y crear el siniestro principal
            siniestro_serializer = SiniestroCreateSerializer(data=siniestro_data)
            if not siniestro_serializer.is_valid():
                return Response(
                    siniestro_serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            siniestro = siniestro_serializer.save()

            # Procesar los heridos
            heridos = request.data.get('heridos', [])
            for herido_dni in heridos:
                herido_descripcion = obtener_descripcion_herido(herido_dni)

                # Si no se obtiene descripción, se podría considerar un valor predeterminado o manejarlo de otra forma
                if herido_descripcion == "Descripción no disponible":
                    herido_descripcion = None 

                InformeHeridos.objects.create(
                    siniestro=siniestro,
                    herido=herido_dni,
                    descripcion=herido_descripcion
                )

            # Configuración de los manejadores de tipos específicos
            tipo_handlers = {
                TipoSiniestroEnum.OBJETO.value: {
                    'model': ChoqueObjeto,
                    'serializer': ChoqueObjetoSerializer,
                    'data_keys': ['numero_denuncia', 'condicion_climatica']
                },
                TipoSiniestroEnum.PERSONA.value: {
                    'model': ChoquePersona,
                    'serializer': ChoquePersonaSerializer,
                    'data_keys': ['persona_chocada', 'numero_denuncia']
                },
                TipoSiniestroEnum.VEHICULO.value: {
                    'model': ChoqueVehiculo,
                    'serializer': ChoqueVehiculoSerializer,
                    'data_keys': ['datos_vehiculo_tercero', 'tercero', 'vehiculo_tercero']
                },
                TipoSiniestroEnum.ROBO.value: {
                    'model': Robo,
                    'serializer': RoboSerializer,
                    'data_keys': ['numero_denuncia']
                },
                TipoSiniestroEnum.ROBO_PARCIAL.value: {
                    'model': RoboParcial,
                    'serializer': RoboParcialSerializer,
                    'data_keys': ['numero_denuncia', 'pertenencias_robadas']
                },
                TipoSiniestroEnum.INCENDIO.value: {
                    'model': Incendio,
                    'serializer': IncendioSerializer,
                    'data_keys': ['numero_informe']
                }
            }

            handler = tipo_handlers.get(tipo_siniestro)
            if not handler:
                raise ValidationError(f'No hay manejador para el tipo: {tipo_siniestro}')

            # Extraer los datos específicos del tipo
            specific_data = {key: request.data.get(key) for key in handler['data_keys']}

            # Manejo especial para ChoqueVehiculo
            if tipo_siniestro == TipoSiniestroEnum.VEHICULO.value:
                patente_tercero = specific_data.pop('vehiculo_tercero', None)
                if not patente_tercero:
                    return Response(
                        {'error': 'La patente del vehículo tercero es obligatoria.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    vehiculo_tercero_instance = Vehiculo.objects.get(patente=patente_tercero)
                    specific_data['vehiculo_tercero'] = vehiculo_tercero_instance
                except Vehiculo.DoesNotExist:
                    return Response(
                        {'error': f'No se encontró un vehículo con la patente: {patente_tercero}.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Validar campos requeridos
            missing_fields = [key for key in handler['data_keys'] if key not in specific_data or specific_data[key] is None]
            if missing_fields:
                raise ValidationError(f'Faltan campos requeridos para {tipo_siniestro}: {", ".join(missing_fields)}')

            # Crear instancia específica del tipo
            specific_instance = handler['model'].objects.create(
                siniestro=siniestro,
                **specific_data
            )

            # Respuesta final
            response_data = {
                'mensaje': 'Siniestro creado exitosamente',
                'siniestro': siniestro_serializer.data,
                'detalle': handler['serializer'](specific_instance).data
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response(
            {'error': f'Error al crear el siniestro: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['GET'])
def get_siniestro(request, user_id):
    try:
        # Filtrar siniestros por el titular del usuario
        siniestros = Siniestro.objects.filter(titular_id=user_id)

        # Verificar si existen siniestros para el usuario
        if not siniestros.exists():
            return Response({'error': 'No siniestros found for this user'}, status=status.HTTP_404_NOT_FOUND)

        # Crear una lista de DTOs a partir de los siniestros obtenidos
        siniestros_dto = [SiniestroDTO(s.id,s.fecha_hora).to_dict() for s in siniestros]

        # Retornar la respuesta con los datos de los DTOs
        return Response(siniestros_dto, status=status.HTTP_200_OK)

    except Exception as e:
        # Manejar cualquier excepción y devolver un error
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def get_siniestro_id(request, siniestro_id):
    try:
        # Obtener el siniestro con el siniestro_id proporcionado
        siniestro = Siniestro.objects.get(id=siniestro_id)

        # Serializar el siniestro
        serializer = SiniestroSerializer(siniestro)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Siniestro.DoesNotExist:
        # Si no se encuentra el siniestro, se devuelve un error
        return Response({'error': 'Siniestro not found'}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        # Capturamos cualquier otro error y lo devolvemos en la respuesta
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    
@api_view(['GET'])
def get_poliza(request, user_id):
    try:
        # Obtener la persona asociada al user_id
        persona = Persona.objects.get(user_id=user_id)

        # Obtener las pólizas asociadas a los vehículos del usuario (persona), excluyendo 'patente' de select_related
        polizas = Poliza.objects.filter(vehiculo__titular=persona).select_related(
            'vehiculo', 'vehiculo__tipo', 'vehiculo__modelo', 'estado'
        )

        # Si no se encuentran pólizas, devolver un error
        if not polizas.exists():
            return Response({'error': 'No se encontraron pólizas para este usuario'}, status=status.HTTP_404_NOT_FOUND)

        # Crear un diccionario para la respuesta
        poliza_data = []
        for poliza in polizas:
            poliza_info = {
                'numero_poliza': poliza.numero,
                'estado_poliza': poliza.estado.nombre if poliza.estado else 'Desconocido',  # Verificar existencia de estado
                'patente': poliza.vehiculo.patente if poliza.vehiculo.patente else 'Desconocida',  # Ahora accedes directamente sin select_related
                'tipo_vehiculo': poliza.vehiculo.tipo.nombre if poliza.vehiculo.tipo else 'Desconocido',  # Verificar existencia de tipo
                'marca_modelo': f"{poliza.vehiculo.modelo.marca.nombre if poliza.vehiculo.modelo.marca else 'Desconocido'} {poliza.vehiculo.modelo.nombre if poliza.vehiculo.modelo else 'Desconocido'}",
                'fecha_inicio': poliza.fecha_inicio,
                'fecha_fin': poliza.fecha_fin,
                'monto': poliza.monto,
                'tipo_cobertura': poliza.tipo_cobertura.nombre if poliza.tipo_cobertura else 'Desconocido',  # Verificar existencia de tipo de cobertura
                'franquicia': poliza.franquicia if poliza.franquicia else 'No especificada'
            }
            poliza_data.append(poliza_info)

        return Response(poliza_data, status=status.HTTP_200_OK)

    except Persona.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Manejar otros errores
        return Response({'error': f'Error inesperado: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    
@api_view(['GET'])
def get_Vehiculo(request,id):
    try:
        vehiculo = Vehiculo.objects.filter(id=id)


        if not vehiculo.exists():  # .exists() es una forma más eficiente de verificar si hay resultados
            return Response({'error': 'No siniestros found for this user'}, status=status.HTTP_404_NOT_FOUND)

        serializer = VehiculoSerializer(vehiculo, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        # Capturamos cualquier error y lo devolvemos en la respuesta
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def get_Estado(request, id):
    try:
        estado = EstadoPoliza.objects.filter(id=id)

        # Verificar si la consulta devuelve resultados
        if not estado.exists(): 
            return Response({'error': 'No estado found for this id'}, status=status.HTTP_404_NOT_FOUND)

        # Serializar los resultados
        serializer = EstadoSerializer(estado, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        # Capturamos cualquier error y lo devolvemos en la respuesta
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def get_Tipo(request, id):
    try:
        # Corregir el uso de la clase y la consulta
        tipo = Tipo.objects.filter(id=id)

        # Verificar si la consulta devuelve resultados
        if not tipo.exists(): 
            return Response({'error': 'No estado found for this id'}, status=status.HTTP_404_NOT_FOUND)

        # Serializar los resultados
        serializer = TipoSerializer(tipo, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        # Capturamos cualquier error y lo devolvemos en la respuesta
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def tipoSiniestro (request):
    try:
        tipo = TipoSiniestroEnum
        return Response({'tipos': [t.value for t in tipo]}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def createVehiculo(request):
    try:
        # Obtener los datos del vehículo del cuerpo de la solicitud
        data = request.data

        # Mapear los valores de 'tipo' y 'uso' a sus respectivos IDs
        tipo_nombre = data.get('tipo')
        uso_nombre = data.get('uso')

        # Verificar si 'tipo' y 'uso' están en la base de datos
        try:
            tipo_obj = Tipo.objects.get(nombre=tipo_nombre)
            data['tipo'] = tipo_obj.id  # Reemplazar el nombre por el ID
        except Tipo.DoesNotExist:
            return Response({'error': f'Tipo "{tipo_nombre}" no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uso_obj = Uso.objects.get(nombre=uso_nombre)
            data['uso'] = uso_obj.id  # Reemplazar el nombre por el ID
        except Uso.DoesNotExist:
            return Response({'error': f'Uso "{uso_nombre}" no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validar los datos del vehículo
        serializer = VehiculoCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Crear una nueva instancia de Vehiculo
        vehiculo = serializer.save()

        # Serializar el vehículo creado para la respuesta
        response_serializer = VehiculoSerializer(vehiculo)

        return Response({'datos': response_serializer.data}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    
@api_view(['GET'])
# Consultar solo la patente de la tabla vehiculos
def getPatente(request):
    try:
        # Obtener solo las patentes
        patentes = Vehiculo.objects.values('patente')  # Devuelve solo la propiedad 'patente'
        
        # Serializar los resultados
        return Response(patentes, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

#obtener marcas de la tabla Marca
@api_view(['GET'])
def getMarca(request):
    try:
        # Obtener todas las marcas
        marcas = Marca.objects.all()
        
        # Serializar los resultados
        serializer = MarcaSerializer(marcas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
#pasandole una marca obtener los modelos de esa marca
@api_view(['GET'])
def getModelo(request, marca_id):
    try:
        # Obtener los modelos de la marca
        modelos = Modelo.objects.filter(marca=marca_id)
        
        # Serializar los resultados
        serializer = ModeloSerializer(modelos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
#pasando una patente de un vehiculo devuelva un bool para ver si existe o no
@api_view(['POST'])
def getPatente(request):
    try:
        # Obtener la patente del cuerpo de la solicitud
        patente = request.data.get('patente')
        
        # Verificar si la patente existe
        vehiculo = Vehiculo.objects.filter(patente=patente).exists()
        return Response({'existe': vehiculo}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

class DireccionesView(APIView):
    def get(self, request, user_id):
        # Dirección 1 (fija)
        direccion1 = {"calle": "Calle 60", "numero": 1522}
        
        try:
            # Dirección 2 (asociada al usuario)
            persona = Persona.objects.get(id=user_id)
            direccion2 = DireccionSerializer(persona.direccion).data
        except Persona.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Datos a devolver al frontend
        data = {
            "direccion1": direccion1,
            "direccion_usuario": direccion2
        }
        
        # Responder con las direcciones
        return Response(
            {"message": "Direcciones recuperadas correctamente.", "data": data},
            status=status.HTTP_200_OK
        )

@api_view(['POST'])
def recibir_direcciones(request):
    try:
        # Obtener los datos del request
        direccion1 = request.data.get("direccion1")
        direccion_usuario = request.data.get("direccion_usuario")
        
        # Validar que ambas direcciones estén presentes
        if not direccion1 or not direccion_usuario:
            return Response(
                {"error": "Ambas direcciones (direccion1 y direccion_usuario) son obligatorias."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Validar estructura de las direcciones
        if not isinstance(direccion1, dict) or not isinstance(direccion_usuario, dict):
            return Response(
                {"error": "Las direcciones deben ser objetos JSON con 'calle' y 'numero'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if "calle" not in direccion1 or "numero" not in direccion1:
            return Response(
                {"error": "La dirección1 debe contener 'calle' y 'numero'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if "calle" not in direccion_usuario or "numero" not in direccion_usuario:
            return Response(
                {"error": "La direccion_usuario debe contener 'calle' y 'numero'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Procesar las direcciones
        procesadas = {
            "direccion1_procesada": direccion1,
            "direccion_usuario_procesada": direccion_usuario,
        }
        
        return Response(
            {"message": "Direcciones recibidas correctamente.", "data": procesadas},
            status=status.HTTP_200_OK,
        )
    
    except Exception as e:
        # Manejo de errores generales
        return Response(
            {"error": f"Se produjo un error al procesar la solicitud: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
@api_view(['GET'])
def obtenerVehiculo(request, id):
    
    try:
        vehiculo = Vehiculo.objects.get(id=id)
        serializer = VehiculoSerializer(vehiculo)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Vehiculo.DoesNotExist:
        return Response({'error': 'Vehiculo no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    



