from django.shortcuts import redirect, render
from django.contrib.auth import login
from django.views import View
from django.conf import settings
from django import http

from QQLoginTool.QQtool import OAuthQQ
from django_redis import get_redis_connection

from utils.response_code import RETCODE
from .utils import generate_access_token, check_access_token
from users.models import User
from .models import OAuthQQUser
import logging

# 日志记录输出器
logger = logging.getLogger('django')


class QQAuthUserView(View):
    """处理qq登录回调"""
    def get(self, request):
        """
        处理QQAuthURLView回调业务逻辑
        :param request:
        :return:
        """
        code = request.GET.get("code")
        print('========================================================')
        print(code)
        if not code:
            return http.HttpResponseForbidden("获取code失败")
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            print(oauth, code, settings.QQ_CLIENT_ID, settings.QQ_CLIENT_SECRET, settings.QQ_REDIRECT_URI)
            # 获取access_token
            access_token = oauth.get_access_token(code)
            print(access_token)
            # 获取openid
            openid = oauth.get_open_id(access_token)
            print(openid)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('Oauth2.0认证失败')
        # 获取openid后判断是否绑定user
        try:
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 没有记录说明openid未绑定商城用户 要显示绑定页面
            # openid不可以明文显示，需要一个可逆的算法
            context = {"access_token_openid": generate_access_token(openid)}
            return render(request, 'oauth_callback.html', context)
            pass
        else:
            # 找到记录说明已绑定  登陆
            # 状态保持
            login(request, oauth_user.user)
            next = request.GET.get('state')
            response = redirect(next)
            response.set_cookie('username', oauth_user.user.username, max_age=3600)
            return response

    def post(self, request):
        """
        绑定用户
        :param request:
        :return:
        """
        # 接收页面参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code_client = request.POST.get("sms_code")
        access_token = request.POST.get("access_token_openid")
        # 校验参数   判断短信验证码是否一致
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get("sms_%s" % mobile)

        if sms_code_server is None:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '无效的短信验证码'})
        if sms_code_client != sms_code_server.decode():
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '输入短信验证码有误'})
        # 判断openid是否有效
        openid = check_access_token(access_token)
        if not openid:
            return render(request, 'oauth_callback.html', {'openid_errmsg': 'openid已经失效'})
        # 使用手机号查询用户是否已存在
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 不存在则创建新用户
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)
        else:
            # 存在手机号则校验密码
            if not user.check_password(password):
                return render(request, 'oauth_callback.html', {'account_errmsg': '账号或者密码错误'})
        # 绑定用户
        try:
            oauth_qq_user = OAuthQQUser.objects.create(user=user, openid=openid)
        except Exception as e:
            logger.error(e)
            return render(request, 'oauth_callback.html', {'account_errmsg': '账号或者密码错误'})

        # 重定向保持状态
        login(request, oauth_qq_user.user)
        next = request.GET.get("state")
        response = redirect(next)
        response.set_cookie('username', oauth_qq_user.user.username, max_age=3600 * 24)
        return response


class QQAuthURLView(View):
    """点击qq图标跳转登陆页面"""
    def get(self, request):
        """
        提供qq登陆扫码页面
        :param request:
        :return:
        """
        next = request.GET.get('next')
        # print(next)

        # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)

        # 生成扫描链接地址
        login_url = oauth.get_qq_url()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})



