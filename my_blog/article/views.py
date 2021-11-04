from django.shortcuts import render,redirect,get_object_or_404
from .models import ArticlePost,ArticleColumn
from django.http import HttpResponse,Http404
from .forms import ArticlePostForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from comment.models import Comment
from django.contrib import messages
import markdown, re

columns = ArticleColumn.objects.all()

md = markdown.Markdown(
  extensions=[
  'markdown.extensions.extra',
  'markdown.extensions.codehilite',
  'markdown.extensions.toc',
  ])
  
def params_replace(data):
  for column in columns:
    if column.title == 'Home':
      data['column']=str(column.id)
  return data

def index(request):
  method = request.method
  
  if method == 'GET':
    data = request.GET.copy()
    data = params_replace(data)
  if data:
    request.GET = data
    
  return article_list(request)

def article_list(request):
  
  search = request.GET.get('search')
  order = request.GET.get('order')
  column = request.GET.get('column')
  tag = request.GET.get('tag')
  
  articles = ArticlePost.objects.all()
  

  # 搜索查询集
  if search:
    articles = articles.filter(
      Q(title__icontains=search) |
      Q(body__icontains=search)
    )
    
  else:
    search = ''
    
  # 栏目查询集
  if column is not None:
    if column.isdigit():
      articles = articles.filter(column=column)
    else:
      raise Http404
  # 标签查询集
  if tag and tag != 'None':
    articles = articles.filter(tags__name__in=[tag])
    
  # 查询集排序
  if order == 'total_views':
    articles = articles.order_by('-total_views')
    
  paginator = Paginator(articles,10)
  page = request.GET.get('page')
  articles = paginator.get_page(page)
  for article in articles:
    article.body = md.convert(article.body)
  context = {
    'articles': articles,
    #'toc':md.toc, 
    'order':order,
    'search':search,
    'column':column,
    'tag':tag,
    'columns':columns
  }
#  if not articles:
#    messages.error(request,"No articles found.")
  return render(request,'article/list.html',context)


def article_detail(request, id):
  article = ArticlePost.objects.get(id=id)
  comments = Comment.objects.filter(article=id)
  
  if request.user != article.author:
    article.total_views += 1
  article.save(update_fields=['total_views'])
  article.body = md.convert(article.body)
  m = re.search(r'<div class="toc">\s*<ul>(.*)</ul>\s*</div>', md.toc, re.S)
  toc = m.group(1) if m is not None else ''
  context = {
    'article':article, 
    'toc':toc, 
    'comments':comments,
    'columns':columns
  }
  return render(request,'article/detail.html',context)

@login_required(login_url='/user/login')
def article_create(request):
  if request.method == "POST":
    article_post_form = ArticlePostForm(request.POST, request.FILES)
    if article_post_form.is_valid():
      new_article = article_post_form.save(commit=False)
      new_article.author = User.objects.get(id=request.user.id)
      if request.POST['column'] != 'none':
        new_article.column = ArticleColumn.objects.get(id=request.POST['column'])
      new_article.save()
      
      # tags的多对多关系
      article_post_form.save_m2m()    
    else:
      messages.error(request,"Input is not valid")
    return redirect("article:article_create")
  else:
    article_post_form = ArticlePostForm(request.POST, request.FILES)
    context = {
      'article_post_form': article_post_form, 
      'columns':columns
    }
    return render(request,'article/create.html',context)

@login_required(login_url='/user/login/')
def article_safe_delete(request, id):
  article = ArticlePost.objects.get(id=id)
  if request.user != article.author or request.method != 'POST':
    messages.error(request,"You have no permission.")
    return redirect("article:article_detail", id=id)
  else:
    article.delete()
    return redirect("article:article_list")

@login_required(login_url='/user/login/')
def article_update(request, id):
  article = ArticlePost.objects.get(id=id)
  
  if request.user != article.author:
    return HttpResponse("You have no permission.")
  if request.method == "POST":
    article_post_form = ArticlePostForm(request.POST, request.FILES)
    if article_post_form.is_valid():
      article.title = request.POST['title']
      article.body = request.POST['body']
      article.tags.set(*request.POST.get('tags').split(','), clear = True)
      if request.FILES.get('avatar'):
        article.avatar = request.FILES.get('avatar')
      if request.POST['column'] != 'none':
        article.column = ArticleColumn.objects.get(id=request.POST['column'])
      else:
        article.column = None
      article.save()
    else:
      messages.error(request,"Input is not valid")
      
    return redirect("article:article_detail", id=id)
  
  else:
    article_post_form = ArticlePostForm()
    
    context = {
      'article':article, 
      'article_post_form':article_post_form, 
      'columns':columns,
      'tags':','.join([x for x in article.tags.names()]),
    }
    return render(request, 'article/update.html', context)
  
  