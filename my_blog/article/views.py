from datetime import datetime, timedelta, date
from django.shortcuts import render,redirect,get_object_or_404
from .models import ArticlePost,ArticleColumn,Banner,Event
from .utils import Calendar
from django.http import HttpResponse,Http404
from .forms import ArticlePostForm, EventForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from comment.models import Comment
from comment.forms import CommentForm
from django.contrib import messages
from django.views import generic
from django.utils.safestring import mark_safe
from bootstrap_modal_forms.generic import BSModalLoginView
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from webpush import send_user_notification
import markdown, re, calendar, json, time
from dateutil import tz
from django.conf import settings
from django.http import JsonResponse
import urllib, string

columns = ArticleColumn.objects.all()
mytz = tz.gettz('Asia/Shanghai')

md = markdown.Markdown(
  extensions=[
  'markdown.extensions.extra',
  'markdown.extensions.codehilite',
  'markdown.extensions.toc',
  ])

def params_replace(data):
  for column in columns:
    if column.title == 'Home':
      banner_list=Banner.objects.all()
      data['column']=str(column.id)
      data['banner_list'] = banner_list
  return data

@require_GET
def index(request):
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
  banner_list=Banner.objects.all()
  articles = ArticlePost.objects.all()
  events=Event.objects.all()
  context = {}

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
  context={
    'articles': articles,
    #'toc':md.toc, 
    'order':order,
    'search':search,
    'column':column,
    'tag':tag,
    'columns':columns,
    'banner_list':banner_list,
    'events':events
  }
#  if not articles:
#    messages.error(request,"No articles found.")
  return render(request,'article/list.html',context)


def article_detail(request, id):
  article = ArticlePost.objects.get(id=id)
  comments = Comment.objects.filter(article=id)
  events=Event.objects.all()
  if request.user != article.author:
    article.total_views += 1
  article.save(update_fields=['total_views'])
  article.body = md.convert(article.body)
  
  #remove blanks
  m = re.search(r'<div class="toc">\s*<ul>(.*)</ul>\s*</div>', md.toc, re.S) 
  toc = m.group(1) if m is not None else ''
  comment_form = CommentForm()
  context = {
    'article':article, 
    'toc':toc, 
    'comments':comments,
    'columns':columns,
    'events':events,
    'comment_form':comment_form,
  }
  return render(request,'article/detail.html',context)

