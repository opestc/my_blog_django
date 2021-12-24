from django.urls import re_path, path

from . import consumers

websocket_urlpatterns = [
	re_path(r'ws/webssh/(?P<host_id>\d+)/$', consumers.WebsshConsumer.as_asgi()),
	path('ws/webssh/', consumers.WebsshConsumer.as_asgi()),
]

