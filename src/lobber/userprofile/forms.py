'''
Created on Mar 22, 2011

@author: leifj
'''
from django.forms.widgets import SelectMultiple, Textarea
from django import forms
from form_utils.forms import BetterForm

class CreateKeyForm(BetterForm):
    entitlements = forms.MultipleChoiceField(label="Entitlements",widget=SelectMultiple,required=False)
    urlfilter = forms.CharField(label="URL filter", required=False,widget=Textarea(attrs={'rows':'4'}))
    expires = forms.DateTimeField(label="Expiration date",required=False)
    
    class Meta:
        fieldsets = [('delegation', {'fields': ['entitlements'],
                                     'legend': 'Step 1: Delegated Rights',
                                     'description': 'Select a set of entitlements to delegate to the application key. When an application authenticates to lobber using this key it will have all rights given to any of the entitlements you choose in this step.',
                                     'classes': ['step']}),
                     ('expiration', {'fields': ['expires'],
                                     'legend': 'Step 2: Expiration date (optional)',
                                     'classes': ['step'],
                                     'description': 'By selecting an expiration date you limit the time this key will be valid.'}),
                     ('constraints', {'fields': ['urlfilter'],
                                      'legend': 'Step 3: Constraints (optional)',
                                      'description': 'Constrain the things an application can do using this key by entering a set of regular expressions. At least one of these regular expressions must match the request URL. If you leave this field blank no URLs will be permitted.',
                                      'classes': ['step','submit_step']})]