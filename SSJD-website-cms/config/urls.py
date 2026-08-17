"""Root URL configuration.

Public + CMS REST API is mounted under /api/v1/. Each app owns its router.
Swagger / ReDoc are served from /api/docs/ and /api/redoc/.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as media_serve
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

api_v1 = [
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.banners.urls")),
    path("", include("apps.schemes.urls")),
    path("", include("apps.notices.urls")),
    path("", include("apps.branches.urls")),
    path("", include("apps.gallery.urls")),
    path("", include("apps.pages.urls")),
    path("", include("apps.testimonials.urls")),
    path("", include("apps.contacts.urls")),
    path("", include("apps.sitesettings.urls")),
    path("", include("apps.dashboard.urls")),
]

urlpatterns = [
    path("", include("apps.website.urls")),
    path("admin/", admin.site.urls),
    path("ckeditor/", include("ckeditor_uploader.urls")),
    path("api/v1/", include((api_v1, "api"), namespace="v1")),
    # API schema + docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# Serve user-uploaded media in production too (Django only auto-serves it in
# DEBUG). Fine for this site's traffic; gunicorn streams the file. For higher
# scale, move media to S3 (MEDIA_STORAGE=s3) or let Caddy serve the volume.
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", media_serve, {"document_root": settings.MEDIA_ROOT}),
]
