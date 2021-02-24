from django.contrib.auth.backends import ModelBackend
from django.conf import settings

import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from .models import User
from .constants import VERIFY_EMAIL_TOKEN_EXPIRES


def get_user_by_account(account):
    """
    获取user对象
    :param account:  用户名或者手机号
    :return: user
    """
    try:
        if re.match(r'^1[3-9]\d{9}', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except:
        return None
    else:
        return user


class UsernameMobileBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写认证方法
        :param username: 用户名或者手机号
        :param password: 密码明文
        :param kwargs: 额外参数
        :return: user
        """
        # 使用账号查询用户
        # 如果查询到用户,需要校验密码
        # 密码校验成功 返回user

        user = get_user_by_account(username)

        if user and user.check_password(password):
            return user
        else:
            return None


def generate_verify_email_url(user):
    """
    生成邮箱激活链接
    生成token
    :return:
    """
    s = Serializer(settings.SECRET_KEY, VERIFY_EMAIL_TOKEN_EXPIRES)
    data = {'user_id': user.id, 'email': user.email}
    token = s.dumps(data)

    return settings.EMAIL_VERIFY_URL + "?token=" + token.decode()


def check_verify_email_token(token):
    """
    反序列化获取token
    :param token: generate_verify_email_url序列化后的token
    :return:
    """
    s = Serializer(settings.SECRET_KEY, VERIFY_EMAIL_TOKEN_EXPIRES)
    try:
        data = s.loads(token)
    except:
        return None
    else:
        user_id = data.get('user_id')
        email = data.get('email')
        try:
            user = User.objects.get(id=user_id, email=email)
        except User.DoesNotExist:
            return None
        else:
            return user
