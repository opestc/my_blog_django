from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
import json
import base64
from django.http.request import QueryDict
import paramiko
import socket
from threading import Thread
import time
import os
from django.utils.six import StringIO
from django.conf import settings

zmodemszstart = b'rz\r**\x18B00000000000000\r\x8a'
zmodemszend = b'**\x18B0800000000022d\r\x8a'
zmodemrzstart = b'rz waiting to receive.**\x18B0100000023be50\r\x8a'
zmodemrzend = b'**\x18B0800000000022d\r\x8a'
zmodemcancel = b'\x18\x18\x18\x18\x18\x08\x08\x08\x08\x08'
	
def get_key_obj(pkeyobj, pkey_file=None, pkey_obj=None, password=None):
	if pkey_file:
		with open(pkey_file) as fo:
			try:
				pkey = pkeyobj.from_private_key(fo, password=password)
				return pkey
			except:
				pass
	else:
		try:
			pkey = pkeyobj.from_private_key(pkey_obj, password=password)
			return pkey
		except:
			pkey_obj.seek(0)
			
			
class SSHBridge(object):
	"""
	桥接WebSocket和ssh
	参考：https://blog.51cto.com/hongchen99/2336087
	"""
	
	def __init__(self, websocket, simpleuser):
		self.websocket = websocket
		self.simpleuser = simpleuser
		self.cmd = ''
		self.zmodem = False
		self.zmodemOO = False
	def connect(self, host, user, pwd=None, key=None, port=22, timeout=6, term='xterm', pty_width=80, pty_height=24):
		"""
		建立SSH连接，放在 self.ssh_channel 通道中，之后直接在通道中交互数据
		:param host:
		:param user:
		:param pwd:
		:param key:
		:param port:
		:param timeout:
		:param term:
		:param pty_width:
		:param pty_height:
		:return:
		"""
		ssh_client = paramiko.SSHClient()
		ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		try:
			if key:
				# 密钥方式认证
				pkey = get_key_obj(paramiko.RSAKey, pkey_obj=key, password=pwd) or \
						get_key_obj(paramiko.DSSKey, pkey_obj=key, password=pwd) or \
						get_key_obj(paramiko.ECDSAKey, pkey_obj=key, password=pwd) or \
						get_key_obj(paramiko.Ed25519Key, pkey_obj=key, password=pwd)
				ssh_client.connect(username=user, hostname=host, port=port, pkey=pkey, timeout=timeout)
			else:
				ssh_client.connect(hostname=host, port=port, username=user, password=pwd, timeout=timeout)
		except Exception as e:
#			# pri00nt(e)
			message = json.dumps({'flag': 'fail', 'message': str(e)})
			self.websocket.send_message_or_team(message)
			return
		
		transport = ssh_client.get_transport()
		
		"""
		另一种方式建立通道
		transport = paramiko.Transport((host, port,))
		transport.start_client()
		transport.auth_password(username=user, password=pwd)
		"""
		
		# 打开一个通道
		self.ssh_channel = transport.open_session()
		# 获取一个终端
		self.ssh_channel.get_pty(term=term, width=pty_width, height=pty_height)
		# 激活终端，这样就可以登录到终端了，就和我们用类似于xshell登录系统一样
		self.ssh_channel.invoke_shell()
		
		# 获取ssh连接主机后的返回内容，例如Linux，会显示上次登录等信息，把这些信息通过WebSocket显示到Web终端。
		# 连接建立一次，之后交互数据不会再进入该方法
		for i in range(2):
			recv = self.ssh_channel.recv(1024).decode('utf-8')
			message = json.dumps({'flag': 'msg', 'message': recv})
			# pri00nt('【WS  --websocket-->  Web】建立SSH通道后，返回欢迎信息：', message)
			self.websocket.send_message_or_team(message)
		Thread(target=self._ssh_to_ws).start()
		
	def close(self):
		message = {'flag': 0, 'message': '关闭WebSocket和SSH连接'}
		# 向WebSocket发送一个关闭消息
		self.websocket.send_message_or_team(json.dumps(message))
		
		try:
			# 关闭ssh通道
			self.ssh_channel.close()
			# 关闭WebSocket连接
			self.websocket.close()
		except BaseException as e:
			# pri00nt('关闭WebSocket和SSH连接产生异常：', e)
			pass
			
	def _ws_to_ssh(self, data):
		"""
		尝试发送数据到ssh通道，产生异常则关闭所有连接
		"""
		try:
			# pri00nt('【Func  --paramiko-->  SSH】WebSocket中的数据发送数据到ssh通道：', data)
			self.ssh_channel.send(data)
			if data == '\r':
				data == '\n'
			self.cmd += data
		except OSError as e:
			# print('ws to ssh error' + e)
			self.close()
	
	def _ws_bytes_to_ssh(self, data):
		try:
			self.ssh_channel.send(data)
		except Exception:
			self.close()
			
	def _ssh_to_ws(self):
		try:
			while True:
				if self.zmodemOO:
					# 文件开始下载
					self.zmodemOO = False
					data = self.ssh_channel.recv(2)
					if not len(data):
						return
					# 文件下载结束
					if data == b'OO':
						self.websocket.send(bytes_data=data)
						continue
					else:
						data += self.ssh_channel.recv(1024)
				else:
					data = self.ssh_channel.recv(1024)
					if not len(data):
						return
				
				if self.zmodem:
					if zmodemszend in data or zmodemrzend in data:
						self.zmodem = False
						if zmodemszend in data:
							self.zmodemOO = True
					if zmodemcancel in data:
						self.zmodem = False
					self.websocket.send(bytes_data=data)
				else:
					if zmodemszstart in data or zmodemrzstart in data:
						self.zmodem = True
						self.websocker.send(bytes_data=data)
					else:
						data = data.decode('unicode_escape')
						# pri00nt('【SSH  --paramiko-->  Func】获取ssh通道返回的数据：', data)
						message = {'flag': 'msg', 'message': data}
						# pri00nt('【WS --websocket-->  Web】通过WebSocket把信息发回前端，显示到Web终端：', message)
						self.websocket.send_message_or_team(json.dumps(message))

