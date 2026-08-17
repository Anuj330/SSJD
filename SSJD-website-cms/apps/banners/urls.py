from rest_framework.routers import DefaultRouter

from apps.banners.views import BannerViewSet

router = DefaultRouter()
router.register("banners", BannerViewSet, basename="banner")

urlpatterns = router.urls
