from django.conf import settings

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

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