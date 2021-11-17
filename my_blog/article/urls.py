from django.urls import path
from . import views
from django.views.generic import TemplateView
app_name = 'article'

urlpatterns= [
  path('', views.index, name='index'),
  path('list/', views.article_list, name='article_list'),
  path('detail/<int:id>/', views.article_detail, name='article_detail'),
  path('create/', views.article_create, name='article_create'),
  path('article-safe-delete/<int:id>/', views.article_safe_delete, name='article_safe_delete'),
  path('update/<int:id>/', views.article_update, name='article_update'),
  path('calendar/', views.CalendarView.as_view(), name='calendar'),  # 日历表
  path('calendar/event/new/', views.event, name='event_new'),
  path('calendar/event/edit/<int:event_id>', views.event, name='event_edit'),
  path('events/', views.event_modal, name='event_modal'),
  path('event-delete/', views.event_delete, name='event_delete'),
  path('search/', views.search, name='search'),
  path('message', views.message, name='message'),
  path('send_push/', views.send_push, name='send_push'),
  #path('sw.js/', TemplateView.as_view(template_name='sw.js', content_type='application/x-javascript'))
  
]