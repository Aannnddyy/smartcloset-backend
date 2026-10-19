from rest_framework import viewsets, permissions, filters
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from .models import ClothingItem
from .serializers import ClothingItemSerializer

class ClothingItemViewSet(viewsets.ModelViewSet):
    serializer_class = ClothingItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    # Activamos los tres motores de consulta:
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    # Filtros exactos por campo
    filterset_fields = ['category', 'color', 'brand']
    
    # Búsqueda por texto (nombre de la prenda, marca o color)
    search_fields = ['name', 'brand', 'color']
    
    # Ordenación permitida
    ordering_fields = ['created_at', 'price', 'name']
    ordering = ['-created_at']  # Por defecto: las prendas más recientes primero

    def get_queryset(self):
        # Cada usuario solo puede ver y manipular sus propias prendas
        return ClothingItem.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
       # Asigna automáticamente el usuario autenticado al crear la prenda
        serializer.save(user=self.request.user)