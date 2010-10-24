'''
Created on Oct 19, 2010

@author: leifj
'''
from django import forms
from django.forms.widgets import Textarea

class LinkForm(forms.Form):
    expires = forms.DateField(label="Expiration date")
    
class LinkMessageForm(forms.Form):
    to = forms.EmailField()
    message = forms.CharField(required=False,widget=Textarea(attrs={'rows':'4'}))

    