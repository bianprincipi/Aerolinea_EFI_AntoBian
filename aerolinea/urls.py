from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AvionViewSet,
    VueloViewSet,
    PasajeroViewSet,
    ReservaViewSet,
    BoletoViewSet
)

# Crear el router de DRF
router = DefaultRouter()

# Registrar los ViewSets
router.register(r'aviones', AvionViewSet, basename='avion')
router.register(r'vuelos', VueloViewSet, basename='vuelo')
router.register(r'pasajeros', PasajeroViewSet, basename='pasajero')
router.register(r'reservas', ReservaViewSet, basename='reserva')
router.register(r'boletos', BoletoViewSet, basename='boleto')

# URLs de la app
urlpatterns = [
    path('', include(router.urls)),
]