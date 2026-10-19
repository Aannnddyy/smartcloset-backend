from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import ClothingItem
from .serializers import ClothingItemSerializer

class ClothingItemViewSet(viewsets.ModelViewSet):
    serializer_class = ClothingItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # Cada usuario solo puede ver y manipular sus propias prendas
        return ClothingItem.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
       # Asigna automáticamente el usuario autenticado al crear la prenda
        serializer.save(user=self.request.user)