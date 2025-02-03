# app/serializers.py

from rest_framework import serializers
from .models import Siniestro, ChoqueObjeto, ChoquePersona, ChoqueVehiculo, Robo, RoboParcial, Incendio,Poliza, Vehiculo, EstadoPoliza,Tipo, Persona, TipoSiniestroEnum, Modelo, Marca, Uso, Direccion

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

class EstadoPolizaSerializer(serializers.Serializer):
    patente = serializers.CharField(required=True)

class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ['nombre', 'apellido', 'dni']  # Solo los campos necesarios para el titular y conductor

class VehiculoSiniestroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = ['patente']  # Solo el campo necesario para el vehículo

class ChoqueVehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChoqueVehiculo
        fields = ['datos_vehiculo_tercero', 'tercero', 'vehiculo_tercero']


class ChoquePersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChoquePersona
        fields = [ 'persona_chocada', 'numero_denuncia']

class ChoqueObjetoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChoqueObjeto
        fields = [ 'numero_denuncia', 'condicion_climatica']

class RoboSerializer(serializers.ModelSerializer):
    class Meta:
        model = Robo
        fields = [ 'numero_denuncia']

class RoboParcialSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoboParcial
        fields = [ 'numero_denuncia', 'pertenencias_robadas']

class IncendioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incendio
        fields = ['numero_informe']

