from django.contrib import admin
from .models import ArticlePost,ArticleColumn,Banner,Event
# Register your models here.
admin.site.register(ArticlePost)
admin.site.register(ArticleColumn)
admin.site.register(Banner)
admin.site.register(Event)
