import time
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
import redis



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
			self.send(text_data=json.dumps({
				'message': time.strftime("%H:%M:%S ") + message
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
	
	def push_message(self, event):
		# print(event, type(event))
		if 'user_conn' in event:
			self.send(text_data=json.dumps(
				{"user_conn":event["user_conn"], "users":"<i class='fas fa-user-circle'></i> "+("<br><i class='fas fa-user-circle'></i> ").join(event['users'])}
			))
		elif 'message' in event:
			msg = time.strftime("%H:%M:%S ") + event["message"]
			self.send(text_data=json.dumps(
			{"message":msg} 
		))
		
def send_group_msg(room_name, message):
	# 从Channels的外部发送消息给Channel
	"""
	from assets import consumers
	consumers.send_group_msg('ITNest', {'content': '这台机器硬盘故障了', 'level': 1})
	consumers.send_group_msg('ITNest', {'content': '正在安装系统', 'level': 2})
	:param room_name:
	:param message:
	:return:
	"""
	channel_layer = get_channel_layer()
	async_to_sync(channel_layer.group_send)(
		'notice_{}'.format(room_name),  # 构造Channels组名称
		{
			"type": "system_message",
			"message": message,
		}
	)