from django.core.exceptions import ValidationError
from datetime import date
from ..repositories.pasajero_repository import PasajeroRepository


class PasajeroService:
    """Service para la lógica de negocio de pasajeros"""
    
    @staticmethod
    def listar_pasajeros():
        """Lista todos los pasajeros"""
        return PasajeroRepository.obtener_todos()
    
    @staticmethod
    def obtener_pasajero(pasajero_id):
        """Obtiene un pasajero por ID"""
        pasajero = PasajeroRepository.obtener_por_id(pasajero_id)
        if not pasajero:
            raise ValidationError("El pasajero no existe")
        return pasajero
    
    @staticmethod
    def obtener_pasajero_por_documento(documento):
        """Obtiene un pasajero por su documento"""
        pasajero = PasajeroRepository.obtener_por_documento(documento)
        if not pasajero:
            raise ValidationError("El pasajero no existe")
        return pasajero
    
    @staticmethod
    def buscar_pasajeros(termino):
        """Busca pasajeros por nombre, apellido o documento"""
        if not termino or len(termino) < 2:
            raise ValidationError("El término de búsqueda debe tener al menos 2 caracteres")
        
        return PasajeroRepository.buscar(termino)
    
    @staticmethod
    def crear_pasajero(datos):
        """Crea un nuevo pasajero con validaciones"""
        if PasajeroRepository.existe_documento(datos['documento']):
            raise ValidationError("Ya existe un pasajero con ese documento")
        
        if PasajeroRepository.existe_email(datos['email']):
            raise ValidationError("Ya existe un pasajero con ese email")
        
        fecha_nacimiento = datos.get('fecha_nacimiento')
        if fecha_nacimiento:
            edad = PasajeroService._calcular_edad(fecha_nacimiento)
            if edad < 0:
                raise ValidationError("La fecha de nacimiento no puede ser en el futuro")
            if edad > 120:
                raise ValidationError("La fecha de nacimiento no es válida")
        
        campos_requeridos = ['nombre', 'apellido', 'tipo_documento', 'documento', 'email', 'telefono']
        for campo in campos_requeridos:
            if campo not in datos or not datos[campo]:
                raise ValidationError(f"El campo {campo} es requerido")
        
        return PasajeroRepository.crear_pasajero(datos)
    
    @staticmethod
    def actualizar_pasajero(pasajero_id, datos):
        """Actualiza un pasajero"""
        pasajero = PasajeroRepository.obtener_por_id(pasajero_id)
        if not pasajero:
            raise ValidationError("El pasajero no existe")
        
        if 'documento' in datos and datos['documento'] != pasajero.documento:
            if PasajeroRepository.existe_documento(datos['documento']):
                raise ValidationError("Ya existe un pasajero con ese documento")
        
        if 'email' in datos and datos['email'] != pasajero.email:
            if PasajeroRepository.existe_email(datos['email']):
                raise ValidationError("Ya existe un pasajero con ese email")
        
        return PasajeroRepository.actualizar_pasajero(pasajero_id, datos)
    
    @staticmethod
    def eliminar_pasajero(pasajero_id):
        """Elimina un pasajero"""
        pasajero = PasajeroRepository.obtener_por_id(pasajero_id)
        if not pasajero:
            raise ValidationError("El pasajero no existe")
        
        from ..repositories.reserva_repository import ReservaRepository
        reservas_activas = ReservaRepository.obtener_activas_pasajero(pasajero_id)
        if reservas_activas:
            raise ValidationError("No se puede eliminar un pasajero con reservas activas")
        
        return PasajeroRepository.eliminar_pasajero(pasajero_id)
    
    @staticmethod
    def obtener_historial_vuelos(pasajero_id):
        """Obtiene el historial de vuelos de un pasajero"""
        pasajero = PasajeroRepository.obtener_por_id(pasajero_id)
        if not pasajero:
            raise ValidationError("El pasajero no existe")
        
        from ..repositories.reserva_repository import ReservaRepository
        return ReservaRepository.obtener_por_pasajero(pasajero_id)
    
    @staticmethod
    def _calcular_edad(fecha_nacimiento):
        """Calcula la edad a partir de la fecha de nacimiento"""
        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year
        
        if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
            edad -= 1
        
        return edad