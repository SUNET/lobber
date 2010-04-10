from django import forms

class UploadForm(forms.Form):
    description = forms.CharField(label="Description", widget=forms.Textarea)
    expires = forms.DateTimeField(label="Expiration date")
    file = forms.FileField(label="Torrent file")

class CreateKeyForm(forms.Form):
    urlfilter = forms.CharField(label="URL filter", widget=forms.Textarea)
    entitlements = forms.CharField(label="Entitlements", widget=forms.Textarea)
    expires = forms.DateTimeField(label="Expiration date")

