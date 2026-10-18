from rest_framework import viewsets, permissions
from .models import ClothingItem
from .serializers import ClothingItemSerializer

class ClothingItemViewSet(viewsets.ModelViewSet):
    serializer_class = ClothingItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Un usuario SOLO debe ver sus propias prendas, nunca las de otros
        return ClothingItem.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # Asigna automáticamente el usuario que hace la petición como dueño de la prenda
        serializer.save(user=self.request.user)