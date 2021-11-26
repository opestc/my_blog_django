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

@require_POST
def chat_enter(request):
	chat_entry_form = ChatEntryForm(data=request.POST)
	if chat_entry_form.is_valid():
		room_name = request.POST['room_name']
		user_name = request.POST['user_name']
		request.session['user_name'] = request.POST['user_name']
		return JsonResponse({"success": True, "room_name": room_name})
	return JsonResponse({"success": False, "error":"Input is not valid."})

def room(request, room_name):
	user_name = request.session['user_name']
	return render(request, 'chat/room.html', {
		'room_name': room_name, 'user_name':user_name, 'columns':columns
	})
	
def pushRedis(request):
	room = request.GET.get("room")
	user = request.GET.get("user")
	
	users = consumers.ChatConsumer.chats[room]
	user_num = len(users)
	user_conn = consumers.ChatConsumer.user_conn

	#print('room: ' + room + ' user: ' + user + ' connections: ' + str(user_conn))

	def push(msg='test'):
		channel_layer = get_channel_layer()
		if request.GET.get("user_conn"):
			async_to_sync(channel_layer.group_send) (
				room,
				{"type": "push.message", "user_conn": user_conn, "users":list(users)}
			)
		else:
			async_to_sync(channel_layer.group_send) (
			room,
			{"type": "push.message", "message": msg, "room_name": room}
		)
	push()
	return JsonResponse({"total_connection": user_conn, "users": list(users)})
	