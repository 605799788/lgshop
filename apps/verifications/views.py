from django.shortcuts import render
from django.views import View
from django import http
from django_redis import get_redis_connection
import random

from verifications.libs.captcha.captcha import captcha
from verifications.libs.ronglianyun.ccp_sms import YunPian
from . import constants

from utils.response_code import RETCODE


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
        redis_conn.setex('img_%s' % uuid, text, constants.IMAGE_CODE_REDIS_EXPIRES)

        # 响应图形验证码
        return http.HttpResponse(image, content_type='image/png')


class SMSCodeView(View):

    def get(self, request, mobile):
        """
        :param request:
        :param mobile:
        :return: json
        """
        # 1. 接受校验参数
        uuid = request.GET.get('uuid')
        image_code_client = request.GET.get('image_code')
        if not all([uuid, image_code_client]):
            return http.HttpResponseForbidden("缺少必传数据")
        # 2.提取redis  删除 对比图形验证码
        redis_conn = get_redis_connection('verify_code')
        # TODO:判断是否频繁发送短信验证码
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return http.JsonResponse({"code": RETCODE.THROTTLINGERR, 'errmsg': "发送短信过于频繁"})

        image_code_server = redis_conn.get('img_%s' % uuid)
        if image_code_server is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': "图形验证码已失效"})
        # 删除
        redis_conn.delete('img_%s' % uuid)
        # 对比
        iamge_code_server = image_code_server.decode()
        if image_code_client.lower() != iamge_code_server.lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '输入图形验证码有误'})
        # 3.生成短信验证码 6位 保存
        sms_code = "%06d" % random.randint(0, 999999)
        # print(sms_code)
        # TODO：保存发送短信验证码
        redis_conn.setex('send_flag_{}'.format(mobile), 1, constants.SEND_SMS_CODE_TIMES)
        # 保存
        redis_conn.setex("sms_{}".format(mobile), sms_code, constants.SMS_CODE_REDIS_EXPIRES)
        # 4. 发送短信 判断响应结果
        YunPian().send_sms(str(sms_code), mobile)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '发送短信成功'})