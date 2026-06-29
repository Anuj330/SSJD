from django.contrib import admin

from apps.gallery.models import GalleryAlbum, GalleryImage
from core.admin import BaseModelAdmin


class GalleryImageInline(admin.TabularInline):
    model = GalleryImage
    extra = 3
    fields = ("image", "title", "display_order")


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(BaseModelAdmin):
    list_display = ("title", "category", "event_date", "is_active")
    list_editable = ("is_active",)
    list_filter = ("category", "is_active")
    search_fields = ("title", "category")
    inlines = [GalleryImageInline]


@admin.register(GalleryImage)
class GalleryImageAdmin(BaseModelAdmin):
    list_display = ("title", "album", "display_order")
    list_filter = ("album",)
    search_fields = ("title",)
