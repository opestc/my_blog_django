from django import forms

class ChatEntryForm(forms.Form):
	room_name = forms.CharField()
	user_name = forms.CharField()