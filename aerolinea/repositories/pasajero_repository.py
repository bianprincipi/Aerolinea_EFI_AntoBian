from django.db.models import Q
from ..models import Pasajero


class PasajeroRepository:
    """Repository para gestionar consultas de pasajeros"""
    
    @staticmethod
    def obtener_todos():
        """Obtiene todos los pasajeros"""
        return Pasajero.objects.all()
    
    @staticmethod
    def obtener_por_id(pasajero_id):
        """Obtiene un pasajero por su ID"""
        try:
            return Pasajero.objects.get(id=pasajero_id)
        except Pasajero.DoesNotExist:
            return None
    
    @staticmethod
    def obtener_por_documento(documento):
        """Obtiene un pasajero por su documento"""
        try:
            return Pasajero.objects.get(documento=documento)
        except Pasajero.DoesNotExist:
            return None
    
    @staticmethod
    def obtener_por_email(email):
        """Obtiene un pasajero por su email"""
        try:
            return Pasajero.objects.get(email=email)
        except Pasajero.DoesNotExist:
            return None
    
    @staticmethod
    def buscar(termino):
        """Busca pasajeros por nombre, apellido o documento"""
        return Pasajero.objects.filter(
            Q(nombre__icontains=termino) |
            Q(apellido__icontains=termino) |
            Q(documento__icontains=termino)
        )
    
    @staticmethod
    def crear_pasajero(datos):
        """Crea un nuevo pasajero"""
        return Pasajero.objects.create(**datos)
    
    @staticmethod
    def actualizar_pasajero(pasajero_id, datos):
        """Actualiza un pasajero"""
        Pasajero.objects.filter(id=pasajero_id).update(**datos)
        return PasajeroRepository.obtener_por_id(pasajero_id)
    
    @staticmethod
    def eliminar_pasajero(pasajero_id):
        """Elimina un pasajero"""
        pasajero = PasajeroRepository.obtener_por_id(pasajero_id)
        if pasajero:
            pasajero.delete()
            return True
        return False
    
    @staticmethod
    def existe_documento(documento):
        """Verifica si un documento ya está registrado"""
        return Pasajero.objects.filter(documento=documento).exists()
    
    @staticmethod
    def existe_email(email):
        """Verifica si un email ya está registrado"""
        return Pasajero.objects.filter(email=email).exists()