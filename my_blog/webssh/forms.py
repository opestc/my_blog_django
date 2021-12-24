from django import forms

class SSHEntryForm(forms.Form):
	user_name = forms.CharField()