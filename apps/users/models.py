from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class User(AbstractUser):
    """
    自定义用户模型类
    """
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号")
    # 追加邮箱字段是否激活
    email_active = models.BooleanField(verbose_name='邮箱状态', default=False)

    class Meta:
        db_table = 'tb_users'
        # 默认后台显示
        verbose_name = '用户'
        verbose_name_plural = verbose_name
