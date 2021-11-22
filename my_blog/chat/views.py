from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import ChatEntryForm
from channels.layers import get_channel_layer
from article.models import ArticleColumn
from asgiref.sync import async_to_sync
from django.views.decorators.http import require_POST,require_GET
from . import consumers
columns = ArticleColumn.objects.all()
users = {}
def index(request):
	if request.method == "POST":
		chat_entry_form = ChatEntryForm(data=request.POST)
		if chat_entry_form.is_valid():
			room_name = request.POST['room_name']
			request.session['user_name'] = request.POST['user_name']
			return redirect('chat:room',room_name=room_name)
	return render(request, 'chat/index.html', {'columns':columns})

def room(request, room_name):
	user_name = request.session['user_name']
	data = request.GET.copy()
	data['room'] = room_name
	data['user'] = request.session['user_name']
	return render(request, 'chat/room.html', {
		'room_name': room_name, 'user_name':user_name, 'columns':columns
	})
	
def pushRedis(request):
	room = request.GET.get("room")
	user = request.GET.get("user")
	
	if room not in users.keys():
		users[room]={}
	if user not in users[room]:	
		users[room][user] = 0
	user_number = 0
	for key,value in users.items():
		if key == room:
			for num in value.values():
				user_number += num
	print(room)
	print(consumers.ChatConsumer.chats[room])
	user_conn = len(consumers.ChatConsumer.chats[room])
	

	print('room: ' + room + ' user: ' + user + ' connections: ' + str(user_conn))
	if request.GET.get("enter") and user_number < user_conn:
		users[room][user] += 1
	if request.GET.get("leave"):
		users[room][user] -= 1
		if users[room][user] <= 0:
			del users[room][user]

	def push():
		channel_layer = get_channel_layer()
		if request.GET.get("number"):
			async_to_sync(channel_layer.group_send) (
				room,
				{"type": "push.message", "number": user_conn, "room_name": room}
			)
		elif request.GET.get("enter"):
			msg = user + " joined room " + room
			async_to_sync(channel_layer.group_send) (
			room,
			{"type": "push.message", "message": msg, "room_name": room}	)
		elif request.GET.get("leave"):
			msg = user + " left room " + room
			async_to_sync(channel_layer.group_send) (
			room,
			{"type": "push.message", "message": msg, "room_name": room}
		)
	push()
	return JsonResponse({"total_connection": user_conn, "users": users})
	