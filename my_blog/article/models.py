from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from taggit.managers import TaggableManager
from PIL import Image
import time
# Create your models here.
class ArticleColumn(models.Model):
  title = models.CharField(max_length=100, blank=True)
  created = models.DateTimeField(default=timezone.now)
  
  def __str__(self):
    return self.title
  
class ArticlePost(models.Model):
  
  author = models.ForeignKey(User, on_delete=models.CASCADE)
  title = models.CharField(max_length=100)
  avatar = models.ImageField(upload_to='article/%Y%m%d',blank=True)
  tags = TaggableManager(blank=True)
  def save(self, *args, **kwargs):
      # 调用原有的 save() 的功能
      article = super(ArticlePost, self).save(*args, **kwargs)
    
      # 固定宽度缩放图片大小
      if self.avatar and not kwargs.get('update_fields'):
        image = Image.open(self.avatar)
        (x, y) = image.size
        new_x = 200
        new_y = int(new_x * (y / x))
        resized_image = image.resize((new_x, new_y), Image.ANTIALIAS)
        resized_image.save(self.avatar.path)
        
      return article
  
  body = models.TextField()
  created = models.DateTimeField(default=timezone.now)
  updated = models.DateTimeField(auto_now=True)
  total_views = models.PositiveIntegerField(default=0)
  column = models.ForeignKey(
    ArticleColumn,
    null=True,
    blank=True,
    on_delete=models.CASCADE,
    related_name='article'
  )
  class Meta:    
    ordering = ('-created',)
  
  def __str__(self):
    return self.title
  
  def get_absolute_url(self):
    return reverse('article:article_detail', args=[self.id])

class Banner(models.Model):
  title=models.CharField('标题',max_length=50)
  pic=models.ImageField('轮播图',upload_to='banner/%Y%m%d')
  link_url=models.URLField('图片连接',max_length=100)
  idx=models.IntegerField('索引排序')
  is_active=models.BooleanField('是否是active',default=False)
  create_time=models.DateTimeField('创建时间',default=timezone.now)
  
  def __str__(self):
    return self.title
  
  class Meta:
    ordering = ("-create_time", "-idx")

class Event(models.Model):
  title = models.CharField(max_length=255, null=True, blank=True)
  start_time = models.DateTimeField(default='')
  end_time = models.DateTimeField(default='')
  create_time = models.DateTimeField(default=timezone.now)
  description = models.TextField(max_length=20, null=True, blank=True)
  
  def __str__(self):
    return self.title
  
  class Meta:
    ordering = ("start_time",)
    
  @property
  def get_html_url(self):
    start = str(self.start_time)
    t = time.strptime(start, '%Y-%m-%d %H:%M:%S%z')
    t = time.strftime('%H:%M',t)
    url = reverse('article:event_edit', args=[self.id])
    return f'<a href="{url}">{t} {self.title} </a>'
  