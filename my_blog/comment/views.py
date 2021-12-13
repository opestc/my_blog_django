from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from article.models import ArticlePost
from .forms import CommentForm
from notifications.signals import notify
from django.contrib.auth.models import User
from .models import Comment

# comments
@login_required(login_url='user/login/')
def post_comment(request, article_id, parent_comment_id=None):
	article = get_object_or_404(ArticlePost, id=article_id)
	
	if request.method =='POST':
		comment_form = CommentForm(request.POST)
		if comment_form.is_valid():
			new_comment = comment_form.save(commit=False)
			new_comment.article = article
			new_comment.user = request.user
			
			if parent_comment_id:
				parent_comment = Comment.objects.get(id=parent_comment_id)
				new_comment.parent_id = parent_comment.get_root().id
				new_comment.reply_to = parent_comment.user
				new_comment.save()
				if not parent_comment.user.is_superuser:
					notify.send(
						request.user,
						recipient=parent_comment.user,
						verb='replied to you',
						target=article,
						action_object=new_comment,
					)
				return HttpResponse('200 OK')
			
			new_comment.save()
			if not request.user.is_superuser:
				notify.send(
						request.user,
						recipient=User.objects.filter(is_superuser=1),
						verb='replied to you',
						target=article,
						action_object=new_comment,
					)
			return redirect("article:article_detail", id=article_id)
		else:
			return HttpResponse("内容有误，请重新填写。")
	
	elif request.method == 'GET':
		comment_form = CommentForm()
		context = {
			'comment_form':comment_form,
			'article_id':article_id,
			'parent_comment_id':parent_comment_id
		}
		return render(request, 'comment/reply.html',context)
	else:
		return HttpResponse("发表评论仅接受POST请求。")

# Create your views here.
	