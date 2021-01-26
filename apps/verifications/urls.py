from django.urls import path, re_path

from .views import ImageVIew
# app_name = 'verification'

urlpatterns = [
    re_path(r'^image_codes/(?P<uuid>[\w-]+)/$', ImageVIew.as_view()),
]