from django.urls import path

from apps.sitesettings.views import SiteSettingView

urlpatterns = [
    path("settings/", SiteSettingView.as_view(), name="site-settings"),
]
