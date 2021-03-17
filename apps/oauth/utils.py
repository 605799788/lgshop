from django.conf import settings

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from urllib.parse import urlencode


from .constants import ASSESS_TOKEN_EXPIRES


def generate_access_token(openid):
    """
    加密签名
    :param openid: 明文openid
    :return:  openid密文
    """
    #                        秘钥                      过期时间s
    serializer = Serializer(settings.SECRET_KEY, ASSESS_TOKEN_EXPIRES)
    data = {"openid": openid}
    # 字节类型  加密
    token = serializer.dumps(data)

    # 解密
    # Serializer.loads(token)
    # 字节转字符串
    return token.decode()


def check_access_token(openid):
    """
    反序列化
    :param openid: 密文openid
    :return: 明文openid
    """
    serializer = Serializer(settings.SECRET_KEY, ASSESS_TOKEN_EXPIRES)
    try:
        data = serializer.loads(openid)
    except Exception as e:
        return None
    else:
        return data.get("openid")


class OAuthQQ(object):
    """
    QQ认证辅助工具类
    """

    def __init__(self, app_id=None, app_key=None, redirect_uri=None, state=None):
        self.app_id = app_id or settings.QQ_APP_ID
        self.app_key = app_key or settings.QQ_APP_KEY
        self.redirect_url = redirect_uri or settings.QQ_REDIRECT_URL
        self.state = state or '/'  # 用于保存登录成功后的跳转页面路径

    def get_auth_url(self):
        """
        获取qq登录的网址
        :return: url网址
        """
        params = {
            'response_type': 'code',
            'client_id': self.app_id,
            'redirect_uri': self.redirect_url,
            'state': self.state,
            'scope': 'get_user_info',
        }
        url = 'https://graph.qq.com/oauth2.0/authorize?' + urlencode(params)
        return url
