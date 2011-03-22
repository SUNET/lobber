from django import forms
from django.forms.widgets import CheckboxSelectMultiple,HiddenInput, TextInput
from form_utils.forms import BetterForm
from lobber.settings import ANNOUNCE_URL

class UploadForm(BetterForm):
    description = forms.CharField(label="Description", widget=forms.Textarea(attrs={'rows':6,'cols':60}),required=False)
    expires = forms.DateTimeField(label="Expiration")
    file = forms.FileField(label="Data")
    publicAccess = forms.BooleanField(required=False,label="Allow public access?")
    acl = forms.HiddenInput()
    
    class Meta:
        fieldsets = [('data',{'fields': ['file'],
                              'legend': 'Step 1: Select file to share',
                              'description': 'Select a plain file or a torrent-file for upload. If you provide a torrent-file it has to include the tracker URL <b>'+ANNOUNCE_URL+'</b>',
                              'classes': ['step']
                              }),
                     ('expiration',{'fields': ['expires'],
                                    'legend': 'Step 2: How long should it be valid?',
                                    'description': 'Set an expiration-date for your data. After this day your data will be removed.',
                                    'classes': ['step']}),
                     ('description',{'fields': ['description'],
                                     'legend': 'Step 3: Describe your data (optional)',
                                     'description': 'By providing a short description of your data you make it easier to understand and find for other users.',
                                     'classes': ['step']}),
                     ('access',{'fields': ['publicAccess','acl'],
                                'legend': 'Step 4: Access control (optional)',
                                'description': 'Here you can control the access restrictions on your data.',
                                'classes': ['step','submit_step']})
                     ]
    
class ACLForm(forms.Form):
    acl = forms.MultipleChoiceField(label="Permissions")
    
class AddACEForm(forms.Form):
    entitlement = forms.CharField(required=False,max_length=255,widget=HiddenInput)
    subject = forms.CharField(max_length=255,widget=TextInput(attrs={'size':'40'}))
    permissions = forms.MultipleChoiceField(widget=CheckboxSelectMultiple,choices=[('r','read'),('w','write'),('d','delete')])

class DataLocationForm(forms.Form):
    url = forms.URLField()

def formdict():
    return {'permissions': AddACEForm()}