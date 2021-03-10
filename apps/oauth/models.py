from django.db import models

from utils.models import BaseModel

# Create your models here.


class OAuthQQUser(BaseModel):
    """QQ登陆模型"""
    user = models.ForeignKey('users.User', on_delete=models.CASCADE,
                             verbose_name='qq用户')
    openid = models.CharField(max_length=64, verbose_name='QQopenid')

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = "QQ登陆"
        verbose_name_plural = verbose_name