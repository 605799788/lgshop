from celery_tasks.main import celery_app

from .ronglianyun.ccp_sms import YunPian


@celery_app.task(name="send_sms_code")
def sends_sms_code(sms_code, mobile):
    """
    短信异步任务
    :param sms_code: 验证码
    :param mobile: 手机号
    :return:
    """
    YunPian().send_sms(sms_code, mobile)
