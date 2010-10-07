from django import forms
from django.forms.widgets import CheckboxInput, CheckboxSelectMultiple,\
    HiddenInput, TextInput, SelectMultiple, Textarea

class UploadForm(forms.Form):
    description = forms.CharField(label="Description", widget=forms.Textarea,required=False)
    expires = forms.DateTimeField(label="Expiration")
    file = forms.FileField(label="Data")
    publicAccess = forms.BooleanField(required=False,label="Allow public access?")
    acl = forms.HiddenInput()
    
class ACLForm(forms.Form):
    acl = forms.MultipleChoiceField(label="Permissions")
    
class AddACEForm(forms.Form):
    entitlement = forms.CharField(required=False,max_length=255,widget=HiddenInput)
    subject = forms.CharField(max_length=255,widget=TextInput(attrs={'size':'40'}))
    permissions = forms.MultipleChoiceField(widget=CheckboxSelectMultiple,choices=[('r','read'),('w','write'),('d','delete')])
        
class CreateKeyForm(forms.Form):
    entitlements = forms.MultipleChoiceField(label="Entitlements",widget=SelectMultiple,required=False)
    urlfilter = forms.CharField(label="URL filter", required=False,widget=Textarea(attrs={'rows':'4'}))
    expires = forms.DateTimeField(label="Expiration date",required=False)

class DataLocationForm(forms.Form):
    url = forms.URLField()

def formdict():
    return {'permissions': AddACEForm()}