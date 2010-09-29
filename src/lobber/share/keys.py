from datetime import datetime as dt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect,\
    HttpResponseForbidden, HttpResponseBadRequest
from forms import CreateKeyForm
from lobber.settings import LOBBER_LOG_FILE
from django.contrib.auth.models import User
from lobber.share.users import create_key_user
from lobber.share.models import UserProfile, user_profile
from lobber.multiresponse import respond_to, json_response
import lobber.log
from django.shortcuts import get_object_or_404

logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

def _list_keys(user):
        lst = []
        for p in UserProfile.objects.filter(creator=user).order_by('-id'):
            if p.expiration_date and p.expiration_date <= dt.now():
                continue
            if not p.user.username.startswith('key:'):
                continue
            lst.append(p)
        return lst

@login_required
def remove(request,key):
    keyuser = get_object_or_404(User,username="key:%s" % key)
    keyprofile = user_profile(keyuser)
    if keyprofile.creator.username != request.user.username:
        return HttpResponseForbidden("That is not your key!")
    
    keyprofile.delete()
    keyuser.delete()
    return HttpResponseRedirect("/key")

@login_required
def keys(request):
    profile = user_profile(request.user)
    if request.method == 'GET':
        form = CreateKeyForm()
        form.fields['entitlements'].choices = [(e,e) for e in profile.get_entitlements()]
        return respond_to(request,
                          {"text/html": 'share/keys.html'},{'keys': _list_keys(request.user),'form': form})
        
    elif request.method == 'POST':
        form = CreateKeyForm(request.POST)
        form.fields['entitlements'].choices = [(e,e) for e in profile.get_entitlements()]
        if form.is_valid():
            logger.info(form.cleaned_data['entitlements'])
            secret = create_key_user(request.user,
                                     form.cleaned_data['urlfilter'] or "",
                                     "", #TODO: tagconstraints
                                     " ".join(form.cleaned_data['entitlements']),
                                     form.cleaned_data['expires'])
            return respond_to(request,
                              {'application/json': secret,
                               'text/html': HttpResponseRedirect("/key")})
        else:
            return respond_to(request,
                              {'application/json': "bad request",
                               'text/html': 'share/keys.html'},{'keys': _list_keys(request.user),'form': form})
    
    raise "Bad method: "+request.method
