from django.contrib.auth.mixins import LoginRequiredMixin
from django import http

from utils.response_code import RETCODE


class LoginRequiredJSONMixin(LoginRequiredMixin):
    """自定义判断用户是否登陆的扩展类，返回json"""
    def handle_no_permission(self):
        """直接响应json数据"""
        return http.JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '用户未登录'})