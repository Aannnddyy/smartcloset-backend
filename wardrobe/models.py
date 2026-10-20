from django.db import models
from django.contrib.auth.models import User
from .services import remove_background_and_crop


class ClothingItem(models.Model):
    class Category(models.TextChoices):
        TOP = 'TOP', 'Parte de arriba'
        BOTTOM = 'BOTTOM', 'Parte de abajo'
        DRESS = 'DRESS', 'Vestido / Mono'
        OUTERWEAR = 'OUTERWEAR', 'Abrigo / Chaqueta'
        SHOES = 'SHOES', 'Calzado'
        ACCESSORY = 'ACCESSORY', 'Accesorio'

    # Relación con el usuario propietario
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clothes')
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=Category.choices)

    # Vista Frontal
    image = models.ImageField(upload_to='clothes/%Y/%m/')
    processed_image = models.ImageField(
        upload_to='clothes/processed/%Y/%m/',
        blank=True,
        null=True
    )

    # Vista Trasera (Opcional)
    back_image = models.ImageField(
        upload_to='clothes/back/%Y/%m/',
        blank=True,
        null=True
    )
    processed_back_image = models.ImageField(
        upload_to='clothes/processed_back/%Y/%m/',
        blank=True,
        null=True
    )

    brand = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Procesa imagen frontal si existe y aún no tiene versión recortada
        if self.image and not self.processed_image:
            self.processed_image = remove_background_and_crop(self.image)

        # Procesa imagen trasera si se proporciona y aún no tiene versión recortada
        if self.back_image and not self.processed_back_image:
            self.processed_back_image = remove_background_and_crop(self.back_image)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"