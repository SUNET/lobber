from django import forms

class UploadForm(forms.Form):
    name = forms.CharField(max_length=128, label="Description")
    expires = forms.DateTimeField(label="Expire date")
    published = forms.BooleanField(initial=True, required=False, label="Listed")

class UploadTorrentForm(UploadForm):
    file = forms.FileField(label="Torrent file")

class UploadAppletForm(UploadForm):
    file = forms.FileField(label="foo bar bletch")
