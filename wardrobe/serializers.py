from rest_framework import serializers
from .models import ClothingItem


def validate_file_image(value):
    # Valida peso y formato de imagen tanto para frontal como para trasera.
    max_size_mb = 10
    if value.size > max_size_mb * 1024 * 1024:
        raise serializers.ValidationError(
            f"La imagen es demasiado pesada. El tamaño máximo permitido es de {max_size_mb} MB."
        )

    valid_content_types = ['image/jpeg', 'image/png', 'image/webp']
    content_type = getattr(value, 'content_type', None)
    if content_type and content_type not in valid_content_types:
        raise serializers.ValidationError(
            "Formato no compatible. Sube una imagen en formato JPG, PNG o WebP."
        )

    return value


class ClothingItemSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = ClothingItem
        fields = [
            'id',
            'user',
            'name',
            'category',
            'category_display',
            # Vista Frontal
            'image',
            'processed_image',
            # Vista Trasera (opcional)
            'back_image',
            'processed_back_image',
            'brand',
            'color',
            'price',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'processed_image',
            'processed_back_image',
            'created_at',
            'category_display',
        ]

    def validate_image(self, value):
        return validate_file_image(value)

    def validate_back_image(self, value):
        if value:
            return validate_file_image(value)
        return value


# Paso 1: Recibe la URL de la tienda para inspeccionar y extraer todas las fotos candidatas
class URLPreviewSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)


# Paso 2: Recibe los datos finales con las fotos elegidas por el usuario
class ClothingItemFromURLSerializer(serializers.Serializer):
    front_image_url = serializers.URLField(required=True)
    back_image_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    name = serializers.CharField(max_length=150, required=True)
    category = serializers.ChoiceField(choices=ClothingItem.Category.choices, required=True)
    brand = serializers.CharField(max_length=100, required=False, allow_blank=True)
    color = serializers.CharField(max_length=50, required=False, allow_blank=True)
    price = serializers.DecimalField(max_digits=7, decimal_places=2, required=False, default=0.00)