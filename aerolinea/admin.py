from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Avion, Asiento, Vuelo, Pasajero, Reserva, Boleto


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Administración de usuarios"""
    list_display = ['username', 'email', 'rol', 'first_name', 'last_name', 'is_active']
    list_filter = ['rol', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('rol', 'telefono')
        }),
    )


@admin.register(Avion)
class AvionAdmin(admin.ModelAdmin):
    """Administración de aviones"""
    list_display = ['modelo', 'capacidad', 'filas', 'columnas', 'activo', 'fecha_registro']
    list_filter = ['activo', 'fecha_registro']
    search_fields = ['modelo']
    readonly_fields = ['fecha_registro']
    
    fieldsets = (
        ('Información del Avión', {
            'fields': ('modelo', 'activo')
        }),
        ('Configuración de Asientos', {
            'fields': ('capacidad', 'filas', 'columnas')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Generar asientos automáticamente al crear un avión"""
        super().save_model(request, obj, form, change)
        
        # Si es un avión nuevo, generar los asientos
        if not change:
            self._generar_asientos(obj)
    
    def _generar_asientos(self, avion):
        """Genera los asientos para el avión"""
        columnas_letras = ['A', 'B', 'C', 'D', 'E', 'F']
        asientos = []
        
        for fila in range(1, avion.filas + 1):
            for col_idx in range(avion.columnas):
                if col_idx < len(columnas_letras):
                    columna = columnas_letras[col_idx]
                    numero = f"{fila}{columna}"
                    
                    # Definir tipo de asiento según la fila
                    if fila <= 2:
                        tipo = 'primera'
                    elif fila <= 5:
                        tipo = 'ejecutivo'
                    else:
                        tipo = 'economico'
                    
                    asientos.append(Asiento(
                        avion=avion,
                        numero=numero,
                        fila=fila,
                        columna=columna,
                        tipo=tipo
                    ))
        
        # Crear todos los asientos de una vez
        Asiento.objects.bulk_create(asientos)


@admin.register(Asiento)
class AsientoAdmin(admin.ModelAdmin):
    """Administración de asientos"""
    list_display = ['numero', 'avion', 'tipo', 'fila', 'columna']
    list_filter = ['tipo', 'avion']
    search_fields = ['numero', 'avion__modelo']
    ordering = ['avion', 'fila', 'columna']


@admin.register(Vuelo)
class VueloAdmin(admin.ModelAdmin):
    """Administración de vuelos"""
    list_display = ['codigo_vuelo', 'origen', 'destino', 'fecha_salida', 'estado', 'precio_base', 'avion']
    list_filter = ['estado', 'origen', 'destino', 'fecha_salida']
    search_fields = ['codigo_vuelo', 'origen', 'destino']
    date_hierarchy = 'fecha_salida'
    readonly_fields = ['duracion']
    
    fieldsets = (
        ('Información del Vuelo', {
            'fields': ('codigo_vuelo', 'avion', 'estado')
        }),
        ('Ruta', {
            'fields': ('origen', 'destino')
        }),
        ('Horarios', {
            'fields': ('fecha_salida', 'fecha_llegada', 'duracion')
        }),
        ('Precio', {
            'fields': ('precio_base',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Hacer duracion readonly siempre"""
        return self.readonly_fields


@admin.register(Pasajero)
class PasajeroAdmin(admin.ModelAdmin):
    """Administración de pasajeros"""
    list_display = ['nombre_completo', 'tipo_documento', 'documento', 'email', 'telefono', 'fecha_registro']
    list_filter = ['tipo_documento', 'fecha_registro']
    search_fields = ['nombre', 'apellido', 'documento', 'email']
    readonly_fields = ['fecha_registro']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'fecha_nacimiento')
        }),
        ('Documentación', {
            'fields': ('tipo_documento', 'documento')
        }),
        ('Contacto', {
            'fields': ('email', 'telefono')
        }),
        ('Usuario Asociado', {
            'fields': ('usuario',),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',)
        }),
    )


class ReservaInline(admin.TabularInline):
    """Inline para mostrar reservas en otros modelos"""
    model = Reserva
    extra = 0
    readonly_fields = ['codigo_reserva', 'fecha_reserva', 'precio']
    fields = ['vuelo', 'pasajero', 'asiento', 'estado', 'precio', 'codigo_reserva']


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    """Administración de reservas"""
    list_display = ['codigo_reserva', 'vuelo', 'pasajero', 'asiento', 'estado', 'precio', 'fecha_reserva']
    list_filter = ['estado', 'fecha_reserva', 'vuelo__origen', 'vuelo__destino']
    search_fields = ['codigo_reserva', 'pasajero__nombre', 'pasajero__apellido', 'vuelo__codigo_vuelo']
    readonly_fields = ['codigo_reserva', 'fecha_reserva']
    date_hierarchy = 'fecha_reserva'
    
    fieldsets = (
        ('Información de la Reserva', {
            'fields': ('codigo_reserva', 'estado', 'fecha_reserva')
        }),
        ('Detalles del Vuelo', {
            'fields': ('vuelo', 'asiento', 'precio')
        }),
        ('Pasajero', {
            'fields': ('pasajero',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Si la reserva ya existe, no permitir cambiar vuelo, asiento y pasajero"""
        if obj:  # Editando una reserva existente
            return self.readonly_fields + ['vuelo', 'asiento', 'pasajero']
        return self.readonly_fields


@admin.register(Boleto)
class BoletoAdmin(admin.ModelAdmin):
    """Administración de boletos"""
    list_display = ['codigo_barra', 'get_pasajero', 'get_vuelo', 'estado', 'fecha_emision']
    list_filter = ['estado', 'fecha_emision']
    search_fields = ['codigo_barra', 'reserva__codigo_reserva', 'reserva__pasajero__nombre']
    readonly_fields = ['codigo_barra', 'fecha_emision', 'reserva']
    date_hierarchy = 'fecha_emision'
    
    fieldsets = (
        ('Información del Boleto', {
            'fields': ('codigo_barra', 'estado', 'fecha_emision')
        }),
        ('Reserva Asociada', {
            'fields': ('reserva',)
        }),
        ('Código QR', {
            'fields': ('qr_code',),
            'classes': ('collapse',)
        }),
    )
    
    def get_pasajero(self, obj):
        """Mostrar el nombre del pasajero"""
        return obj.reserva.pasajero.nombre_completo
    get_pasajero.short_description = 'Pasajero'
    
    def get_vuelo(self, obj):
        """Mostrar el código del vuelo"""
        return obj.reserva.vuelo.codigo_vuelo
    get_vuelo.short_description = 'Vuelo'
    
    def has_add_permission(self, request):
        """No permitir crear boletos manualmente desde el admin"""
        return False


# Personalizar el título del admin
admin.site.site_header = "Administración de Aerolínea"
admin.site.site_title = "Aerolínea Admin"
admin.site.index_title = "Panel de Administración"
