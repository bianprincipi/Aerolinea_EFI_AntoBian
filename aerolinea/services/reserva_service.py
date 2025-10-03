from django.core.exceptions import ValidationError
from django.db import transaction
from ..repositories.reserva_repository import ReservaRepository
from ..repositories.vuelo_repository import VueloRepository
from ..repositories.pasajero_repository import PasajeroRepository
from ..models import Boleto


class ReservaService:
    """Service para la lógica de negocio de reservas"""
    
    @staticmethod
    def listar_reservas():
        """Lista todas las reservas"""
        return ReservaRepository.obtener_todas()
    
    @staticmethod
    def obtener_reserva(reserva_id):
        """Obtiene una reserva por ID"""
        reserva = ReservaRepository.obtener_por_id(reserva_id)
        if not reserva:
            raise ValidationError("La reserva no existe")
        return reserva
    
    @staticmethod
    def obtener_reserva_por_codigo(codigo_reserva):
        """Obtiene una reserva por código"""
        reserva = ReservaRepository.obtener_por_codigo(codigo_reserva)
        if not reserva:
            raise ValidationError("La reserva no existe")
        return reserva
    
    @staticmethod
    def obtener_reservas_pasajero(pasajero_id):
        """Obtiene todas las reservas de un pasajero"""
        pasajero = PasajeroRepository.obtener_por_id(pasajero_id)
        if not pasajero:
            raise ValidationError("El pasajero no existe")
        
        return ReservaRepository.obtener_por_pasajero(pasajero_id)
    
    @staticmethod
    def obtener_reservas_activas_pasajero(pasajero_id):
        """Obtiene las reservas activas de un pasajero"""
        pasajero = PasajeroRepository.obtener_por_id(pasajero_id)
        if not pasajero:
            raise ValidationError("El pasajero no existe")
        
        return ReservaRepository.obtener_activas_pasajero(pasajero_id)
    
    @staticmethod
    @transaction.atomic
    def crear_reserva(vuelo_id, pasajero_id, asiento_id, precio=None):
        """Crea una nueva reserva con validaciones"""
        vuelo = VueloRepository.obtener_por_id(vuelo_id)
        if not vuelo:
            raise ValidationError("El vuelo no existe")
        
        if vuelo.estado != 'programado':
            raise ValidationError("El vuelo no está disponible para reservas")
        
        pasajero = PasajeroRepository.obtener_por_id(pasajero_id)
        if not pasajero:
            raise ValidationError("El pasajero no existe")
        
        if not ReservaRepository.verificar_asiento_disponible(vuelo_id, asiento_id):
            raise ValidationError("El asiento no está disponible")
        
        if ReservaRepository.verificar_pasajero_tiene_reserva(vuelo_id, pasajero_id):
            raise ValidationError("El pasajero ya tiene una reserva en este vuelo")
        
        if precio is None:
            precio = vuelo.precio_base
        
        datos_reserva = {
            'vuelo_id': vuelo_id,
            'pasajero_id': pasajero_id,
            'asiento_id': asiento_id,
            'precio': precio,
            'estado': 'pendiente'
        }
        
        return ReservaRepository.crear_reserva(datos_reserva)
    
    @staticmethod
    @transaction.atomic
    def confirmar_reserva(reserva_id):
        """Confirma una reserva y genera el boleto"""
        reserva = ReservaRepository.obtener_por_id(reserva_id)
        if not reserva:
            raise ValidationError("La reserva no existe")
        
        if reserva.estado != 'pendiente':
            raise ValidationError("Solo se pueden confirmar reservas pendientes")
        
        if reserva.vuelo.estado != 'programado':
            raise ValidationError("El vuelo ya no está disponible")
        
        reserva = ReservaRepository.confirmar_reserva(reserva_id)
        
        if not ReservaRepository.tiene_boleto(reserva_id):
            boleto = Boleto.objects.create(
                reserva=reserva,
                estado='emitido'
            )
        
        return reserva
    
    @staticmethod
    def cancelar_reserva(reserva_id):
        """Cancela una reserva"""
        reserva = ReservaRepository.obtener_por_id(reserva_id)
        if not reserva:
            raise ValidationError("La reserva no existe")
        
        if reserva.estado == 'completada':
            raise ValidationError("No se puede cancelar una reserva completada")
        
        if reserva.estado == 'cancelada':
            raise ValidationError("La reserva ya está cancelada")
        
        if ReservaRepository.tiene_boleto(reserva_id):
            boleto = reserva.boleto
            boleto.estado = 'cancelado'
            boleto.save()
        
        return ReservaRepository.cancelar_reserva(reserva_id)
    
    @staticmethod
    def cambiar_estado(reserva_id, nuevo_estado):
        """Cambia el estado de una reserva"""
        estados_validos = ['pendiente', 'confirmada', 'cancelada', 'completada']
        
        if nuevo_estado not in estados_validos:
            raise ValidationError(f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}")
        
        reserva = ReservaRepository.obtener_por_id(reserva_id)
        if not reserva:
            raise ValidationError("La reserva no existe")
        
        return ReservaRepository.cambiar_estado(reserva_id, nuevo_estado)
    
    @staticmethod
    def obtener_reservas_vuelo(vuelo_id):
        """Obtiene todas las reservas de un vuelo"""
        vuelo = VueloRepository.obtener_por_id(vuelo_id)
        if not vuelo:
            raise ValidationError("El vuelo no existe")
        
        return ReservaRepository.obtener_por_vuelo(vuelo_id)
    
    @staticmethod
    def generar_boleto(reserva_id):
        """Genera un boleto para una reserva confirmada"""
        reserva = ReservaRepository.obtener_por_id(reserva_id)
        if not reserva:
            raise ValidationError("La reserva no existe")
        
        if reserva.estado != 'confirmada':
            raise ValidationError("Solo se pueden generar boletos para reservas confirmadas")
        
        if ReservaRepository.tiene_boleto(reserva_id):
            raise ValidationError("La reserva ya tiene un boleto generado")
        
        boleto = Boleto.objects.create(
            reserva=reserva,
            estado='emitido'
        )
        
        return boleto