from django.db.models import Q, Count, F
from datetime import datetime, timedelta
from ..models import Vuelo, Reserva


class VueloRepository:
    """Repository para gestionar consultas de vuelos"""
    
    @staticmethod
    def obtener_todos():
        """Obtiene todos los vuelos"""
        return Vuelo.objects.select_related('avion').all()
    
    @staticmethod
    def obtener_por_id(vuelo_id):
        """Obtiene un vuelo por su ID"""
        try:
            return Vuelo.objects.select_related('avion').get(id=vuelo_id)
        except Vuelo.DoesNotExist:
            return None
    
    @staticmethod
    def obtener_por_codigo(codigo_vuelo):
        """Obtiene un vuelo por su código"""
        try:
            return Vuelo.objects.select_related('avion').get(codigo_vuelo=codigo_vuelo)
        except Vuelo.DoesNotExist:
            return None
    
    @staticmethod
    def filtrar_por_origen_destino(origen=None, destino=None):
        """Filtra vuelos por origen y/o destino"""
        queryset = Vuelo.objects.select_related('avion')
        
        if origen:
            queryset = queryset.filter(origen__icontains=origen)
        if destino:
            queryset = queryset.filter(destino__icontains=destino)
        
        return queryset
    
    @staticmethod
    def filtrar_por_fecha(fecha_inicio=None, fecha_fin=None):
        """Filtra vuelos por rango de fechas"""
        queryset = Vuelo.objects.select_related('avion')
        
        if fecha_inicio:
            queryset = queryset.filter(fecha_salida__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha_salida__lte=fecha_fin)
        
        return queryset
    
    @staticmethod
    def buscar_vuelos(origen=None, destino=None, fecha=None):
        """Busca vuelos disponibles según criterios"""
        queryset = Vuelo.objects.select_related('avion').filter(
            estado='programado'
        )
        
        if origen:
            queryset = queryset.filter(origen__icontains=origen)
        if destino:
            queryset = queryset.filter(destino__icontains=destino)
        if fecha:
            fecha_inicio = datetime.combine(fecha, datetime.min.time())
            fecha_fin = datetime.combine(fecha, datetime.max.time())
            queryset = queryset.filter(
                fecha_salida__gte=fecha_inicio,
                fecha_salida__lte=fecha_fin
            )
        
        return queryset.order_by('fecha_salida')
    
    @staticmethod
    def obtener_vuelos_disponibles():
        """Obtiene vuelos en estado programado"""
        return Vuelo.objects.select_related('avion').filter(
            estado='programado',
            fecha_salida__gte=datetime.now()
        ).order_by('fecha_salida')
    
    @staticmethod
    def obtener_asientos_disponibles(vuelo_id):
        """Obtiene los asientos disponibles de un vuelo"""
        vuelo = VueloRepository.obtener_por_id(vuelo_id)
        if not vuelo:
            return []
        
        asientos_reservados = Reserva.objects.filter(
            vuelo_id=vuelo_id,
            estado__in=['pendiente', 'confirmada']
        ).values_list('asiento_id', flat=True)
        
        return vuelo.avion.asientos.exclude(id__in=asientos_reservados)
    
    @staticmethod
    def contar_reservas(vuelo_id):
        """Cuenta las reservas de un vuelo"""
        return Reserva.objects.filter(
            vuelo_id=vuelo_id,
            estado__in=['pendiente', 'confirmada']
        ).count()
    
    @staticmethod
    def obtener_pasajeros(vuelo_id):
        """Obtiene la lista de pasajeros de un vuelo"""
        return Reserva.objects.filter(
            vuelo_id=vuelo_id,
            estado__in=['confirmada', 'completada']
        ).select_related('pasajero', 'asiento').order_by('asiento__numero')
    
    @staticmethod
    def crear_vuelo(datos):
        """Crea un nuevo vuelo"""
        return Vuelo.objects.create(**datos)
    
    @staticmethod
    def actualizar_vuelo(vuelo_id, datos):
        """Actualiza un vuelo existente"""
        Vuelo.objects.filter(id=vuelo_id).update(**datos)
        return VueloRepository.obtener_por_id(vuelo_id)
    
    @staticmethod
    def eliminar_vuelo(vuelo_id):
        """Elimina un vuelo"""
        vuelo = VueloRepository.obtener_por_id(vuelo_id)
        if vuelo:
            vuelo.delete()
            return True
        return False
    
    @staticmethod
    def cambiar_estado(vuelo_id, nuevo_estado):
        """Cambia el estado de un vuelo"""
        Vuelo.objects.filter(id=vuelo_id).update(estado=nuevo_estado)
        return VueloRepository.obtener_por_id(vuelo_id)