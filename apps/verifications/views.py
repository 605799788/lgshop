from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django_redis import get_redis_connection

from verifications.libs.captcha.captcha import captcha


# Create your views here.


class ImageVIew(View):
    """图形验证码"""
    def get(self, request, uuid):
        """
        :param request:
        :param uuid: 通用唯一识别符
        :return: 验证码图片
        """
        # 生成验证码 和 图形验证码
        text, image = captcha.generate_captcha()
        # print(text, image)
        # 保存验证码 redis
        redis_conn = get_redis_connection('verify_code')
        # setex(self, name, time, value):
        redis_conn.setex('img_%s' % uuid, text, 300)

        # 响应图形验证码
        return HttpResponse(image, content_type='image/png')

