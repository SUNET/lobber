from django import forms
from django.forms.widgets import CheckboxInput

class UploadForm(forms.Form):
    description = forms.CharField(label="Description", widget=forms.Textarea)
    expires = forms.DateTimeField(label="Expiration date")
    file = forms.FileField(label="Torrent file")
    publicAccess = forms.BooleanField(label="Allow public access?")

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.content_type == 'application/x-bittorrent':
            raise forms.ValidationError('Not a BitTorrent file...')
        return file
    
class ACLForm(forms.Form):
    acl = forms.MultipleChoiceField(label="Permissions")
        
class CreateKeyForm(forms.Form):
    urlfilter = forms.CharField(label="URL filter", widget=forms.Textarea)
    tagconstraints = forms.CharField(label="Tag constraints", widget=forms.Textarea)
    entitlements = forms.CharField(label="Entitlements", widget=forms.Textarea)
    expires = forms.DateTimeField(label="Expiration date")

class TagForm(forms.Form):
    tags = forms.CharField(label="Tags")