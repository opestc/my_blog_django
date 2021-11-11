from django.urls import path
from . import views

app_name = 'article'

urlpatterns= [
  path('', views.index, name='index'),
  path('list/', views.article_list, name='article_list'),
  path('detail/<int:id>/', views.article_detail, name='article_detail'),
  path('create/', views.article_create, name='article_create'),
  path('article-safe-delete/<int:id>/', views.article_safe_delete, name='article_safe_delete'),
  path('update/<int:id>/', views.article_update, name='article_update'),
  path('calendar/', views.CalendarView.as_view(), name='calendar'),  # 日历表
  path('add_event/', views.add_event, name='add_event'), 
  path('calendar/event/new/', views.event, name='event_new'),
  path('calendar/event/edit/<int:event_id>', views.event, name='event_edit'),
]
