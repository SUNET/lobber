from django.forms import Form
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput, TextInput
from django.forms.widgets import Textarea
from django.forms.fields import CharField, MultipleChoiceField, DateTimeField
from django.forms.fields import FileField, BooleanField
from form_utils.forms import BetterForm
from lobber.settings import ANNOUNCE_URL
from lobber.userprofile.models import user_profile

class UploadForm(BetterForm):
    description = CharField(label="Description", widget=Textarea(attrs={'rows':6,'cols':60}),required=False)
    expires = DateTimeField(label="Expiration")
    file = FileField(label="Data")
    publicAccess = BooleanField(required=False,label="Allow public access?")
    
    def __init__(self, *args, **kwargs):
        '''
        Adds the users available entitlements to the access restriction part of
        the upload form.
        '''
        user = kwargs.pop('user')
        super(UploadForm, self).__init__(*args, **kwargs)
        # We need to show the generated fields but Meta is already read.
        # Solution?
        for e in user_profile(user).get_entitlements():
            self.fields[str(e)] = MultipleChoiceField(required=False, 
                                widget=CheckboxSelectMultiple,
                                choices=[('r','read'),('w','write'),('d','delete')])
    
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
            ('access',{'fields': ['publicAccess'],
                'legend': 'Step 4: Access control (optional)',
                'description': 'Here you can control the access restrictions on your data.',
                'classes': ['step','submit_step']})]


class ACLForm(Form):
    acl = MultipleChoiceField(label="Permissions")


class AddACEForm(Form):
    entitlement = CharField(required=False,max_length=255,widget=HiddenInput)
    subject = CharField(max_length=255,widget=TextInput(attrs={'size':'40'}))
    permissions = MultipleChoiceField(widget=CheckboxSelectMultiple,choices=[('r','read'),('w','write'),('d','delete')])


def formdict():
    return {'permissions': AddACEForm()}

