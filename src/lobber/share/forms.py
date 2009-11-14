from django import forms

class UploadTorrentForm(forms.Form):
    file = forms.FileField()
    name = forms.CharField(max_length=128)
    published = forms.BooleanField(initial=True)
    expires = forms.DateTimeField()
