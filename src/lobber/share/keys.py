from datetime import datetime as dt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from forms import CreateKeyForm
from lobber.settings import LOBBER_LOG_FILE
from lobber.share.users import create_key_user
from lobber.share.models import UserProfile
from lobber.multiresponse import respond_to, json_response
import lobber.log

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
def keys(request):
    if request.method == 'GET':
        return respond_to(request,
                          {"application/json": lambda dict: json_response(dict.get('keys')),
                           "text/html": 'share/keys.html'},{'keys': _list_keys(request.user),'form': CreateKeyForm()})
        
    elif request.method == 'POST':
        form = CreateKeyForm(request.POST)
        if form.is_valid():
            create_key_user(request.user,
                            form.cleaned_data['urlfilter'],
                            form.cleaned_data['tagconstraints'],
                            form.cleaned_data['entitlements'],
                            form.cleaned_data['expires'])
            return respond_to(request,
                              {'application/json': HttpResponse("Created key"),
                               'text/html': HttpResponseRedirect("/key.html")})
        else:
            return respond_to(request,
                              {'application/json': json_response(form.errors),
                               'text/html': 'share/keys.html'},{'keys': _list_keys(request.user),'form': form})
    
    raise "Bad method: "+request.method
