from django import forms
from django.forms.widgets import TextInput, HiddenInput
from form_utils.forms import BetterForm
from lobber.settings import ANNOUNCE_URL
from django.forms.models import ModelChoiceField
from django.contrib.auth.models import Group
from django.forms.forms import Form
from django.db.models import Q


class UploadForm(BetterForm):
    description = forms.CharField(label="Description", widget=forms.Textarea(attrs={'rows':6,'cols':60}),required=False)
    expires = forms.DateTimeField(label="Expiration")
    file = forms.FileField(label="Data")
    storage = ModelChoiceField(Group.objects.filter(Q(user__username__startswith='key:') | Q(name='Public Storage')),required=False)
    public = forms.BooleanField(label='Allow public access?')
    
    class Meta:
        fieldsets = [('data',{'fields': ['file'],
                              'legend': 'Step 1: Select file to share',
                              'description': 'Select a plain file or a torrent-file for upload. If you provide a torrent-file it has to include the tracker URL <b>'+ANNOUNCE_URL+'</b>',
                              'classes': ['step']
                              }),
                     ('expiration',{'fields': ['expires','public'],
                                    'legend': 'Step 2: How long should it be valid?',
                                    'description': 'Set an expiration-date for your data. After this day your data will be removed. If you want your data to be readable by all users on the system check the box for public access.',
                                    'classes': ['step']}),
                     ('description',{'fields': ['description'],
                                     'legend': 'Step 3: Describe your data (optional)',
                                     'description': 'By providing a short description of your data you make it easier to understand and find for other users.',
                                     'classes': ['step']}),
                     ('storage',{'fields': ['storage'],
                                'legend': 'Step 4: Storage (optional)',
                                'description': 'Select storage for your data. Each item represents a group of storage resources. Pick one you trust to keep your data safe! Public storage is provided by the operators of the system. If you do not select any storage below, public storage will be used.',
                                'classes': ['step','submit_step']})
                     ]
    
class AddACEForm(Form):
    subject_id = forms.IntegerField(widget=HiddenInput(),required=False)
    subject_type = forms.CharField(widget=HiddenInput(),required=False)
    who = forms.CharField(max_length=255,widget=TextInput(attrs={'size':'40'}))
    permission = forms.ChoiceField(choices=(('r','read'),('w','read and write'),('d','remove')))

def formdict():
    return {'permissions': AddACEForm()}