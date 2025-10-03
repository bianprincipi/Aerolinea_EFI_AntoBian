from rest_framework import serializers
from .models import Usuario, Avion, Asiento, Vuelo, Pasajero, Reserva, Boleto


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Usuario"""
    
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'rol', 'telefono', 'is_active']
        read_only_fields = ['id']


class UsuarioRegistroSerializer(serializers.ModelSerializer):
    """Serializer para registro de nuevos usuarios"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'telefono']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = Usuario.objects.create_user(**validated_data)
        return user


class AsientoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Asiento"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = Asiento
        fields = ['id', 'numero', 'fila', 'columna', 'tipo', 'tipo_display', 'avion']
        read_only_fields = ['id']


class AsientoSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para Asiento (para usar en otros serializers)"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = Asiento
        fields = ['id', 'numero', 'fila', 'columna', 'tipo', 'tipo_display']
        read_only_fields = ['id']


class AvionSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Avion"""
    asientos = AsientoSimpleSerializer(many=True, read_only=True)
    total_asientos = serializers.SerializerMethodField()
    
    class Meta:
        model = Avion
        fields = ['id', 'modelo', 'capacidad', 'filas', 'columnas', 'activo', 
                  'fecha_registro', 'asientos', 'total_asientos']
        read_only_fields = ['id', 'fecha_registro']
    
    def get_total_asientos(self, obj):
        return obj.asientos.count()


class AvionSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para Avion"""
    
    class Meta:
        model = Avion
        fields = ['id', 'modelo', 'capacidad']
        read_only_fields = ['id']


class VueloSerializer(serializers.ModelSerializer):
    """Serializer completo para el modelo Vuelo"""
    avion = AvionSimpleSerializer(read_only=True)
    avion_id = serializers.PrimaryKeyRelatedField(
        queryset=Avion.objects.all(), 
        source='avion', 
        write_only=True
    )
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    asientos_disponibles = serializers.SerializerMethodField()
    total_reservas = serializers.SerializerMethodField()
    
    class Meta:
        model = Vuelo
        fields = ['id', 'codigo_vuelo', 'avion', 'avion_id', 'origen', 'destino',
                  'fecha_salida', 'fecha_llegada', 'duracion', 'estado', 'estado_display',
                  'precio_base', 'asientos_disponibles', 'total_reservas']
        read_only_fields = ['id', 'duracion']
    
    def get_asientos_disponibles(self, obj):
        """Calcula la cantidad de asientos disponibles"""
        from .repositories.vuelo_repository import VueloRepository
        asientos = VueloRepository.obtener_asientos_disponibles(obj.id)
        return len(asientos)
    
    def get_total_reservas(self, obj):
        """Cuenta el total de reservas del vuelo"""
        return obj.reservas.filter(estado__in=['pendiente', 'confirmada']).count()


class VueloSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para Vuelo"""
    avion = AvionSimpleSerializer(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Vuelo
        fields = ['id', 'codigo_vuelo', 'origen', 'destino', 'fecha_salida', 
                  'fecha_llegada', 'estado', 'estado_display', 'precio_base', 'avion']
        read_only_fields = ['id']


class PasajeroSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Pasajero"""
    nombre_completo = serializers.CharField(read_only=True)
    tipo_documento_display = serializers.CharField(source='get_tipo_documento_display', read_only=True)
    total_reservas = serializers.SerializerMethodField()
    
    class Meta:
        model = Pasajero
        fields = ['id', 'nombre', 'apellido', 'nombre_completo', 'tipo_documento', 
                  'tipo_documento_display', 'documento', 'email', 'telefono', 
                  'fecha_nacimiento', 'fecha_registro', 'total_reservas']
        read_only_fields = ['id', 'fecha_registro']
    
    def get_total_reservas(self, obj):
        """Cuenta el total de reservas del pasajero"""
        return obj.reservas.count()
    
    def validate_documento(self, value):
        """Valida que el documento sea único"""
        if self.instance:  # Si es actualización
            if Pasajero.objects.exclude(id=self.instance.id).filter(documento=value).exists():
                raise serializers.ValidationError("Ya existe un pasajero con ese documento")
        else:  # Si es creación
            if Pasajero.objects.filter(documento=value).exists():
                raise serializers.ValidationError("Ya existe un pasajero con ese documento")
        return value
    
    def validate_email(self, value):
        """Valida que el email sea único"""
        if self.instance:
            if Pasajero.objects.exclude(id=self.instance.id).filter(email=value).exists():
                raise serializers.ValidationError("Ya existe un pasajero con ese email")
        else:
            if Pasajero.objects.filter(email=value).exists():
                raise serializers.ValidationError("Ya existe un pasajero con ese email")
        return value


class PasajeroSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para Pasajero"""
    nombre_completo = serializers.CharField(read_only=True)
    
    class Meta:
        model = Pasajero
        fields = ['id', 'nombre', 'apellido', 'nombre_completo', 'documento', 'email']
        read_only_fields = ['id']


class ReservaSerializer(serializers.ModelSerializer):
    """Serializer completo para el modelo Reserva"""
    vuelo = VueloSimpleSerializer(read_only=True)
    pasajero = PasajeroSimpleSerializer(read_only=True)
    asiento = AsientoSimpleSerializer(read_only=True)
    
    vuelo_id = serializers.PrimaryKeyRelatedField(
        queryset=Vuelo.objects.all(),
        source='vuelo',
        write_only=True
    )
    pasajero_id = serializers.PrimaryKeyRelatedField(
        queryset=Pasajero.objects.all(),
        source='pasajero',
        write_only=True
    )
    asiento_id = serializers.PrimaryKeyRelatedField(
        queryset=Asiento.objects.all(),
        source='asiento',
        write_only=True
    )
    
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tiene_boleto = serializers.SerializerMethodField()
    
    class Meta:
        model = Reserva
        fields = ['id', 'codigo_reserva', 'vuelo', 'vuelo_id', 'pasajero', 'pasajero_id',
                  'asiento', 'asiento_id', 'estado', 'estado_display', 'fecha_reserva',
                  'precio', 'tiene_boleto']
        read_only_fields = ['id', 'codigo_reserva', 'fecha_reserva']
    
    def get_tiene_boleto(self, obj):
        """Verifica si la reserva tiene boleto"""
        return hasattr(obj, 'boleto')
    
    def validate(self, data):
        """Validaciones personalizadas"""
        # Verificar que el vuelo esté disponible
        vuelo = data.get('vuelo')
        if vuelo and vuelo.estado != 'programado':
            raise serializers.ValidationError("El vuelo no está disponible para reservas")
        
        # Verificar que el asiento esté disponible
        from .repositories.reserva_repository import ReservaRepository
        asiento = data.get('asiento')
        if vuelo and asiento:
            if not ReservaRepository.verificar_asiento_disponible(vuelo.id, asiento.id):
                raise serializers.ValidationError("El asiento no está disponible")
        
        # Verificar que el pasajero no tenga ya una reserva en este vuelo
        pasajero = data.get('pasajero')
        if vuelo and pasajero:
            if ReservaRepository.verificar_pasajero_tiene_reserva(vuelo.id, pasajero.id):
                raise serializers.ValidationError("El pasajero ya tiene una reserva en este vuelo")
        
        # Si no se especifica precio, usar el precio base del vuelo
        if 'precio' not in data and vuelo:
            data['precio'] = vuelo.precio_base
        
        return data


class ReservaSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para Reserva"""
    pasajero = PasajeroSimpleSerializer(read_only=True)
    asiento = AsientoSimpleSerializer(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Reserva
        fields = ['id', 'codigo_reserva', 'pasajero', 'asiento', 'estado', 'estado_display', 
                  'fecha_reserva', 'precio']
        read_only_fields = ['id', 'codigo_reserva', 'fecha_reserva']


class BoletoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Boleto"""
    reserva = ReservaSimpleSerializer(read_only=True)
    vuelo = serializers.SerializerMethodField()
    pasajero = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Boleto
        fields = ['id', 'codigo_barra', 'reserva', 'vuelo', 'pasajero', 
                  'estado', 'estado_display', 'fecha_emision', 'qr_code']
        read_only_fields = ['id', 'codigo_barra', 'fecha_emision']
    
    def get_vuelo(self, obj):
        """Obtiene información del vuelo"""
        return VueloSimpleSerializer(obj.reserva.vuelo).data
    
    def get_pasajero(self, obj):
        """Obtiene información del pasajero"""
        return PasajeroSimpleSerializer(obj.reserva.pasajero).data


class BoletoSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para Boleto"""
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Boleto
        fields = ['id', 'codigo_barra', 'estado', 'estado_display', 'fecha_emision']
        read_only_fields = ['id', 'codigo_barra', 'fecha_emision']


# Serializers para reportes y consultas específicas

class ReportePasajerosVueloSerializer(serializers.Serializer):
    """Serializer para el reporte de pasajeros por vuelo"""
    vuelo = VueloSimpleSerializer(read_only=True)
    total_pasajeros = serializers.IntegerField(read_only=True)
    pasajeros = ReservaSimpleSerializer(many=True, read_only=True)


class AsientoDisponibleSerializer(serializers.Serializer):
    """Serializer para mostrar asientos disponibles con información adicional"""
    asiento = AsientoSimpleSerializer(read_only=True)
    disponible = serializers.BooleanField(read_only=True)


class EstadisticasVueloSerializer(serializers.Serializer):
    """Serializer para estadísticas de vuelo"""
    total_vuelos = serializers.IntegerField()
    vuelos_programados = serializers.IntegerField()
    vuelos_completados = serializers.IntegerField()
    vuelos_cancelados = serializers.IntegerField()