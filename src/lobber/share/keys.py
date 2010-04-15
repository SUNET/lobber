from datetime import datetime as dt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render_to_response
from forms import CreateKeyForm
from lobber.settings import LOBBER_LOG_FILE
from lobber.share.links import _create_key_user
from lobber.share.models import UserProfile
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
        for p in UserProfile.objects.filter(creator=user):
            if p.expiration_date and p.expiration_date <= dt.now():
                continue
            if not p.user.username.startswith('key:'):
                continue
            lst.append(p)
        return lst

    d = {'user': req.user}
        
    if req.method == 'GET':
        d.update({'keys': _list(req.user)})
        response = render_to_response('share/keys.html', d)
    elif req.method == 'POST':
        form = CreateKeyForm(req.POST)
        if form.is_valid():
            _create_key_user(req.user,
                             form.cleaned_data['urlfilter'],
                             form.cleaned_data['entitlements'],
                             form.cleaned_data['expires'])
            d.update({'keys': _list(req.user)})
            response = render_to_response('share/keys.html', d)
        else:
            response = render_to_response('share/create_key.html',
                                          {'form': CreateKeyForm(),
                                           'user': req.user})
    return response

@login_required
def api_key(req, inst):
    """
    GET ==> get key
    DELETE ==> delete key
    """
    response = HttpResponse('NYI: not yet implemented')
    return response

def key_form(req):
    return render_to_response('share/create_key.html',
                              {'form': CreateKeyForm(),
                               'user': req.user})
