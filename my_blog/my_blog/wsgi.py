"""
WSGI config for my_blog project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os, django
from django.core.wsgi import get_wsgi_application
from channels.http import AsgiHandler
from channels.routing import ProtocolTypeRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_blog.settings')
#django.setup()

#application = Cling(get_wsgi_application())
application = ProtocolTypeRouter({
	"http": AsgiHandler(),
	# We will add WebSocket protocol later, but for now it's just HTTP.
})