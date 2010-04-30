from datetime import datetime as dt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render_to_response
from forms import CreateKeyForm
from lobber.settings import LOBBER_LOG_FILE
from lobber.share.users import create_key_user
from lobber.share.models import UserProfile
from lobber.multiresponse import make_response_dict
import lobber.log

logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

@login_required
def api_keys(req):
    """
    GET ==> list keys
    POST ==> create key
    """
    def _list(user):
        lst = []
        for p in UserProfile.objects.filter(creator=user).order_by('-id'):
            if p.expiration_date and p.expiration_date <= dt.now():
                continue
            if not p.user.username.startswith('key:'):
                continue
            lst.append(p)
        return lst

    if req.method == 'GET':
        response = render_to_response('share/keys.html', make_response_dict(req,{'keys': _list(req.user)}))
    elif req.method == 'POST':
        form = CreateKeyForm(req.POST)
        if form.is_valid():
            create_key_user(req.user,
                            form.cleaned_data['urlfilter'],
                            form.cleaned_data['tagconstraints'],
                            form.cleaned_data['entitlements'],
                            form.cleaned_data['expires'])
            response = render_to_response('share/keys.html', make_response_dict(req,{'keys': _list(req.user)}))
        else:
            response = render_to_response('share/create_key.html',
                                          make_response_dict(req, {'form': CreateKeyForm()}))
    return response

def key_form(req):
    return render_to_response('share/create_key.html',
                              make_response_dict(req,{'form': CreateKeyForm()}))
