from django.contrib import admin
from .models import ClothingItem

@admin.register(ClothingItem)
class ClothingItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'user', 'created_at')
    list_filter = ('category', 'user')
    search_fields = ('name', 'brand')