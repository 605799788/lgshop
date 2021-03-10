from django.urls import path

from .views import QQAuthURLView


urlpatterns = [
    # 生成qq链接
    path("qq/login/", QQAuthURLView.as_view())

]