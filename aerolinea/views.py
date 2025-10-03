from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.core.exceptions import ValidationError
from datetime import datetime

from .models import Avion, Vuelo, Pasajero, Reserva, Boleto, Asiento
from .serializers import (
    AvionSerializer, VueloSerializer, PasajeroSerializer, 
    ReservaSerializer, BoletoSerializer, AsientoSerializer,
    ReportePasajerosVueloSerializer, UsuarioSerializer,
    UsuarioRegistroSerializer
)
from .services.vuelo_service import VueloService
from .services.reserva_service import ReservaService
from .services.pasajero_service import PasajeroService
from .services.boleto_service import BoletoService


class AvionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar aviones"""
    queryset = Avion.objects.all()
    serializer_class = AvionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(detail=True, methods=['get'])
    def asientos(self, request, pk=None):
        """Obtiene el layout de asientos de un avión"""
        avion = self.get_object()
        asientos = avion.asientos.all()
        serializer = AsientoSerializer(asientos, many=True)
        return Response(serializer.data)


class VueloViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar vuelos"""
    queryset = Vuelo.objects.select_related('avion').all()
    serializer_class = VueloSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['origen', 'destino', 'estado']
    search_fields = ['codigo_vuelo', 'origen', 'destino']
    ordering_fields = ['fecha_salida', 'precio_base']
    ordering = ['-fecha_salida']
    
    def get_queryset(self):
        """Filtra vuelos según parámetros"""
        queryset = super().get_queryset()
        
        # Filtrar por fecha
        fecha = self.request.query_params.get('fecha', None)
        if fecha:
            try:
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_salida__date=fecha_obj)
            except ValueError:
                pass
        
        # Filtrar vuelos disponibles
        disponibles = self.request.query_params.get('disponibles', None)
        if disponibles == 'true':
            queryset = queryset.filter(
                estado='programado',
                fecha_salida__gte=datetime.now()
            )
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Crea un nuevo vuelo con validaciones"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            vuelo = VueloService.crear_vuelo(serializer.validated_data)
            output_serializer = self.get_serializer(vuelo)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def asientos_disponibles(self, request, pk=None):
        """Obtiene los asientos disponibles de un vuelo"""
        try:
            asientos = VueloService.obtener_asientos_disponibles(pk)
            serializer = AsientoSerializer(asientos, many=True)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def pasajeros(self, request, pk=None):
        """Obtiene el listado de pasajeros de un vuelo"""
        try:
            reporte = VueloService.obtener_reporte_pasajeros(pk)
            serializer = ReportePasajerosVueloSerializer(reporte)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancela un vuelo"""
        try:
            vuelo = VueloService.cancelar_vuelo(pk)
            serializer = self.get_serializer(vuelo)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def iniciar_abordaje(self, request, pk=None):
        """Cambia el estado del vuelo a abordando"""
        try:
            vuelo = VueloService.iniciar_abordaje(pk)
            serializer = self.get_serializer(vuelo)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def iniciar_vuelo(self, request, pk=None):
        """Cambia el estado del vuelo a en_vuelo"""
        try:
            vuelo = VueloService.iniciar_vuelo(pk)
            serializer = self.get_serializer(vuelo)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        """Marca el vuelo como completado"""
        try:
            vuelo = VueloService.completar_vuelo(pk)
            serializer = self.get_serializer(vuelo)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PasajeroViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar pasajeros"""
    queryset = Pasajero.objects.all()
    serializer_class = PasajeroSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ['nombre', 'apellido', 'documento', 'email']
    ordering_fields = ['apellido', 'nombre', 'fecha_registro']
    ordering = ['apellido', 'nombre']
    
    def create(self, request, *args, **kwargs):
        """Crea un nuevo pasajero con validaciones"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            pasajero = PasajeroService.crear_pasajero(serializer.validated_data)
            output_serializer = self.get_serializer(pasajero)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Actualiza un pasajero"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            pasajero = PasajeroService.actualizar_pasajero(instance.id, serializer.validated_data)
            output_serializer = self.get_serializer(pasajero)
            return Response(output_serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def reservas(self, request, pk=None):
        """Obtiene todas las reservas de un pasajero"""
        try:
            reservas = ReservaService.obtener_reservas_pasajero(pk)
            serializer = ReservaSerializer(reservas, many=True)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def reservas_activas(self, request, pk=None):
        """Obtiene las reservas activas de un pasajero"""
        try:
            reservas = ReservaService.obtener_reservas_activas_pasajero(pk)
            serializer = ReservaSerializer(reservas, many=True)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        """Obtiene el historial de vuelos de un pasajero"""
        try:
            historial = PasajeroService.obtener_historial_vuelos(pk)
            serializer = ReservaSerializer(historial, many=True)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)


class ReservaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar reservas"""
    queryset = Reserva.objects.select_related('vuelo', 'pasajero', 'asiento').all()
    serializer_class = ReservaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['estado', 'vuelo', 'pasajero']
    search_fields = ['codigo_reserva', 'pasajero__nombre', 'pasajero__apellido']
    ordering_fields = ['fecha_reserva']
    ordering = ['-fecha_reserva']
    
    def create(self, request, *args, **kwargs):
        """Crea una nueva reserva"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            vuelo_id = serializer.validated_data['vuelo'].id
            pasajero_id = serializer.validated_data['pasajero'].id
            asiento_id = serializer.validated_data['asiento'].id
            precio = serializer.validated_data.get('precio')
            
            reserva = ReservaService.crear_reserva(vuelo_id, pasajero_id, asiento_id, precio)
            output_serializer = self.get_serializer(reserva)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """Confirma una reserva y genera el boleto"""
        try:
            reserva = ReservaService.confirmar_reserva(pk)
            serializer = self.get_serializer(reserva)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancela una reserva"""
        try:
            reserva = ReservaService.cancelar_reserva(pk)
            serializer = self.get_serializer(reserva)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def por_codigo(self, request):
        """Busca una reserva por código"""
        codigo = request.query_params.get('codigo', None)
        if not codigo:
            return Response({'error': 'Se requiere el parámetro codigo'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        try:
            reserva = ReservaService.obtener_reserva_por_codigo(codigo)
            serializer = self.get_serializer(reserva)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)


class BoletoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar boletos (solo lectura)"""
    queryset = Boleto.objects.select_related('reserva', 'reserva__vuelo', 'reserva__pasajero').all()
    serializer_class = BoletoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ['codigo_barra']
    ordering_fields = ['fecha_emision']
    ordering = ['-fecha_emision']
    
    @action(detail=False, methods=['get'])
    def por_codigo(self, request):
        """Busca un boleto por código de barra"""
        codigo = request.query_params.get('codigo', None)
        if not codigo:
            return Response({'error': 'Se requiere el parámetro codigo'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        try:
            boleto = BoletoService.obtener_por_codigo(codigo)
            serializer = self.get_serializer(boleto)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def verificar(self, request):
        """Verifica la validez de un boleto"""
        codigo = request.data.get('codigo_barra', None)
        if not codigo:
            return Response({'error': 'Se requiere el código de barra'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        try:
            resultado = BoletoService.verificar_boleto(codigo)
            if resultado['valido']:
                serializer = self.get_serializer(resultado['boleto'])
                return Response({
                    'valido': True,
                    'mensaje': resultado['mensaje'],
                    'boleto': serializer.data
                })
            else:
                return Response({
                    'valido': False,
                    'mensaje': resultado['mensaje']
                }, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def usar(self, request):
        """Marca un boleto como usado (check-in)"""
        codigo = request.data.get('codigo_barra', None)
        if not codigo:
            return Response({'error': 'Se requiere el código de barra'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        try:
            boleto = BoletoService.usar_boleto(codigo)
            serializer = self.get_serializer(boleto)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)