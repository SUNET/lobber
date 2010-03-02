from django import forms

class UploadForm(forms.Form):
    name = forms.CharField(max_length=128, label="Description", widget=forms.Textarea)
    expires = forms.DateTimeField(label="Expiration date")
    file = forms.FileField(label="Torrent file")

class CreateKeyForm(forms.Form):
    urlfilter = forms.CharField(label="URL filter", widget=forms.Textarea)
    entitlements = forms.CharField(label="Entitlements", widget=forms.Textarea)
    expires = forms.DateTimeField(label="Expiration date")
