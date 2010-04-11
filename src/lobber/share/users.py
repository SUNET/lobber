import os
from datetime import datetime as dt
from hashlib import sha256
from random import getrandbits

from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

from lobber.settings import BASE_DIR, MEDIA_ROOT, LOGIN_URL, ANNOUNCE_URL, NORDUSHARE_URL, BASE_UI_URL, LOBBER_LOG_FILE
from lobber.share.models import Torrent, Tag, UserProfile
from forms import UploadForm, CreateKeyForm

from lobber.resource import Resource
import lobber.log
logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

@login_required
def user_self(req):
    # FIXME: Move to api_user() -- this is GET user/U with
    # representation html.
    lst = []
    for t in Torrent.objects.all().order_by('-creation_date')[:40]:
        if t.auth(req.user.username, 'r') and t.expiration_date > dt.now():
            lst.append(t)

    profile = None
    try: 
       profile = req.user.profile.get();
    except ObjectDoesNotExist:
       profile = UserProfile()
       
    return render_to_response('share/user.html', {'user': req.user,
                                                  'profile': profile,
                                                  'torrents': lst})

