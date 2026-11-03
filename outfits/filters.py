import django_filters
from .models import Outfit


class OutfitFilter(django_filters.FilterSet):
    class Meta:
        model = Outfit
        fields = {
            'season': ['exact'],
            'occasion': ['exact'],
            'is_favorite': ['exact'],
        }