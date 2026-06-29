from rest_framework.routers import DefaultRouter

from apps.gallery.views import GalleryAlbumViewSet, GalleryImageViewSet

router = DefaultRouter()
router.register("gallery/albums", GalleryAlbumViewSet, basename="gallery-album")
router.register("gallery/images", GalleryImageViewSet, basename="gallery-image")

urlpatterns = router.urls
