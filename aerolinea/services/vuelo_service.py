from datetime import datetime
from django.core.exceptions import ValidationError
from ..repositories.vuelo_repository import VueloRepository


class VueloService:
    """Service para la lógica de negocio de vuelos"""
    
    @staticmethod
    def listar_vuelos():
        """Lista todos los vuelos"""
        return VueloRepository.obtener_todos()
    
    @staticmethod
    def obtener_vuelo(vuelo_id):
        """Obtiene un vuelo por ID"""
        vuelo = VueloRepository.obtener_por_id(vuelo_id)
        if not vuelo:
            raise ValidationError("El vuelo no existe")
        return vuelo
    
    @staticmethod
    def obtener_vuelo_por_codigo(codigo_vuelo):
        """Obtiene un vuelo por código"""
        vuelo = VueloRepository.obtener_por_codigo(codigo_vuelo)
        if not vuelo:
            raise ValidationError("El vuelo no existe")
        return vuelo
    
    @staticmethod
    def buscar_vuelos_disponibles(origen=None, destino=None, fecha=None):
        """Busca vuelos disponibles"""
        vuelos = VueloRepository.buscar_vuelos(origen, destino, fecha)
        
        resultado = []
        for vuelo in vuelos:
            asientos_disponibles = VueloRepository.obtener_asientos_disponibles(vuelo.id)
            resultado.append({
                'vuelo': vuelo,
                'asientos_disponibles': len(asientos_disponibles),
                'capacidad_total': vuelo.avion.capacidad
            })
        
        return resultado
    
    @staticmethod
    def obtener_asientos_disponibles(vuelo_id):
        """Obtiene los asientos disponibles de un vuelo"""
        vuelo = VueloRepository.obtener_por_id(vuelo_id)
        if not vuelo:
            raise ValidationError("El vuelo no existe")
        
        if vuelo.estado != 'programado':
            raise ValidationError("El vuelo no está disponible para reservas")
        
        return VueloRepository.obtener_asientos_disponibles(vuelo_id)
    
    @staticmethod
    def crear_vuelo(datos):
        """Crea un nuevo vuelo con validaciones"""
        if datos['fecha_salida'] >= datos['fecha_llegada']:
            raise ValidationError("La fecha de llegada debe ser posterior a la fecha de salida")
        
        if datos['fecha_salida'] < datetime.now():
            raise ValidationError("La fecha de salida no puede ser en el pasado")
        
        if datos['precio_base'] <= 0:
            raise ValidationError("El precio debe ser mayor a 0")
        
        if VueloRepository.obtener_por_codigo(datos['codigo_vuelo']):
            raise ValidationError("Ya existe un vuelo con ese código")
        
        return VueloRepository.crear_vuelo(datos)
    
    @staticmethod
    def actualizar_vuelo(vuelo_id, datos):
        """Actualiza un vuelo"""
        vuelo = VueloRepository.obtener_por_id(vuelo_id)
        if not vuelo:
            raise ValidationError("El vuelo no existe")
        
        reservas = VueloRepository.contar_reservas(vuelo_id)
        if reservas > 0:
            campos_bloqueados = ['avion_id', 'fecha_salida', 'origen', 'destino']
            if any(campo in datos for campo in campos_bloqueados):
                raise ValidationError(
                    "No se puede modificar el avión, fechas o ruta de un vuelo con reservas"
                )
        
        return VueloRepository.actualizar_vuelo(vuelo_id, datos)
    
    @staticmethod
    def cancelar_vuelo(vuelo_id):
        """Cancela un vuelo"""
        vuelo = VueloRepository.obtener_por_id(vuelo_id)
        if not vuelo:
            raise ValidationError("El vuelo no existe")
        
        if vuelo.estado == 'completado':
            raise ValidationError("No se puede cancelar un vuelo completado")
        
        return VueloRepository.cambiar_estado(vuelo_id, 'cancelado')
    
    @staticmethod
    def obtener_reporte_pasajeros(vuelo_id):
        """Obtiene el reporte de pasajeros de un vuelo"""
        vuelo = VueloRepository.obtener_por_id(vuelo_id)
        if not vuelo:
            raise ValidationError("El vuelo no existe")
        
        pasajeros = VueloRepository.obtener_pasajeros(vuelo_id)
        
        return {
            'vuelo': vuelo,
            'total_pasajeros': len(pasajeros),
            'pasajeros': pasajeros
        }
    
    @staticmethod
    def iniciar_abordaje(vuelo_id):
        """Cambia el estado del vuelo a abordando"""
        vuelo = VueloRepository.obtener_por_id(vuelo_id)
        if not vuelo:
            raise ValidationError("El vuelo no existe")
        
        if vuelo.estado != 'programado':
            raise ValidationError("El vuelo no está en estado programado")
        
        return VueloRepository.cambiar_estado(vuelo_id, 'abordando')
    
    @staticmethod
    def iniciar_vuelo(vuelo_id):
        """Cambia el estado del vuelo a en_vuelo"""
        vuelo = VueloRepository.obtener_por_id(vuelo_id)
        if not vuelo:
            raise ValidationError("El vuelo no existe")
        
        if vuelo.estado != 'abordando':
            raise ValidationError("El vuelo debe estar en estado abordando")
        
        return VueloRepository.cambiar_estado(vuelo_id, 'en_vuelo')
    
    @staticmethod
    def completar_vuelo(vuelo_id):
        """Marca el vuelo como completado"""
        vuelo = VueloRepository.obtener_por_id(vuelo_id)
        if not vuelo:
            raise ValidationError("El vuelo no existe")
        
        if vuelo.estado != 'en_vuelo':
            raise ValidationError("El vuelo debe estar en estado en_vuelo")
        
        return VueloRepository.cambiar_estado(vuelo_id, 'completado')