from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Outfit
from .serializers import OutfitSerializer
from .filters import OutfitFilter


class OutfitViewSet(viewsets.ModelViewSet):
    serializer_class = OutfitSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = OutfitFilter
    search_fields = ['name']
    ordering_fields = ['created_at', 'name', 'is_favorite']
    ordering = ['-created_at']

    def get_queryset(self):
        return (
            Outfit.objects.filter(user=self.request.user)
            .prefetch_related('clothes')
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='toggle-favorite')
    def toggle_favorite(self, request, pk=None):
        outfit = self.get_object()
        outfit.is_favorite = not outfit.is_favorite
        outfit.save(update_fields=['is_favorite', 'updated_at'])
        
        return Response(
            {
                'id': outfit.id,
                'name': outfit.name,
                'is_favorite': outfit.is_favorite
            },
            status=status.HTTP_200_OK
        )