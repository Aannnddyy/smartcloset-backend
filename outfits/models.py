from django.conf import settings
from django.db import models


class Outfit(models.Model):
    class Season(models.TextChoices):
        SPRING = 'SPRING', 'Primavera'
        SUMMER = 'SUMMER', 'Verano'
        AUTUMN = 'AUTUMN', 'Otoño'
        WINTER = 'WINTER', 'Invierno'
        ALL = 'ALL', 'Todas las estaciones'

    class Occasion(models.TextChoices):
        CASUAL = 'CASUAL', 'Casual'
        FORMAL = 'FORMAL', 'Formal'
        WORK = 'WORK', 'Trabajo'
        SPORT = 'SPORT', 'Deporte'
        PARTY = 'PARTY', 'Fiesta'
        OTHER = 'OTHER', 'Otro'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='outfits'
    )
    name = models.CharField(max_length=150, default='Nuevo Outfit')
    clothes = models.ManyToManyField(
        'wardrobe.ClothingItem',
        related_name='outfits',
        blank=False
    )
    season = models.CharField(
        max_length=20,
        choices=Season.choices,
        default=Season.ALL
    )
    occasion = models.CharField(
        max_length=20,
        choices=Occasion.choices,
        default=Occasion.CASUAL
    )
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"