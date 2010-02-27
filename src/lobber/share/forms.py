from django import forms

class UploadForm(forms.Form):
    name = forms.CharField(max_length=128, label="Description", widget=forms.Textarea)
    expires = forms.DateTimeField(label="Expire date")
    published = forms.BooleanField(initial=True, required=False, label="Publicize")
    file = forms.FileField(label="Torrent file")
