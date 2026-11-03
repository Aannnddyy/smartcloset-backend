from rest_framework.routers import DefaultRouter
from .views import OutfitViewSet

router = DefaultRouter()
router.register(r'', OutfitViewSet, basename='outfit')

urlpatterns = router.urls