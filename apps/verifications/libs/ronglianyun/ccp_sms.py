import json
import requests


# 单例设计模式
class CCP(object):

    def __new__(cls, *args, **kwargs):
        # 第一次实力化，应该返回实例化后的对象
        # 接下来的实例化都返回第一次的实例化对象
        if not hasattr(cls, '_instance'):
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)
        # else:
        #     return cls._instance
        return cls._instance


class YunPian(CCP):

    def __init__(self):
        self.api_key = "6a53edf950559932d1c904bff9bb09e6"
        self.single_send_url = "https://sms.yunpian.com/v2/sms/single_send.json"

    def send_sms(self, code, mobile):
        parmas = {
            "apikey": self.api_key,
            "mobile": mobile,
            "text": "【李准先生】您的验证码是%s。如非本人操作，请忽略本短信" % code
                }

        response = requests.post(self.single_send_url, data=parmas)
        re_dict = json.loads(response.text)
        print(re_dict)
        if re_dict['code'] == 0:
            return 0
        else:
            return -1

        # print(re_dict)
        # return re_dict


if __name__ == "__main__":
    # APIKEY = "6a53edf950559932d1c904bff9bb09e6"
    # yun_pian = YunPian()
    # yun_pian.send_sms("520", '17710709974')
    # a = YunPian()
    # b = YunPian()
    # c = CCP()
    # print(id(a))
    # print(id(b))
    # print(id(c))
    YunPian().send_sms('1234', '17710709974')

