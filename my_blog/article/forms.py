from django import forms
from .models import ArticlePost, Event

class ArticlePostForm(forms.ModelForm):
  class Meta:
    model = ArticlePost
    fields = ('title', 'body', 'tags', 'avatar')

class EventForm(forms.ModelForm):
  class Meta:
    model = Event
# datetime-local is a HTML5 input type, format to make date time show on fields
    widgets = {
      'title': forms.TextInput(attrs={
        'id': 'event-title',
        'required': True, 
        'placeholder': 'Title'
      }),
      'start_time': forms.DateInput(attrs={'id':'event-start', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
      'end_time': forms.DateInput(attrs={'id':'event-end', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
      'description':forms.TextInput(attrs={
        'id': 'event-text', 
        'placeholder': 'More info...'
      }),
    }
    fields = '__all__'
    
  def __init__(self, *args, **kwargs):
    super(EventForm, self).__init__(*args, **kwargs)
    # input_formats to parse HTML5 datetime-local input to datetime field
    self.fields['start_time'].input_formats = ('%Y-%m-%dT%H:%M',)
    self.fields['end_time'].input_formats = ('%Y-%m-%dT%H:%M',)