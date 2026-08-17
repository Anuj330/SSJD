from rest_framework.routers import DefaultRouter

from apps.schemes.views import SchemeViewSet

router = DefaultRouter()
router.register("schemes", SchemeViewSet, basename="scheme")

urlpatterns = router.urls
