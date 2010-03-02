from django import forms

class UploadForm(forms.Form):
    name = forms.CharField(max_length=128, label="Description", widget=forms.Textarea)
    expires = forms.DateTimeField(label="Expire date")
    file = forms.FileField(label="Torrent file")
