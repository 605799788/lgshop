from django.views import View
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, authenticate
from django_redis import get_redis_connection
from django.contrib.auth.hashers import check_password
from django.contrib.auth.backends import ModelBackend

# from users.models import User
from .forms import RegisterForm, LoginForm
from .models import User

from utils.response_code import RETCODE

# Create your views here.


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

            # 响应结果 重定向到首页
            return redirect(reverse('content:index'))
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
            return redirect(reverse('content:index'))
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
