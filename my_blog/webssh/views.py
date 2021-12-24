import time
import random
import hashlib
import os
from django.conf import settings
from django.shortcuts import render, HttpResponse
from article.models import ArticleColumn
# Create your views here.

columns = ArticleColumn.objects.all()

def index(request):
	# print(request.session['user_name'])
	return render(request, 'webssh/index.html', {'columns':columns})


def unique():
	ctime = str(time.time())
	salt = str(random.random())
	m = hashlib.md5(bytes(salt, encoding='utf-8'))
	m.update(bytes(ctime, encoding='utf-8'))
	return m.hexdigest()


def upload_ssh_key(request):
	if request.method == 'POST':
		key_file = request.FILES.get('key_file')
		if not key_file:
			return HttpResponse('')
		print(type(key_file.read()))
		ssh_key = key_file.read().decode('utf-8')  # 获取上传文件的内容
		
		sshkey_filename = unique()
		print('文件保存为唯一名称：', sshkey_filename)
		
		ssh_key_path = os.path.join(settings.MEDIA_ROOT, 'sshkey')
		
		if not os.path.exists(ssh_key_path):
			os.mkdir(ssh_key_path)  # 创建保存key文件的文件夹
			
		with open(os.path.join(ssh_key_path, sshkey_filename), 'w', encoding='utf-8') as f:
			f.write(ssh_key)
			
		return HttpResponse(sshkey_filename)