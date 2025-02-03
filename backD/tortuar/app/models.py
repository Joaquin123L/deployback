from django.db import models
from django.contrib.auth.models import User
from enum import Enum

class Provincia(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=45)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'provincia'

class Localidad(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=45)
    provincia = models.ForeignKey(Provincia, on_delete=models.PROTECT)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'localidad'

class Direccion(models.Model):
    id = models.AutoField(primary_key=True)
    calle = models.CharField(max_length=45)
    numero = models.IntegerField()
    codigo_postal = models.CharField(max_length=45)
    departamento = models.CharField(max_length=45, blank=True, null=True)
    piso = models.IntegerField(blank=True, null=True)
    localidad = models.ForeignKey(Localidad, on_delete=models.PROTECT)
    
    def __str__(self):
        return f"{self.calle} {self.numero}, {self.localidad}"
    
    class Meta:
        db_table = 'direccion'

class Empresa(models.Model):
    id = models.AutoField(primary_key=True)
    cuil = models.BigIntegerField(unique=True)
    nombre = models.CharField(max_length=45)
    razon_social = models.CharField(max_length=45)
    telefono = models.BigIntegerField(unique=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'empresa'

class Persona(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=45)
    apellido = models.CharField(max_length=45)
    dni = models.IntegerField(unique=True)
    email = models.EmailField(max_length=45,unique=True)
    numero_registro = models.CharField(max_length=45, blank=True, null=True,unique=True)
    telefono = models.BigIntegerField(unique=True)
    direccion = models.ForeignKey(Direccion, on_delete=models.PROTECT)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    class Meta:
        db_table = 'persona'

class ConductoresEmpresa(models.Model):
    id = models.AutoField(primary_key=True)
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT)
    
    def __str__(self):
        return f"{self.persona} - {self.empresa}"
    
    class Meta:
        db_table = 'conductores_empresa'

class Marca(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=45)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'marca'

class Modelo(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=45)
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name='modelos')
    
    def __str__(self):
        return f"{self.marca} {self.nombre}"
    
    class Meta:
        db_table = 'modelo'

class Uso(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=45)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'uso'

class Tipo(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=45)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'tipo'

class Vehiculo(models.Model):
    id = models.AutoField(primary_key=True)
    anio = models.IntegerField()
    color = models.CharField(max_length=45)
    numero_chasis = models.BigIntegerField(unique=True)
    numero_motor = models.CharField(max_length=45,unique=True)
    patente = models.CharField(max_length=45,unique=True)
    tipo = models.ForeignKey(Tipo, on_delete=models.PROTECT, null=True) 
    uso = models.ForeignKey(Uso, on_delete=models.PROTECT, null=True)   
    modelo = models.ForeignKey(Modelo, on_delete=models.PROTECT, null=True)  
    titular = models.ForeignKey(Persona, on_delete=models.PROTECT, null=True)
    
    def __str__(self):
        return f"{self.patente} - {self.modelo}"
    
    class Meta:
        db_table = 'vehiculo'

class TipoCobertura(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=45)
    descripcion = models.TextField()
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'tipo_cobertura'

class EstadoPoliza(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=45)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'estado_poliza'

class Poliza(models.Model):
    id = models.AutoField(primary_key=True)
    numero = models.IntegerField(unique=True)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT)
    estado = models.ForeignKey(EstadoPoliza, on_delete=models.PROTECT)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    franquicia = models.DecimalField(max_digits=10, decimal_places=2)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_cobertura = models.ForeignKey(TipoCobertura, on_delete=models.PROTECT)
    
    def __str__(self):
        return f"Póliza #{self.numero} - {self.vehiculo}"
    
    class Meta:
        db_table = 'poliza'

