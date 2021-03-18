from django.urls import path, re_path

from .views import RegisterView, UsernameCountView, LoginView, LogoutView, DefaultAddressView
from .views import UserInfotView, EmailView, VerifyEmailView, AddressView
from .views import AddressCreateView, UpdateDestoryAddressView, ChangPWDView
app_name = 'users'

urlpatterns = [
    # 注册
    path('register/', RegisterView.as_view(), name='register'),
    # 判断用户是否重复
    re_path(r'^usernames/(?P<username>[a-zA-Z0-9-_]{5,20})/count/$',
            UsernameCountView.as_view()),

    path('login/', LoginView.as_view(), name='login'),

    path('logout/', LogoutView.as_view(), name='logout'),
    # 个人中心
    path('info/', UserInfotView.as_view(), name='info'),
    # 保存邮件
    path('email/', EmailView.as_view()),
    # 激活邮箱请求
    path('emails/verification/', VerifyEmailView.as_view()),
    # 收货地址
    path('addresses/', AddressView.as_view(), name='address'),
    # 新增收件人
    path('addresses/create/', AddressCreateView.as_view()),
    # 更改地址
    re_path(r'^addresses/(?P<address_id>\d+)/$', UpdateDestoryAddressView.as_view()),
    # 新增收件人
    path('pwd/', ChangPWDView.as_view(), name='pwd'),
    # 设置默认收货地址
    re_path(r'^addresses/(?P<address_id>\d+)/default/$', DefaultAddressView.as_view())

]