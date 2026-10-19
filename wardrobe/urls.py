from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClothingItemViewSet

router = DefaultRouter()
router.register(r'clothes', ClothingItemViewSet, basename='clothing-item')

urlpatterns = [
    path('', include(router.urls)),
]