#			while not self.ssh_channel.exit_status_ready():
#				# data = self.ssh_channel.recv(1024).decode('utf-8')
#				data = self.ssh_channel.recv(1024).decode('unicode_escape')
#				# pri00nt('【SSH  --paramiko-->  Func】获取ssh通道返回的数据：', data)
#				if len(data) != 0:
#					message = {'flag': 'msg', 'message': data}
#					# pri00nt('【WS --websocket-->  Web】通过WebSocket把信息发回前端，显示到Web终端：', message)
#					self.websocket.send_message_or_team(json.dumps(message))
#				else:
#					break
				
		except:
			print('ssh to ws error')
			self.close()
			
	def shell(self, data):
		# Thread(target=self._ws_to_ssh, args=(data,)).start()
		self._ws_to_ssh(data)
		# Thread(target=self._ssh_to_ws).start()
		"""
		t1 = Thread(target=self._ws_to_ssh, args=(data,))
		t1.setDaemon(True)
		t1.start()
		t2 = Thread(target=self._ssh_to_ws)
		t2.setDaemon(True)
		t2.start()
		"""
		
	def resize_pty(self, cols, rows):
		self.ssh_channel.resize_pty(width=cols, height=rows)
		
		
class WebsshConsumer(WebsocketConsumer):
	"""
	1、xterm.js 在浏览器端模拟 shell 终端, 监听用户输入通过 websocket 将用户输入的内容上传到 django
    2、django 接受到用户上传的内容, 将用户在前端页面输入的内容通过 paramiko 建立的 ssh 通道上传到远程服务器执行
    3、paramiko 将远程服务器的处理结果返回给 django
    4、django 将 paramiko 返回的结果通过 websocket 返回给用户
    5、xterm.js 接收 django 返回的数据并将其写入前端页面
	"""
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.host_id = ''
		self.simple_user = ''
		self.is_team = False
		self.team_name = ''
		
	def connect(self):
		"""
		建立WebSocket连接，并实例化SSHBridge类，在这个对象中建立SSH连接，放在 self.ssh_channel 通道中
		:return:
		"""
		self.host_id = self.scope['url_route']['kwargs'].get('host_id')
		try:
			self.simple_user = self.scope["session"]["user_name"]  # 获取session中的值
		except:
			self.simple_user = 'anonymous user'
		# pri00nt('【Web  --websocket-->  WS】建立WebSocket通道，当前连接用户：', self.simple_user)
		print('host_id', self.host_id)
		self.accept()
		
		# WebSocket连接成功后，连接ssh
		query_string = self.scope.get('query_string')
		ws_args = QueryDict(query_string=query_string, encoding='utf-8')

		# # pri00nt(ws_args)
		# <QueryDict: {'user': ['admin'], 'host': ['192.168.96.20'], 'port': ['22'], 'auth': ['pwd'], 'pwd': ['ZGphbmdvYWRtaW4='], 'key': [''], 'width': ['113'], 'height': ['43']}>
		# 根据参数判断是否是协作
		team = ws_args.get('team')
		if team:
			self.is_team = True
			self.team_name = "team_{}".format(self.host_id)  # 加到这个通道组
			async_to_sync(self.channel_layer.group_add)(
				self.team_name,
				self.channel_name
			)
			# 用户连接时，同一群组发送消息
			self.send_message_or_team(json.dumps({'flag': 'user', 'message': '用户 {} 已连接本终端'.format(self.simple_user)}))
			
		width = ws_args.get('width')
		height = ws_args.get('height')
		width = int(width)
		height = int(height)  # ssh连接要求int类型：required argument is an integer
		
		ssh_connect_dict = {}
		
		if self.host_id:
			# 指定连接
			# pri00nt('连接的服务器id：', self.host_id)
			if int(self.host_id) == 1:
				ssh_connect_dict = {
					'host': '192.168.96.20',
					'user': 'user',
					'port': 22,
					'timeout': 30,
					'pty_width': width,
					'pty_height': height,
					'pwd': 'user'
				}
			elif int(self.host_id) == 2:
				ssh_connect_dict = {
					'host': '192.168.96.21',
					'user': 'user',
					'port': 22,
					'timeout': 30,
					'pty_width': width,
					'pty_height': height,
					'pwd': 'user'
				}
			else:
				self.close()
				return
			
		else:
			user = ws_args.get('user')
			host = ws_args.get('host')
			port = ws_args.get('port')
			port = int(port)
			auth = ws_args.get('auth')
			pwd = ws_args.get('pwd')
			if pwd:
				pwd = base64.b64decode(pwd).decode('utf-8')
			sshkey_filename = ws_args.get('sshkey_filename')
			
			ssh_connect_dict = {
				'host': host,
				'user': user,
				'port': port,
				'timeout': 30,
				'pty_width': width,
				'pty_height': height,
				'pwd': pwd
			}
			
			if auth == 'key':
				sshkey_file = os.path.join(settings.MEDIA_ROOT, 'sshkey', sshkey_filename)
				if not os.path.exists(sshkey_file):
					self.send(json.dumps({'flag': 'error', 'message': '密钥文件不存在'}))
					
				else:
					try:
						f = open(sshkey_file, 'r', encoding='utf-8')
						key = f.read()
						string_io = StringIO()
						string_io.write(key)
						string_io.flush()
						string_io.seek(0)
						ssh_connect_dict['key'] = string_io
						
						os.remove(sshkey_file)  # 用完之后删除key文件
					except BaseException as e:
						# pri00nt('打开密钥文件出错', e)
						pass
						
		# 建立SSH连接
		self.ssh = SSHBridge(websocket=self, simpleuser=self.simple_user)
		# pri00nt('【WS  --SSHBridge-->  SSH】连接SSH参数：', ssh_connect_dict)
		self.ssh.connect(**ssh_connect_dict)
		
	def disconnect(self, close_code):
		# 断开连接
		# pri00nt('用户 {} 断开WebSocket连接，断开SSH连接'.format(self.simple_user))
		try:
			if self.is_team:
				# 用户连接时，同一群组发送消息
				self.send_message_or_team(json.dumps({'flag': 'user', 'message': '用户 {} 已断开本终端'.format(self.simple_user)}))
				# 退出群组
				async_to_sync(self.channel_layer.group_discard)(
					self.team_name,
					self.channel_name
				)
			self.ssh.close()
		except BaseException as e:
			pass
			
	def receive(self, text_data=None, bytes_data=None):
		# 从WebSocket中接收消息
		text_data = json.loads(text_data)  # json字符串转字典
		# pri00nt('\n\n【Web  --websocket-->  WS】Web终端按键内容通过WebSocket传到后端：', text_data)
		if type(text_data) == dict:
			if text_data.get('flag') == 'entered_key':
				data = text_data.get('entered_key', '')  # 获取前端传过来输入的按键值，并传递给shell
				# pri00nt('【WS  --SSHBridge-->  Func】WebSocket转发SSHBridge：', text_data)
				self.ssh.shell(data=data)
			else:
				cols = text_data['cols']
				rows = text_data['rows']
				# 改变通道中终端大小
				self.ssh.resize_pty(cols=cols, rows=rows)
		else:
			# pri00nt('【！！！】收到的数据不是dict类型')
			if text_data is None:
				self.ssh._ws_bytes_to_ssh(bytes_data)
			else:
				pass
			
	def send_message_or_team(self, message):
		if self.is_team:
			async_to_sync(self.channel_layer.group_send)(
				self.team_name,
				{
					'type': 'team_message',
					'message': message
				}
			)
		else:
			self.send(message)
			
	def team_message(self, event):
		message = event['message']
		
		# 发送消息到WebSocket
		self.send(message)
		
		