class Cuota(models.Model):
    id = models.AutoField(primary_key=True)
    fecha_pago = models.DateTimeField(blank=True, null=True)
    fecha_vencimiento = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    numero = models.IntegerField(unique=True)
    poliza = models.ForeignKey(Poliza, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Cuota {self.numero} - Póliza #{self.poliza.numero}"
    
    class Meta:
        db_table = 'cuota'

# Definir un Enum para los tipos de siniestro
class TipoSiniestroEnum(str, Enum):
    OBJETO = 'ChoqueObjeto'
    PERSONA = 'ChoquePersona'
    VEHICULO = 'ChoqueVehiculo'
    ROBO = 'Robo'
    ROBO_PARCIAL = 'RoboParcial'
    INCENDIO = 'Incendio'
    OTRO = 'Otro'

    @classmethod
    def choices(cls):
        return [(item.value, item.value) for item in cls]

class Siniestro(models.Model):
    id = models.AutoField(primary_key=True)
    datos_vehiculo = models.TextField()
    descripcion = models.TextField()
    fecha_hora = models.DateTimeField()
    tipo_siniestro = models.CharField(
        choices=TipoSiniestroEnum.choices(),
        default=TipoSiniestroEnum.OTRO.value,
        max_length=20
    )
    direccion = models.TextField()  # Almacenamos la dirección como string
    vehiculo = models.ForeignKey('Vehiculo', on_delete=models.PROTECT)
    titular = models.ForeignKey(
        'Persona', 
        on_delete=models.PROTECT, 
        related_name='siniestros_titular'
    )
    conductor = models.ForeignKey(
        'Persona', 
        on_delete=models.PROTECT, 
        related_name='siniestros_conductor'
    )

    def __str__(self):
        return f"Siniestro #{self.numero}"

    class Meta:
        db_table = 'siniestro'

    @property
    def tipo_siniestro_enum(self):
        return TipoSiniestroEnum(self.tipo_siniestro)


class ChoqueObjeto(models.Model):
    siniestro = models.OneToOneField(Siniestro, on_delete=models.CASCADE, primary_key=True)
    numero_denuncia = models.IntegerField(unique=True)
    condicion_climatica = models.TextField()
    
    def __str__(self):
        return f"Choque objeto - Siniestro #{self.siniestro.numero}"
    
    class Meta:
        db_table = 'choque_objeto'


class ChoquePersona(models.Model):
    siniestro = models.OneToOneField(Siniestro, on_delete=models.CASCADE, primary_key=True)
    persona_chocada = models.TextField()  # Almacenamos como string
    numero_denuncia = models.IntegerField(unique=True)
    
    def __str__(self):
        return f"Choque persona - Siniestro #{self.siniestro.numero}"
    
    class Meta:
        db_table = 'choque_persona'


class ChoqueVehiculo(models.Model):
    siniestro = models.OneToOneField(Siniestro, on_delete=models.CASCADE, primary_key=True)
    datos_vehiculo_tercero = models.TextField()
    tercero = models.TextField()  # Almacenamos como string
    vehiculo_tercero = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)

    def __str__(self):
        return f"Choque vehículo - Siniestro #{self.siniestro.numero}"
    
    class Meta:
        db_table = 'choque_vehiculo'


class Robo(models.Model):
    siniestro = models.OneToOneField(Siniestro, on_delete=models.CASCADE, primary_key=True)
    numero_denuncia = models.IntegerField(unique=True)
    
    def __str__(self):
        return f"Robo - Siniestro #{self.siniestro.numero}"
    
    class Meta:
        db_table = 'robo'


class RoboParcial(models.Model):
    siniestro = models.OneToOneField(Siniestro, on_delete=models.CASCADE, primary_key=True)
    numero_denuncia = models.IntegerField(unique=True)
    pertenencias_robadas = models.TextField()
    
    def __str__(self):
        return f"Robo parcial - Siniestro #{self.siniestro.numero}"
    
    class Meta:
        db_table = 'robo_parcial'


class Incendio(models.Model):
    siniestro = models.OneToOneField(Siniestro, on_delete=models.CASCADE, primary_key=True)
    numero_informe = models.CharField(max_length=45, unique=True)
    
    def __str__(self):
        return f"Incendio - Siniestro #{self.siniestro.numero}"
    
    class Meta:
        db_table = 'incendio'


class InformeHeridos(models.Model):
    id = models.AutoField(primary_key=True)
    siniestro = models.ForeignKey(Siniestro, on_delete=models.CASCADE)
    herido = models.TextField()  # Almacenamos como string
    descripcion = models.TextField(null=True)
    
    def __str__(self):
        return f"Informe heridos - Siniestro #{self.siniestro.numero}"
    
    class Meta:
        db_table = 'informe_heridos'

