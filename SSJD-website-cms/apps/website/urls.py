from django.urls import path

from apps.website.views import home

urlpatterns = [
    path("", home, name="home"),
]
