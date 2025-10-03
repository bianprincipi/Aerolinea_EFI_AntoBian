from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
import uuid
from datetime import datetime


class Usuario(AbstractUser):
    """Usuario del sistema con roles"""
    ROLES = [
        ('admin', 'Administrador'),
        ('empleado', 'Empleado'),
        ('cliente', 'Cliente'),
    ]
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'


class Avion(models.Model):
    """Modelo para los aviones de la flota"""
    modelo = models.CharField(max_length=100)
    capacidad = models.IntegerField(validators=[MinValueValidator(1)])
    filas = models.IntegerField(validators=[MinValueValidator(1)])
    columnas = models.IntegerField(validators=[MinValueValidator(1)])
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'aviones'
        verbose_name = 'Avión'
        verbose_name_plural = 'Aviones'
    
    def __str__(self):
        return f"{self.modelo} (Cap: {self.capacidad})"


class Asiento(models.Model):
    """Asientos de cada avión"""
    TIPOS_ASIENTO = [
        ('economico', 'Económico'),
        ('ejecutivo', 'Ejecutivo'),
        ('primera', 'Primera Clase'),
    ]
    
    avion = models.ForeignKey(Avion, on_delete=models.CASCADE, related_name='asientos')
    numero = models.CharField(max_length=10)
    fila = models.IntegerField(validators=[MinValueValidator(1)])
    columna = models.CharField(max_length=2)
    tipo = models.CharField(max_length=20, choices=TIPOS_ASIENTO, default='economico')
    
    class Meta:
        db_table = 'asientos'
        unique_together = ['avion', 'numero']
        ordering = ['fila', 'columna']
    
    def __str__(self):
        return f"Asiento {self.numero} - {self.avion.modelo}"


class Vuelo(models.Model):
    """Vuelos programados"""
    ESTADOS_VUELO = [
        ('programado', 'Programado'),
        ('abordando', 'Abordando'),
        ('en_vuelo', 'En Vuelo'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    
    avion = models.ForeignKey(Avion, on_delete=models.PROTECT, related_name='vuelos')
    origen = models.CharField(max_length=100)
    destino = models.CharField(max_length=100)
    fecha_salida = models.DateTimeField()
    fecha_llegada = models.DateTimeField()
    duracion = models.DurationField()
    estado = models.CharField(max_length=20, choices=ESTADOS_VUELO, default='programado')
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    codigo_vuelo = models.CharField(max_length=10, unique=True)
    
    class Meta:
        db_table = 'vuelos'
        ordering = ['-fecha_salida']
    
    def __str__(self):
        return f"{self.codigo_vuelo}: {self.origen} → {self.destino}"
    
    def save(self, *args, **kwargs):
        if self.fecha_salida and self.fecha_llegada:
            self.duracion = self.fecha_llegada - self.fecha_salida
        super().save(*args, **kwargs)


class Pasajero(models.Model):
    """Información de pasajeros"""
    TIPOS_DOCUMENTO = [
        ('dni', 'DNI'),
        ('pasaporte', 'Pasaporte'),
        ('ci', 'Cédula de Identidad'),
    ]
    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    tipo_documento = models.CharField(max_length=20, choices=TIPOS_DOCUMENTO)
    documento = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='pasajero')
    
    class Meta:
        db_table = 'pasajeros'
        ordering = ['apellido', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.documento})"
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"


class Reserva(models.Model):
    """Reservas de vuelos"""
    ESTADOS_RESERVA = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]
    
    vuelo = models.ForeignKey(Vuelo, on_delete=models.CASCADE, related_name='reservas')
    pasajero = models.ForeignKey(Pasajero, on_delete=models.CASCADE, related_name='reservas')
    asiento = models.ForeignKey(Asiento, on_delete=models.PROTECT, related_name='reservas')
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='pendiente')
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    codigo_reserva = models.CharField(max_length=10, unique=True, editable=False)
    
    class Meta:
        db_table = 'reservas'
        unique_together = [
            ['vuelo', 'pasajero'],
            ['vuelo', 'asiento'],
        ]
        ordering = ['-fecha_reserva']
    
    def __str__(self):
        return f"Reserva {self.codigo_reserva} - {self.pasajero.nombre_completo}"
    
    def save(self, *args, **kwargs):
        if not self.codigo_reserva:
            self.codigo_reserva = self._generar_codigo_reserva()
        super().save(*args, **kwargs)
    
    def _generar_codigo_reserva(self):
        return str(uuid.uuid4().hex[:6].upper())


class Boleto(models.Model):
    """Boletos electrónicos generados"""
    ESTADOS_BOLETO = [
        ('emitido', 'Emitido'),
        ('usado', 'Usado'),
        ('cancelado', 'Cancelado'),
    ]
    
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='boleto')
    codigo_barra = models.CharField(max_length=50, unique=True, editable=False)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_BOLETO, default='emitido')
    qr_code = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'boletos'
        ordering = ['-fecha_emision']
    
    def __str__(self):
        return f"Boleto {self.codigo_barra}"
    
    def save(self, *args, **kwargs):(venv) bian-principi@bian-principi-LOQ-15IAX9:~/Aerolinea_EFI_AntoBian$ mkdir aerolinea/services/reserva_service.py
mkdir: no se puede crear el directorio «aerolinea/services/reserva_service.py»: No existe el archivo o el directorio

        if not self.codigo_barra:
            self.codigo_barra = self._generar_codigo_barra()
        super().save(*args, **kwargs)
    
    def _generar_codigo_barra(self):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = uuid.uuid4().hex[:6].upper()
        return f"BT{timestamp}{random_str}"
