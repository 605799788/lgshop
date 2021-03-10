from django.views import View
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, authenticate, logout
from django_redis import get_redis_connection
from django.contrib.auth.hashers import check_password
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.conf import settings

# from users.models import User
from .forms import RegisterForm, LoginForm
from .models import User
from utils.views import LoginRequiredJSONMixin
from celery_tasks.email.tasks import send_verify_email

from utils.response_code import RETCODE
from .utils import generate_verify_email_url, check_verify_email_token

import json, re

# Create your views here.


class VerifyEmailView(View):

    def get(self, request):
        # 1. 接收
        token = request.GET.get('token')
        if not token:
            return HttpResponseForbidden('缺少token')
        # 2.解密  对比加密参数
        user = check_verify_email_token(token)
        if user.email_active == 0:
            user.email_active = True
            user.save()
        else:
            return HttpResponseForbidden("邮箱已经激活")
        # 3.查询用户判断是否唯一  更改email_active是否已经激活为True，没有则激活

        # 4.响应结果
        return redirect(reverse('users:info'))


class EmailView(LoginRequiredJSONMixin, View):
    """邮箱发送"""

    def put(self, request):
        """
        put请求内容在body里
        :param request:
        :return:
        """
        # print(request)
        # 接受参数
        json_str = request.body.decode()
        # print(json_str) # 此时是一个字符串
        json_dict = json.loads(json_str)
        email = json_dict.get('email')
        # 校验参数
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return HttpResponseForbidden('参数邮箱格式有误')
        # 保存
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})
        # 发送邮件
        # subject = "商城邮箱验证"
        # html_message = '<p>尊敬的用户您好！</p>' \
        #                '<p>感谢您使用商城。</p>' \
        #                '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
        #                '<p><a href="%s">%s<a></p>' % (email, 'www.baidu.com', 'www.baidu.com')
        # send_mail(subject, '', from_email=settings.EMAIL_FROM, recipient_list=[email], html_message=html_message)
        verify_url = generate_verify_email_url(request.user)
        send_verify_email.delay(email, verify_url)
        # 激活成功
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})


class UserInfotView(LoginRequiredMixin, View):
    # 未登录跳转的地址
    login_url = '/users/login/'
    # 登录后要跳转的地址

    def get(self, request):
        # print(request)
        content = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }
        return render(request, 'user_center_info.html', context=content)

        # if request.user.is_authenticated:
        #     return render(request, 'user_center_info.html')
        # else:
        #     return redirect(reverse('users:login'))


class LogoutView(View):
    """退出登录"""

    def get(self, request):
        """
        实现退出登录逻辑
        :param request:
        :return:
        """
        logout(request)
        # 重定向
        response = redirect(reverse('content:index'))
        # 删除cookie
        response.delete_cookie('username')
        return response


class LoginView(View):
    """用户登录"""

    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # 接收参数
        # login_form = LoginForm(request.POST)
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            remembered = login_form.cleaned_data.get('remembered')

            if not all([username, password]):
                return HttpResponseForbidden('缺少必传参数')

            # 认证登录用户
            # user = User.objects.get(username=username)
            # pwd = user.password  # 密文
            # user.check_password()
            # if check_password(password, pwd):
            #     print('密码正确')
            # else:
            #     print('密码错误')
            user = authenticate(username=username, password=password)
            # print(user)
            if user is None:
                return render(request, 'login.html', {'account_errmsg': '账号或密码错误'})
            # 状态保持
            login(request, user)

            if remembered != True:
                # 没有记住登录  浏览器关闭就销毁
                request.session.set_expiry(0)
            else:
                # 记住登录  状态保持默认为2周
                request.session.set_expiry(None)
            next = request.GET.get('next')
            if next:
                response = redirect(next)
                # return redirect(next)
            else:
                response = redirect(reverse('content:index'))
            # 将用户名设置到cookie中

            # 响应结果 重定向到首页；
            # return redirect(reverse('content:index'))
            # response = redirect(reverse('content:index'))
            response.set_cookie('username', user.username, max_age=3600)
            return response
        else:
            # print(login_form.errors)
            # print(login_form.errors.get_json_data())
            context = {
                'forms_errors': login_form.errors
            }
            return render(request, 'login.html', context=context)

        # 校验参数
        # if login_form.is_valid():
        #     username = login_form.cleaned_data.get('username')
        #     password = login_form.cleaned_data.get('password')
        #     remembered = login_form.cleaned_data.get('remembered')
        #     # print(username, password)
        #     if not all([username, password]):
        #         return HttpResponseForbidden("缺少毕传参数(账号或密码)")
        #
        #     # 认证登陆用户
        #     # user = User.objects.get(username=username)
        #     # pwd = user.password  # 密文
        #     # user.check_password()
        #     # if check_password(password, pwd):
        #     #     print("密码正确")
        #     # else:
        #     #     print("密码错误")
        #     # 认证用户
        #     user = authenticate(username=username, password=password)
        #     # print(user)
        #     if user is None:
        #         return render(request, 'login.html', {"account_errmsg": "账号或密码错误"})
        #     login(request, user)
        #
        #     if remembered != True:
        #         # 设置过期时间，0表示关闭浏览器就过期,None表示默认联合国周
        #         request.session.set_expiry(0)
        #     else:
        #         # 默认保持两周
        #         request.session.set_expiry(None)
        #
        #     # 重定向
        #     return redirect(reverse("content:index"))


class RegisterView(View):
    """注册页面"""
    def get(self, request):
        """提供用户注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """用户注册逻辑
        """
        # 校验参数
        register_form = RegisterForm(request.POST)

        if register_form.is_valid():
            username = register_form.cleaned_data.get('username')
            password = register_form.cleaned_data.get('password')
            mobile = register_form.cleaned_data.get('mobile')
            # 短信验证码
            sms_code_client = register_form.cleaned_data.get('sms_code')
            redis_conn = get_redis_connection('verify_code')
            sms_code_server = redis_conn.get('sms_{}'.format(mobile))

            if sms_code_server is None:
                return render(request, 'register.html', {'sms_code_errmsg': '短信验证码已失效'})
            # 对比
            if sms_code_client != sms_code_server.decode():
                return render(request, 'register.html', {'sms_code_errmsg': '输入短信验证码错误'})

            # 保存到数据库
            try:
                user = User.objects.create_user(username=username, password=password, mobile=mobile)

            except Exception as e:
                return render(request, 'register.html', {"register_errmsg": "注册失败"})
            # return HttpResponse("注册成功")
            # 状态保持
            login(request, user)
            next = request.GET.get('next')
            if next:
                response = redirect(next)
                # return redirect(next)
            else:
                response = redirect(reverse('content:index'))
            # 将用户名设置到cookie中

            # 响应结果 重定向到首页；
            # return redirect(reverse('content:index'))
            # response = redirect(reverse('content:index'))
            response.set_cookie('username', user.username, max_age=3600)
            # return redirect(reverse('content:index'))
            return response
        else:
            print(register_form.errors.get_json_data())
            context = {
                'forms_error': register_form.errors.get_json_data()
            }
            return render(request, 'register.html', context=context)


class UsernameCountView(View):
    """用户名是否重复注册"""
    def get(self, request, username):
        """
        ajax请求
        :param request:
        :param username: 用户名
        :return: 返回判断用户名是否重复
        """
        count = User.objects.filter(username=username).count()
        content = {
            'code': RETCODE.OK,
            'errmsg': 'ok',
            'count': count,
                    }
        return JsonResponse(content)
