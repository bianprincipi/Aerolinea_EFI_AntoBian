from django.db.models import Q
from ..models import Reserva, Boleto


class ReservaRepository:
    """Repository para gestionar consultas de reservas"""
    
    @staticmethod
    def obtener_todas():
        """Obtiene todas las reservas"""
        return Reserva.objects.select_related(
            'vuelo', 'pasajero', 'asiento', 'vuelo__avion'
        ).all()
    
    @staticmethod
    def obtener_por_id(reserva_id):
        """Obtiene una reserva por su ID"""
        try:
            return Reserva.objects.select_related(
                'vuelo', 'pasajero', 'asiento', 'vuelo__avion'
            ).get(id=reserva_id)
        except Reserva.DoesNotExist:
            return None
    
    @staticmethod
    def obtener_por_codigo(codigo_reserva):
        """Obtiene una reserva por su código"""
        try:
            return Reserva.objects.select_related(
                'vuelo', 'pasajero', 'asiento', 'vuelo__avion'
            ).get(codigo_reserva=codigo_reserva)
        except Reserva.DoesNotExist:
            return None
    
    @staticmethod
    def obtener_por_pasajero(pasajero_id):
        """Obtiene todas las reservas de un pasajero"""
        return Reserva.objects.filter(
            pasajero_id=pasajero_id
        ).select_related(
            'vuelo', 'asiento', 'vuelo__avion'
        ).order_by('-fecha_reserva')
    
    @staticmethod
    def obtener_por_vuelo(vuelo_id):
        """Obtiene todas las reservas de un vuelo"""
        return Reserva.objects.filter(
            vuelo_id=vuelo_id
        ).select_related(
            'pasajero', 'asiento'
        ).order_by('asiento__numero')
    
    @staticmethod
    def obtener_activas_pasajero(pasajero_id):
        """Obtiene las reservas activas de un pasajero"""
        return Reserva.objects.filter(
            pasajero_id=pasajero_id,
            estado__in=['pendiente', 'confirmada']
        ).select_related(
            'vuelo', 'asiento', 'vuelo__avion'
        ).order_by('-fecha_reserva')
    
    @staticmethod
    def verificar_asiento_disponible(vuelo_id, asiento_id):
        """Verifica si un asiento está disponible en un vuelo"""
        return not Reserva.objects.filter(
            vuelo_id=vuelo_id,
            asiento_id=asiento_id,
            estado__in=['pendiente', 'confirmada']
        ).exists()
    
    @staticmethod
    def verificar_pasajero_tiene_reserva(vuelo_id, pasajero_id):
        """Verifica si un pasajero ya tiene reserva en un vuelo"""
        return Reserva.objects.filter(
            vuelo_id=vuelo_id,
            pasajero_id=pasajero_id,
            estado__in=['pendiente', 'confirmada']
        ).exists()
    
    @staticmethod
    def crear_reserva(datos):
        """Crea una nueva reserva"""
        return Reserva.objects.create(**datos)
    
    @staticmethod
    def actualizar_reserva(reserva_id, datos):
        """Actualiza una reserva"""
        Reserva.objects.filter(id=reserva_id).update(**datos)
        return ReservaRepository.obtener_por_id(reserva_id)
    
    @staticmethod
    def cambiar_estado(reserva_id, nuevo_estado):
        """Cambia el estado de una reserva"""
        Reserva.objects.filter(id=reserva_id).update(estado=nuevo_estado)
        return ReservaRepository.obtener_por_id(reserva_id)
    
    @staticmethod
    def cancelar_reserva(reserva_id):
        """Cancela una reserva"""
        return ReservaRepository.cambiar_estado(reserva_id, 'cancelada')
    
    @staticmethod
    def confirmar_reserva(reserva_id):
        """Confirma una reserva"""
        return ReservaRepository.cambiar_estado(reserva_id, 'confirmada')
    
    @staticmethod
    def eliminar_reserva(reserva_id):
        """Elimina una reserva"""
        reserva = ReservaRepository.obtener_por_id(reserva_id)
        if reserva:
            reserva.delete()
            return True
        return False
    
    @staticmethod
    def obtener_con_boleto(reserva_id):
        """Obtiene una reserva con su boleto asociado"""
        try:
            return Reserva.objects.select_related(
                'vuelo', 'pasajero', 'asiento', 'boleto'
            ).get(id=reserva_id)
        except Reserva.DoesNotExist:
            return None
    
    @staticmethod
    def tiene_boleto(reserva_id):
        """Verifica si una reserva tiene boleto generado"""
        return Boleto.objects.filter(reserva_id=reserva_id).exists()