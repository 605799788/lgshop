from django.urls import path, re_path

from .views import RegisterView, UsernameCountView, LoginView

app_name = 'users'

urlpatterns = [
    # 注册
    path('register/', RegisterView.as_view(), name='register'),
    # 判断用户是否重复
    re_path(r'^usernames/(?P<username>[a-zA-Z0-9-_]{5,20})/count/$',
            UsernameCountView.as_view()),

    path('login/', LoginView.as_view(), name='login')

]