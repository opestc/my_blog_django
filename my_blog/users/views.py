from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.contrib import messages
from .forms import UserLoginForm, ProfileForm
from .models import Profile
from article.models import ArticleColumn

columns = ArticleColumn.objects.all()

def user_login(request):
  if request.method == "POST":
    user_login_form = UserLoginForm(data=request.POST)
    if user_login_form.is_valid():
      data = user_login_form.cleaned_data
      user = authenticate(username=data['username'], password=data['password'])
      if user:
        login(request, user)
        return redirect("article:article_list")
      else:
        messages.error(request,"Username or password is wrong")
        return redirect("users:login")
    else:
      messages.error(request,"Input is not valid")
      return redirect("users:login")
  elif request.method == 'GET':
    user_login_form = UserLoginForm()
    context = {'form': user_login_form, 'columns':columns }
    return render(request, 'users/login.html', context)
  else:
    return HttpResponse("Please use GET or POST to get data")



def user_logout(request):
  logout(request)
  return redirect("article:index")

'''
def user_register(request):
  if request.method == 'POST':
    user_register_form = UserRegisterForm(data=request.POST)
    if user_register_form.is_valid():
      new_user = user_register_form.save(commit=False)
      # 设置密码
      new_user.set_password(user_register_form.cleaned_data['password'])
      new_user.save()
      # 保存好数据后立即登录并返回博客列表页面
      login(request, new_user)
      return redirect("article:article_list")
    else:
      return HttpResponse("Wrong input, please input again")
  elif request.method == 'GET':
    user_register_form = UserRegisterForm()
    context = { 'form': user_register_form }
    return render(request, 'users/register.html', context)
  else:
    return HttpResponse("请使用GET或POST请求数据")
'''

@login_required(login_url='/user/login/')
def user_delete(request, id):
  if request.method == 'POST':
    user = User.objects.get(id=id)
    if request.user == user:
      logout(request)
      user.delete()
      return redirect("article:article_list")
    else:
      return HttpResponse("You have no permission")
  else:
    return HttpResponse("Only for post request")
  
@login_required(login_url='/user/login')
def profile_edit(request, id):
  user = User.objects.get(id=id)
  
  if Profile.objects.filter(user_id=id).exists():
    profile = Profile.objects.get(user_id=id)
  else:
    profile = Profile.objects.create(user=user)
  if request.method == 'POST':
    if request.user != user:
      return HttpResponse("You have no permission.")
    
    profile_form = ProfileForm(request.POST, request.FILES)
    if profile_form.is_valid():
      profile_cd = profile_form.cleaned_data
      profile.email = profile_cd['email']
      profile.bio = profile_cd['bio']
      if 'avatar' in request.FILES:
        profile.avatar = profile_cd['avatar']
      profile.save()
      return redirect("users:edit", id=id)
    else:
      messages.error(request,"Input is not valid")
      return redirect("users:edit", id=id)
    
  elif request.method == 'GET':
    #profile_form = ProfileForm()
    context = {'profile':profile, 'user':user, 'columns':columns}
    return render(request, 'users/edit.html',context)
  else:
    return HttpResponse("Only allow POST/GET")
  