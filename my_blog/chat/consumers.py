import time
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
import redis
from . import tasks
from channels.layers import get_channel_layer
import paramiko
import threading
import getpass
# channel_layer = get_channel_layer()
COMMANDS = {
	'help': {
		'help':'命令帮助信息.',
	},
	'search': {
		'args': 2,
		'help': '通过名字查找诗人诗文, e.g. search 李白.\n可另加数字参数查看更多内容, e.g. search 李白 2 (数字为页码).\n清空内容请输入 search clear.\n',
		'task': 'search'
	},
}

class MyThread(threading.Thread):
	def __init__(self, chan):
		threading.Thread.__init__(self)
		self.chan = chan
		
	def run(self):
		# while not self.chan.chan.exit_status_ready():
		while True:
			# time.sleep(0.1)
			try:
				data = self.chan.chan.recv(1024)
				async_to_sync(self.chan.channel_layer.group_send)(
					self.chan.room_group_name,
					{
						"type": "push.message",
						"message": data.decode('unicode_escape')
					},
				)
			except Exception as ex:
				print(str(ex))
		self.chan.sshclient.close()
		return False

class ChatConsumer(WebsocketConsumer):
	chats = dict()
	user_conn = 0
	def connect(self):
		self.room_name = self.scope['url_route']['kwargs']['room_name']
		self.room_group_name = 'chat_%s' % self.room_name
		self.user_name = self.scope["session"]["user_name"] # username in session
		# Join room group
		async_to_sync(self.channel_layer.group_add)(
			self.room_group_name,
			self.channel_name
		)
		if self.room_name not in ChatConsumer.chats:
			ChatConsumer.chats[self.room_name]={}

		try:
			ChatConsumer.chats[self.room_name][self.user_name].add(self)
		except:
			ChatConsumer.chats[self.room_name][self.user_name] = set([self])
		ChatConsumer.user_conn += 1	
#		print(ChatConsumer.chats)
		self.accept()
		async_to_sync(self.channel_layer.group_send)(
			self.room_group_name,
			{
				'type': 'chat_message',
				'message': '@%s joined the group' % (self.user_name),
				'user_conn': ChatConsumer.user_conn,
				'users': list(ChatConsumer.chats[self.room_name]),
			}
		)
		
	def disconnect(self, close_code):
		# Leave room group
		async_to_sync(self.channel_layer.group_discard)(
			self.room_group_name,
			self.channel_name
		)
		ChatConsumer.chats[self.room_name][self.user_name].remove(self)
		
		if not ChatConsumer.chats[self.room_name][self.user_name]:
			del ChatConsumer.chats[self.room_name][self.user_name]
		if not ChatConsumer.chats[self.room_name]:
			del ChatConsumer.chats[self.room_name]
		ChatConsumer.user_conn -= 1		
		async_to_sync(self.channel_layer.group_send)(
			self.room_group_name,
			{
				'type': 'chat_message',
				'message': '@%s left the group' % (self.user_name),
				'user_conn': ChatConsumer.user_conn,
				'users': list(ChatConsumer.chats[self.room_name]),
			}
		)


	# Receive message from WebSocket
	def receive(self, text_data):
		text_data_json = json.loads(text_data)
		message = text_data_json['message']
		print("receive_message: ", message)
		print("Sender: ", self.user_name)

		# Send message to room group
		async_to_sync(self.channel_layer.group_send)(
			self.room_group_name,
			{
				'type': 'chat_message',
				'message': self.user_name+': ' + message,
			}
		)
		if self.room_name == 'bot':
			response_message = "Pls input 'help' for commands."
			message_parts = message.split()
			if message_parts:
				command = message_parts[0].lower()
				if command == 'help':
					response_message = '支持的命令有:\n' + '\n'.join([f'{command} - {params["help"]} ' for command, params in COMMANDS.items()])

				elif command in COMMANDS:
					if len(message_parts[1:]) > COMMANDS[command]['args'] or len(message_parts)==1:
						response_message = f'命令`{command}`参数错误，请重新输入.'
					else:
						getattr(tasks, COMMANDS[command]['task']).delay(self.channel_name, *message_parts[1:])
						response_message = f'收到`{message}`任务.'
			async_to_sync(self.channel_layer.group_send)(
				self.room_group_name,
				{
					'type': 'chat_message',
					'message': self.room_name+': ' + response_message,
				}
			)
		
	# Receive message from room group
	def chat_message(self, event):
		message = event['message']
		# Send message to WebSocket
		if 'user_conn' in event:
			self.send(text_data=json.dumps({
				'message': time.strftime("%H:%M:%S ") + message,
				'user_conn': event['user_conn'],
				'users':event['users']
			}))
		else:
			try:
				self.send(text_data=json.dumps({
					'message': time.strftime("%H:%M:%S ") + message
				}))
			# if message is a dict
			except:
				self.send(text_data=json.dumps({
					'message': message
				}))
