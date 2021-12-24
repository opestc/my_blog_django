from django.urls import path
from .views import index, upload_ssh_key
# from simpleauth.tools.simpleauth_tool import simple_permission_required

app_name = 'webssh'

urlpatterns = [
	path('', index, name='index'),  # 终端主页
	path('upload_ssh_key/', upload_ssh_key, name='upload_ssh_key'),  # 终端主页
]