@login_required(login_url='/user/login')
def article_create(request):
  events=Event.objects.all()
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
      messages.success(request, 'The article was created successfully.')
      return redirect("article:article_list")
    else:
      messages.error(request,"Input was not valid")
    return redirect("article:article_create")
  else:
    article_post_form = ArticlePostForm(request.POST, request.FILES)
    context = {
      'article_post_form': article_post_form, 
      'columns':columns,
      'events':events
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
  # ini = {'body': article.body}
  events=Event.objects.all()
  if request.user != article.author:
    messages.error(request,"You have no permission.")
    return redirect("article:article_detail", id=id)
  if request.method == "POST":
    article_post_form = ArticlePostForm(request.POST, request.FILES)
    # article_post_form = ArticlePostForm(initial=ini)
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
      messages.success(request,"The article was updated successfully.")
    else:
      messages.error(request,"Input was not valid")
      
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
  
  
class CalendarView(generic.ListView):
  model = Event
  template_name = 'article/calendar.html'
  
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    #d = get_date(self.request.GET.get('day', None))
    #cal = Calendar(d.year, d.month)
    #html_cal = cal.formatmonth(withyear=True)
    #context['calendar'] = mark_safe(html_cal)
    
    d = get_date(self.request.GET.get('month', None))
    cal = Calendar(d.year, d.month)
    html_cal = cal.formatmonth(withyear=True)
    context['calendar'] = mark_safe(html_cal)
    context['prev_month'] = prev_month(d)
    context['next_month'] = next_month(d)
 
    return context
  
def get_date(req_day):
  if req_day:
    year, month = (int(x) for x in req_day.split('-'))
    return date(year, month, day=1)
  return datetime.today()

def prev_month(d):
  first = d.replace(day=1)
  prev_month = first - timedelta(days=1)
  month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
  return month

def next_month(d):
  days_in_month = calendar.monthrange(d.year, d.month)[1]
  last = d.replace(day=days_in_month)
  next_month = last + timedelta(days=1)
  month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
  return month

def event(request, event_id=None):
  instance = Event()
  if event_id:
    instance = get_object_or_404(Event, pk=event_id)    
  form = EventForm(request.POST or None, instance=instance)
  if request.POST and form.is_valid() and request.user.is_superuser:
      response = {}
      form.save()
      eventObj = Event.objects.order_by('-pk')[0]
      response['id'] = eventObj.id
      response['title'] = eventObj.title
      response['start'] = eventObj.start_time.astimezone(mytz)
      response['end'] = eventObj.end_time.astimezone(mytz)
      response['description'] = eventObj.description
      
      return HttpResponse(
        json.dumps(response,indent=4, sort_keys=True, default=str), # change datetime in json type
        content_type="application/json"
      )
  if request.method == 'GET' :
      return render(request, 'article/event.html', {'form':form})
  return HttpResponse(
    json.dumps({"error":"You have no permission."}),
    content_type="application/json") 

  
def event_modal(request):
  events=Event.objects.all()
  return render(request, 'article/cal_modal.html', {'events':events})

def event_delete(request):

  if not request.user.is_superuser  or request.method != 'POST':
    messages.error(request,"You have no permission.")

  else:
    id = request.POST['id']
    event = Event.objects.get(id=id)
    event.delete()
  return redirect("article:calendar")

# design search results
def search(request):
  q=request.GET.get('search')
  error_msg, results = '', ''
  if not q:
    error_msg = 'Please input keywords.'
  search_articles = ArticlePost.objects.filter(
    Q(title__icontains=q) |
    Q(body__icontains=q)
  )
  for article in search_articles:
    results += f'<hr><h4><b><a href="{article.get_absolute_url}" style="color: black;" target="_blank">{article.title}</a></b> &nbsp;&nbsp;&nbsp;'

    if article.tags:
      for tag in article.tags.all():
        results += f'<span class="badge badge-secondary">{tag.name}</span>&nbsp;'
    results += f'</h4><p>{article.body}</p>'
    if article.column:
      results += f'<span class="badge badge-primary">{article.column}</span>&nbsp;&nbsp;&nbsp;'
    created = str(article.created.replace(microsecond=0))
    t = time.strptime(created, '%Y-%m-%d %H:%M:%S%z')
    t = time.strftime('%Y-%m-%d %H:%M',t)
    results += f'{t}</span>'
    
  return HttpResponse(
      json.dumps({'error_msg':error_msg,'results':results}),
      content_type="application/json") 

# send push notification
@require_POST
@csrf_exempt
def send_push(request):
  try:
    body = request.body
    data = json.loads(body)
    
    if 'head' not in data or 'body' not in data or 'id' not in data:
      return JsonResponse(status=400, data={"message": "Invalid data format"})
    user_id = data['id']
    user = get_object_or_404(User, pk=user_id)
    payload = {'head': data['head'], 'body': data['body']}
    send_user_notification(user=user, payload=payload, ttl=1000)
    
    return JsonResponse(status=200, data={"message": "Web push successful"})
  except TypeError:
    return JsonResponse(status=500, data={"message": "An error occurred"})  
  
@require_GET
def message(request):
  webpush_settings = getattr(settings, 'WEBPUSH_SETTINGS', {})
  vapid_key = webpush_settings.get('VAPID_PUBLIC_KEY')
  user = request.user
  webpush = {"group": 'test' }
  return render(request, 'message.html', {'user': user, 'vapid_key': vapid_key, 'columns':columns})

def chat(request):
  target = r'http://api.qingyunke.com/api.php?key=free&appid=0&msg='
  print("=================")
  keyword = request.POST.get("content")
  if keyword:
    tmp = target + keyword
    url = urllib.parse.quote(tmp, safe=string.printable)
    page = urllib.request.urlopen(url)
    
    html = page.read().decode("utf-8")
    res = json.loads(html)
    answer = res['content']
    return JsonResponse(answer, json_dumps_params={'ensure_ascii':False}, safe=False)
  return render(request, 'chatbot.html')