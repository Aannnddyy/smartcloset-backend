from rest_framework import serializers
from wardrobe.models import ClothingItem
from wardrobe.serializers import ClothingItemSerializer
from .models import Outfit
from .services.canvas import OutfitCanvasGenerator


class OutfitSerializer(serializers.ModelSerializer):
    clothes = ClothingItemSerializer(many=True, read_only=True)
    clothes_ids = serializers.PrimaryKeyRelatedField(
        queryset=ClothingItem.objects.all(),
        many=True,
        write_only=True,
        source='clothes'
    )
    season_display = serializers.CharField(source='get_season_display', read_only=True)
    occasion_display = serializers.CharField(source='get_occasion_display', read_only=True)

    class Meta:
        model = Outfit
        fields = [
            'id',
            'user',
            'name',
            'clothes',
            'clothes_ids',
            'canvas_image',
            'season',
            'season_display',
            'occasion',
            'occasion_display',
            'is_favorite',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'canvas_image', 'created_at', 'updated_at']

    def validate_clothes_ids(self, value):
        if not value:
            raise serializers.ValidationError("Un outfit debe contener al menos una prenda.")
        user = self.context['request'].user
        for item in value:
            if item.user != user:
                raise serializers.ValidationError("Solo puedes incluir prendas que pertenezcan a tu armario.")
        return value

    def _generate_canvas(self, outfit, clothes):
        """
        Llama al generador de Pillow con las prendas asociadas y guarda
        el resultado en el campo canvas_image del outfit.
        """
        generator = OutfitCanvasGenerator(clothes=list(clothes))
        canvas_file = generator.generate()
        if canvas_file:
            # save=True guarda el archivo en disco/media y actualiza la base de datos
            filename = f"outfit_{outfit.id}_canvas.jpg"
            outfit.canvas_image.save(filename, canvas_file, save=True)

    def create(self, validated_data):
        clothes = validated_data.pop('clothes')
        outfit = Outfit.objects.create(**validated_data)
        outfit.clothes.set(clothes)
        
        # Generar el canvas con las prendas recién asociadas
        self._generate_canvas(outfit, clothes)
        
        return outfit

    def update(self, instance, validated_data):
        clothes = validated_data.pop('clothes', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        
        if clothes is not None:
            instance.clothes.set(clothes)
            # Si cambiaron las prendas del look, regeneramos el canvas
            self._generate_canvas(instance, clothes)
            
        return instance