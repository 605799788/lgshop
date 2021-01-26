from django.views import View
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login

# from users.models import User
from .forms import RegisterForm
from .models import User
# Create your views here.


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
            'code': 200,
            'errmsg': 'ok',
            'count': count,
                    }
        return JsonResponse(content)
