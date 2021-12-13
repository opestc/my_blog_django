import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_blog.settings')

#实例化
app = Celery('my_blog')

app.config_from_object('django.conf:settings', namespace='CELERY')

#自动从已注册的app中发现任务
app.autodiscover_tasks()

#一个测试任务
@app.task(bind=True)
def debug_task(self):
	print(f'Request: {self.request!r}')
