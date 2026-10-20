import requests
from django_filters import rest_framework as django_filters
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import ClothingItem
from .serializers import (
    ClothingItemFromURLSerializer,
    ClothingItemSerializer,
    URLPreviewSerializer,
)
from .services import download_image_from_url, extract_product_preview


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

    @action(detail=False, methods=['post'], url_path='extract-preview')
    def extract_preview(self, request):
        """
        Paso 1: Recibe la URL del producto de cualquier tienda, renderiza
        con Playwright y devuelve las imágenes candidatas y el título sugerido.
        """
        serializer = URLPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_url = serializer.validated_data['url']

        try:
            preview_data = extract_product_preview(target_url)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error al procesar la tienda con el navegador: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        return Response(preview_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='import-url')
    def import_from_url(self, request):
        """
        Paso 2: Recibe la imagen frontal (y trasera opcional) elegida por
        el usuario, las descarga y crea el ClothingItem procesando ambas con rembg.
        """
        serializer = ClothingItemFromURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        front_url = serializer.validated_data['front_image_url']
        back_url = serializer.validated_data.get('back_image_url')

        # 1. Descarga de imagen frontal obligatoria
        try:
            front_file = download_image_from_url(front_url)
        except (requests.RequestException, ValueError) as e:
            return Response(
                {"error": f"Error al descargar la imagen frontal: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Descarga de imagen trasera opcional (si el usuario la seleccionó)
        back_file = None
        if back_url:
            try:
                back_file = download_image_from_url(back_url)
            except (requests.RequestException, ValueError) as e:
                return Response(
                    {"error": f"Error al descargar la imagen trasera: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 3. Creación de la prenda
        item = ClothingItem(
            user=request.user,
            name=serializer.validated_data['name'],
            category=serializer.validated_data['category'],
            brand=serializer.validated_data.get('brand', ''),
            color=serializer.validated_data.get('color', ''),
            price=serializer.validated_data.get('price', 0.00),
            image=front_file,
            back_image=back_file,
        )

        # item.save() ejecuta automáticamente rembg para frontal y trasera
        item.save()

        output_serializer = ClothingItemSerializer(item)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)