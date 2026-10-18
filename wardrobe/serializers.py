from rest_framework import serializers
from .models import ClothingItem

class ClothingItemSerializer(serializers.ModelSerializer):
    # Campo extra de solo lectura para ver la categoría en texto legible
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = ClothingItem
        fields = [
            'id',
            'name',
            'category',
            'category_display',
            'image',
            'brand',
            'color',
            'price',
            'created_at',
        ]
        # El usuario no se pasa a mano en el JSON; lo asignará el servidor automáticamente
        read_only_fields = ['id', 'created_at']