'''
pool = redis.ConnectionPool(
	host="127.0.0.1",
	port=6379,
	max_connections=10,
	decode_response=True,
)
conn = redis.Redis(connection_pool=pool, decode_responses=True)

class ChatConsumer(AsyncWebsocketConsumer):
	chats = dict()
	async def connect(self):
		self.room_name = self.scope['url_route']['kwargs']['room_name']
		self.room_group_name = 'chat_%s' % self.room_name
		self.user = self.scope["user"]
		print('user: ')
		print(self.user.username)
		# Join room group
		await self.channel_layer.group_add(
			self.room_group_name,
			self.channel_name
		)
		try:
			ChatConsumer.chats[self.room_name].add(self)
		except:
			ChatConsumer.chats[self.room_name] = set([self])
			
		await self.accept()

		
	async def disconnect(self, close_code):
		# Leave room group
		print("close_code: ", close_code)
		await self.channel_layer.group_discard(
			self.room_group_name,
			self.channel_name
		)
		ChatConsumer.chats[self.room_name].remove(self)
			
		await self.close()

		
	# Receive message from WebSocket
	async def receive(self, text_data):
		text_data_json = json.loads(text_data)
		message = text_data_json['message']
		username = text_data_json['username']
		print("receive_message: ", message)
		print("Sender: ", username)
		# Send message to room group
		await self.channel_layer.group_send(
			self.room_group_name,
			{
				'type': 'chat_message',
				'message': message,
				'username': username
			}
		)
		
	# Receive message from room group
	async def chat_message(self, event):
		message = event['message']
		username = event['username']
		# Send message to WebSocket
		await self.send(text_data=json.dumps({
			'message': time.strftime("%H:%M:%S ") + username + ": " + message
		}))
'''
class PushMessage(WebsocketConsumer):
	
	def connect(self):
		self.room_group_name = self.scope['url_route']['kwargs']['room_name']
		
		async_to_sync(self.channel_layer.group_add)(
			self.room_group_name,
			self.channel_name
		)
		self.accept()
		
	def disconnect(self, code):
		# Leave room group
		async_to_sync(self.channel_layer.group_discard)(
			self.room_group_name,
			self.channel_name
		)
	
	def receive(self, text_data):
		if text_data == '1':
			self.sshclient = paramiko.SSHClient()
			self.sshclient.load_system_host_keys()
			self.sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			host = input('Host: ')
			user = input('User: ')
			pd = getpass.getpass('Password: ')
			self.sshclient.connect(host, 22, user, pd, timeout=10)
			self.chan = self.sshclient.invoke_shell(term='xterm')
			# self.chan.settimeout(30)
			t1 = MyThread(self)
			t1.setDaemon(True)
			t1.start()
		else:
			try:
				self.chan.send(text_data)
			except Exception as ex:
				print(str(ex))


	def push_message(self, event):
		# print(event, type(event))
#		if 'user_conn' in event:
#			self.send(text_data=json.dumps(
#				{"user_conn":event["user_conn"], "users":"<i class='fas fa-user-circle'></i> "+("<br><i class='fas fa-user-circle'></i> ").join(event['users'])}
#			))
#		elif 'message' in event:
#			msg = time.strftime("%H:%M:%S ") + event["message"]
#			self.send(text_data=json.dumps(
#			{"message":msg} 
#		))
		self.send(text_data=event['message'])
		
def send_group_msg(room_name, message):
	# 从Channels的外部发送消息给Channel
	"""
	from chat import consumers
	consumers.send_group_msg('ITNest', {'content': '这台机器硬盘故障了', 'level': 1})
	consumers.send_group_msg('ITNest', {'content': '正在安装系统', 'level': 2})
	:param room_name:
	:param message:
	:return:
	"""

	async_to_sync(channel_layer.group_send)(
		'chat_{}'.format(room_name),  # 构造Channels组名称
		{
			"type": "chat_message",
			"message": message,
		}
	)