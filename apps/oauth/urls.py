from django.urls import path

from .views import QQAuthURLView, QQAuthUserView


urlpatterns = [
    # 生成qq链接
    path("qq/login/", QQAuthURLView.as_view()),

    path('oauth_callback/', QQAuthUserView.as_view()),

]