"""my_blog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from chat.views import pushRedis
from django_private_chat2 import urls as django_private_chat2_urls
import notifications.urls
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('article.urls', namespace='article')),
    path('user/', include('users.urls', namespace='users')),
    path('password-reset/', include('password_reset.urls')),
    path('inbox/nottifications/', include(notifications.urls, namespace='notifications')),
    path('comment/', include('comment.urls', namespace='comment')),
    path('webpush/', include('webpush.urls')),
    path('chat/', include('chat.urls',namespace='chat')),
    path("push", pushRedis, name="push"),
    path('webssh/', include('webssh.urls',namespace='webssh')),
    path('notice/', include('notice.urls', namespace='notice')),
    #path('chat2/', include(django_private_chat2_urls)),
    #path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/x-javascript'))
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)