import time
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
import redis



class ChatConsumer(WebsocketConsumer):
	chats = dict()
	def connect(self):
		self.room_name = self.scope['url_route']['kwargs']['room_name']
		self.room_group_name = 'chat_%s' % self.room_name
		self.user = self.scope["user"]

		# Join room group
		async_to_sync(self.channel_layer.group_add)(
			self.room_group_name,
			self.channel_name
		)
		try:
			ChatConsumer.chats[self.room_name].add(self)
		except:
			ChatConsumer.chats[self.room_name] = set([self])
					
		self.accept()
		
	def disconnect(self, close_code):
		# Leave room group
		async_to_sync(self.channel_layer.group_discard)(
			self.room_group_name,
			self.channel_name
		)
		ChatConsumer.chats[self.room_name].remove(self)

	# Receive message from WebSocket
	def receive(self, text_data):
		text_data_json = json.loads(text_data)
		message = text_data_json['message']
		username = text_data_json['username']
		print("receive_message: ", message)
		print("Sender: ", username)

		# Send message to room group
		async_to_sync(self.channel_layer.group_send)(
			self.room_group_name,
			{
				'type': 'chat_message',
				'message': message,
				'username': username
			}
		)
		
	# Receive message from room group
	def chat_message(self, event):
		message = event['message']
		username = event['username']
		# Send message to WebSocket
		self.send(text_data=json.dumps({
			'message': time.strftime("%H:%M:%S ") + username + ": " + message
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
		if 'number' in event.keys():
			self.send(text_data=json.dumps(
				{"number":event["number"]}
			))
		elif 'message' in event.keys():
			msg = time.strftime("%H:%M:%S ") + event["message"]
			self.send(text_data=json.dumps(
			{"message":msg} 
		))
		