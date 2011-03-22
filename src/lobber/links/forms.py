'''
Created on Oct 19, 2010

@author: leifj
'''
from django import forms
from django.forms.widgets import Textarea
from form_utils.forms import BetterForm

class LinkForm(BetterForm):
    expires = forms.DateField(label="Expiration date")
    
    class Meta:
        fieldsets = [('step',{'fields': ['expires'],
                              'legend': 'Expiration date for your share',
                              'classes': ['step','submit_step'],
                              'description': 'A sharable link to your data is a URL which you can give to anyone who should be able to download the data. After the expiration date has passed the link will be invalidated.'})]
    
class LinkMessageForm(BetterForm):
    to = forms.EmailField()
    message = forms.CharField(required=False,widget=Textarea(attrs={'rows':'4'}))
    
    class Meta:
        fieldsets = [('step',{'fields': ['to','message'],
                              'legend': 'Destination and Message',
                              'classes': ['step','submit_step'],
                              'description': 'Provide a list of recipients and optionally a helpful message. An email will be sent which contains the share-link. When the the recipient clicks on the link they will be presented with options for downloading the data.'})]

    