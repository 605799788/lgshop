# celery入口文件
from celery import Celery

# 创建实例  生产者
celery_app = Celery('lg')

# 加载配置文件
celery_app.config_from_object('celery_tasks.config')

# 注册任务
celery_app.autodiscover_tasks(['celery_tasks.sms'])
# windows启动添加最后一个参数 --pool=solo
# celery -A celery_tasks.main worker -l info --pool=solo
# celery -A celery_tasks.main worker -l info -P eventlet
