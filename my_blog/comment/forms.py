#!/usr/bin/env python3
from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
	class Meta:
		model = Comment
		fields = ['body']
		
