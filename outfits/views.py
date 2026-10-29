from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Outfit
from .serializers import OutfitSerializer


class OutfitViewSet(viewsets.ModelViewSet):
    serializer_class = OutfitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Outfit.objects.filter(user=self.request.user)
            .prefetch_related('clothes')
            .order_by('-created_at')
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)