class SiniestroSerializer(serializers.ModelSerializer):
    choque_vehiculo = ChoqueVehiculoSerializer(read_only=True)
    choque_persona = ChoquePersonaSerializer(read_only=True)
    choque_objeto = ChoqueObjetoSerializer(read_only=True)
    robo = RoboSerializer(read_only=True)
    robo_parcial = RoboParcialSerializer(read_only=True)
    incendio = IncendioSerializer(read_only=True)
    titular = PersonaSerializer(read_only=True)
    conductor = PersonaSerializer(read_only=True)
    vehiculo = VehiculoSiniestroSerializer(read_only=True)

    class Meta:
        model = Siniestro
        fields = [
            'id', 'datos_vehiculo', 'descripcion', 'fecha_hora',
            'tipo_siniestro', 'direccion', 'vehiculo', 'titular', 'conductor',
            'choque_vehiculo', 'choque_persona', 'choque_objeto', 'robo', 'robo_parcial', 'incendio'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        tipo = TipoSiniestroEnum(instance.tipo_siniestro)
        
        # Verificación de existencia antes de asignar al diccionario de representación
        if tipo == TipoSiniestroEnum.VEHICULO and hasattr(instance, 'choquevehiculo'):
            representation['choque_vehiculo'] = ChoqueVehiculoSerializer(instance.choquevehiculo).data
        else:
            representation.pop('choque_vehiculo', None)

        if tipo == TipoSiniestroEnum.PERSONA and hasattr(instance, 'choquepersona'):
            representation['choque_persona'] = ChoquePersonaSerializer(instance.choquepersona).data
        else:
            representation.pop('choque_persona', None)

        if tipo == TipoSiniestroEnum.OBJETO and hasattr(instance, 'choqueobjeto'):
            representation['choque_objeto'] = ChoqueObjetoSerializer(instance.choqueobjeto).data
        else:
            representation.pop('choque_objeto', None)

        if tipo == TipoSiniestroEnum.ROBO and hasattr(instance, 'robo'):
            representation['robo'] = RoboSerializer(instance.robo).data
        else:
            representation.pop('robo', None)

        if tipo == TipoSiniestroEnum.ROBO_PARCIAL and hasattr(instance, 'roboparcial'):
            representation['robo_parcial'] = RoboParcialSerializer(instance.roboparcial).data
        else:
            representation.pop('robo_parcial', None)

        if tipo == TipoSiniestroEnum.INCENDIO and hasattr(instance, 'incendio'):
            representation['incendio'] = IncendioSerializer(instance.incendio).data
        else:
            representation.pop('incendio', None)

        return representation

class EstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoPoliza
        fields = '__all__'  # Incluye todos los campos del modelo junto con 'patente'

class TipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tipo
        fields = '__all__'

class VehiculoSerializer(serializers.ModelSerializer):
    tipo = TipoSerializer()  # Usa el serializer anidado

    class Meta:
        model = Vehiculo
        fields = ['id', 'anio', 'color', 'numero_chasis', 'numero_motor', 'patente', 'tipo', 'uso', 'modelo', 'titular']


class TipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tipo
        fields = '__all__'  

class PolizaSerializer(serializers.ModelSerializer):
    estado_poliza = EstadoSerializer(source='estado')  # Make sure 'estado' is the correct field name
    vehiculo = VehiculoSerializer()  # Include the full vehicle data
    class Meta:
        model = Poliza
        fields = '__all__'

class SiniestroCreateSerializer(serializers.ModelSerializer):
    titular = serializers.PrimaryKeyRelatedField(queryset=Persona.objects.all())
    conductor = serializers.PrimaryKeyRelatedField(queryset=Persona.objects.all())
    vehiculo = serializers.PrimaryKeyRelatedField(queryset=Vehiculo.objects.all())

    class Meta:
        model = Siniestro
        fields = [
            'datos_vehiculo', 'descripcion', 'fecha_hora',
            'tipo_siniestro', 'direccion', 'vehiculo', 'titular', 'conductor'
        ]

    def create(self, validated_data):
        # Extraer los campos anidados para tipos de siniestros específicos, si existen en la data
        tipo_siniestro = validated_data.get('tipo_siniestro')
        siniestro = Siniestro.objects.create(**validated_data)

        # Lógica para crear siniestros específicos, solo si los datos anidados están presentes
        if tipo_siniestro == TipoSiniestroEnum.VEHICULO and 'choque_vehiculo' in self.initial_data:
            ChoqueVehiculo.objects.create(siniestro=siniestro, **self.initial_data['choque_vehiculo'])
        elif tipo_siniestro == TipoSiniestroEnum.PERSONA and 'choque_persona' in self.initial_data:
            ChoquePersona.objects.create(siniestro=siniestro, **self.initial_data['choque_persona'])
        elif tipo_siniestro == TipoSiniestroEnum.OBJETO and 'choque_objeto' in self.initial_data:
            ChoqueObjeto.objects.create(siniestro=siniestro, **self.initial_data['choque_objeto'])
        elif tipo_siniestro == TipoSiniestroEnum.ROBO and 'robo' in self.initial_data:
            Robo.objects.create(siniestro=siniestro, **self.initial_data['robo'])
        elif tipo_siniestro == TipoSiniestroEnum.ROBO_PARCIAL and 'robo_parcial' in self.initial_data:
            RoboParcial.objects.create(siniestro=siniestro, **self.initial_data['robo_parcial'])
        elif tipo_siniestro == TipoSiniestroEnum.INCENDIO and 'incendio' in self.initial_data:
            Incendio.objects.create(siniestro=siniestro, **self.initial_data['incendio'])

        return siniestro



class ModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modelo
        fields = ['id', 'nombre']  # Incluye los campos que deseas exponer

class MarcaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Marca
        fields = ['id', 'nombre']  # Incluye el campo 'modelos'

class VehiculoCreateSerializer(serializers.ModelSerializer):
    tipo = serializers.PrimaryKeyRelatedField(queryset=Tipo.objects.all())  # Solo acepta el ID
    uso = serializers.PrimaryKeyRelatedField(queryset=Uso.objects.all(), required=False, allow_null=True)
    modelo = serializers.PrimaryKeyRelatedField(queryset=Modelo.objects.all(), required=False, allow_null=True)
    titular = serializers.PrimaryKeyRelatedField(queryset=Persona.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Vehiculo
        fields = ['anio', 'color', 'numero_chasis', 'numero_motor', 'patente', 'tipo', 'uso', 'modelo', 'titular']

class DireccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direccion
        fields = ['calle', 'numero']