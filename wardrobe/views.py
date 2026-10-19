import requests
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters import rest_framework as django_filters

from .models import ClothingItem
from .serializers import ClothingItemSerializer, ClothingItemFromURLSerializer
from .services import extract_image_from_url


class ClothingItemFilter(django_filters.FilterSet):
    category = django_filters.ChoiceFilter(
        choices=ClothingItem.Category.choices,
        empty_label='Todas las categorías'
    )

    class Meta:
        model = ClothingItem
        fields = ['category', 'color', 'brand']


class ClothingItemViewSet(viewsets.ModelViewSet):
    serializer_class = ClothingItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ClothingItemFilter
    search_fields = ['name', 'brand', 'color']
    ordering_fields = ['created_at', 'price', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        return ClothingItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='import-url')
    def import_from_url(self, request):
        serializer = ClothingItemFromURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        url = serializer.validated_data['url']

        try:
            image_file = extract_image_from_url(url)
        except requests.RequestException as e:
            return Response(
                {"error": f"Error al conectar con la tienda: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Creamos la instancia asignando el archivo descargado
        item = ClothingItem(
            user=request.user,
            name=serializer.validated_data['name'],
            category=serializer.validated_data['category'],
            brand=serializer.validated_data.get('brand', ''),
            color=serializer.validated_data.get('color', ''),
            price=serializer.validated_data.get('price', 0.00),
            image=image_file,
        )
        # item.save() ejecutará automáticamente el recorte con rembg
        item.save()

        output_serializer = ClothingItemSerializer(item)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)