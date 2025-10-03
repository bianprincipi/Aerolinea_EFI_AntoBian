from django.core.exceptions import ValidationError
from ..models import Boleto


class BoletoService:
    """Service para la lógica de negocio de boletos"""
    
    @staticmethod
    def obtener_boleto(boleto_id):
        """Obtiene un boleto por ID"""
        try:
            return Boleto.objects.select_related(
                'reserva', 'reserva__vuelo', 'reserva__pasajero', 'reserva__asiento'
            ).get(id=boleto_id)
        except Boleto.DoesNotExist:
            raise ValidationError("El boleto no existe")
    
    @staticmethod
    def obtener_por_codigo(codigo_barra):
        """Obtiene un boleto por su código de barra"""
        try:
            return Boleto.objects.select_related(
                'reserva', 'reserva__vuelo', 'reserva__pasajero', 'reserva__asiento'
            ).get(codigo_barra=codigo_barra)
        except Boleto.DoesNotExist:
            raise ValidationError("El boleto no existe")
    
    @staticmethod
    def verificar_boleto(codigo_barra):
        """Verifica la validez de un boleto"""
        boleto = BoletoService.obtener_por_codigo(codigo_barra)
        
        if boleto.estado == 'cancelado':
            return {
                'valido': False,
                'mensaje': 'El boleto está cancelado',
                'boleto': boleto
            }
        
        if boleto.estado == 'usado':
            return {
                'valido': False,
                'mensaje': 'El boleto ya fue utilizado',
                'boleto': boleto
            }
        
        if boleto.reserva.estado != 'confirmada':
            return {
                'valido': False,
                'mensaje': f'La reserva está en estado: {boleto.reserva.estado}',
                'boleto': boleto
            }
        
        if boleto.reserva.vuelo.estado == 'cancelado':
            return {
                'valido': False,
                'mensaje': 'El vuelo está cancelado',
                'boleto': boleto
            }
        
        return {
            'valido': True,
            'mensaje': 'Boleto válido',
            'boleto': boleto
        }
    
    @staticmethod
    def usar_boleto(codigo_barra):
        """Marca un boleto como usado (check-in)"""
        boleto = BoletoService.obtener_por_codigo(codigo_barra)
        
        if boleto.estado == 'usado':
            raise ValidationError("El boleto ya fue utilizado")
        
        if boleto.estado == 'cancelado':
            raise ValidationError("El boleto está cancelado")
        
        if boleto.reserva.estado != 'confirmada':
            raise ValidationError("La reserva no está confirmada")
        
        boleto.estado = 'usado'
        boleto.save()
        
        boleto.reserva.estado = 'completada'
        boleto.reserva.save()
        
        return boleto
    
    @staticmethod
    def cancelar_boleto(boleto_id):
        """Cancela un boleto"""
        boleto = BoletoService.obtener_boleto(boleto_id)
        
        if boleto.estado == 'usado':
            raise ValidationError("No se puede cancelar un boleto ya utilizado")
        
        boleto.estado = 'cancelado'
        boleto.save()
        
        return boleto