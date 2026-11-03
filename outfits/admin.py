from django.contrib import admin
from .models import Outfit


@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'season', 'occasion', 'is_favorite', 'created_at')
    list_filter = ('season', 'occasion', 'is_favorite', 'created_at')
    search_fields = ('name', 'user__username')
    filter_horizontal = ('clothes',)  # Crea un selector cómodo de doble columna para las prendas