from rest_framework import serializers
from .models import ClothingItem

class ClothingItemSerializer(serializers.ModelSerializer):
    # Campo extra de solo lectura para ver la categoría en texto legible
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = ClothingItem
        fields = [
            'id',
            'user',
            'name',
            'category',
            'category_display',
            'image',
            'processed_image',
            'brand',
            'color',
            'price',
            'created_at',
        ]
        # El usuario no se pasa a mano en el JSON; lo asignará el servidor automáticamente
        read_only_fields = ['id', 'user', 'processed_image', 'created_at', 'category_display']

        def validate_image(self, value):
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

# Actúa como un formulario de validación puro en memoria
class ClothingItemFromURLSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)
    name = serializers.CharField(max_length=100, required=True)
    category = serializers.ChoiceField(choices=ClothingItem.Category.choices, required=True)
    brand = serializers.CharField(max_length=50, required=False, allow_blank=True)
    color = serializers.CharField(max_length=30, required=False, allow_blank=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0.00)