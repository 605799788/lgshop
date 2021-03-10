from django.shortcuts import render
from django.views import View
from django.conf import settings
from django.http import JsonResponse

from QQLoginTool.QQtool import OAuthQQ

from utils.response_code import RETCODE

# Create your views here.


class QQAuthURLView(View):

    def get(self, request):
        """
        提供qq登陆扫码页面
        :param request:
        :return:
        """
        next = request.GET.get('next')
        print(next)
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)
        login_url = oauth.get_qq_url()
        return JsonResponse({"code": RETCODE.OK, "errmsg": 'ok',
                             "login_url": login_url})