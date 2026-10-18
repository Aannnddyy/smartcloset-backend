from django.db import models
from django.contrib.auth.models import User

class ClothingItem(models.Model):
    class Category(models.TextChoices):
        TOP = 'TOP', 'Parte de arriba'
        BOTTOM = 'BOTTOM', 'Parte de abajo'
        DRESS = 'DRESS', 'Vestido / Mono'
        OUTERWEAR = 'OUTERWEAR', 'Abrigo / Chaqueta'
        SHOES = 'SHOES', 'Calzado'
        ACCESSORY = 'ACCESSORY', 'Accesorio'

    # Relacionamos cada prenda con un usuario
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clothes')
    
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=Category.choices)
    
    # Foto de la prenda (se guardará dentro de media/clothes/...)
    image = models.ImageField(upload_to='clothes/%Y/%m/')
    
    brand = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"