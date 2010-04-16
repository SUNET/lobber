from datetime import datetime as dt
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from lobber.multiresponse import respond_to, make_response_dict

from lobber.settings import LOBBER_LOG_FILE
from lobber.share.models import Torrent, UserProfile

import lobber.log
logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

def create_key_user(creator, urlfilter, entitlements, expires=None):
    # FIXME: Do random.seed() somewhere.
    # FIXME: Is 256 bits of random data proper?
    # FIXME: Don't chop the digest!!!  Necessary for now, since
    # Djangos User class allows for max 30 characters user names.
    secret = sha256(str(getrandbits(256))).hexdigest()[:26]
    username = 'key:%s' % secret
    user = User.objects.create_user(username, 'nomail@dev.null', username)

    lst = map(lambda s: s.replace('$self', username), entitlements.split())
    entls = ' '.join(map(lambda e: 'user:%s:%s' % (creator.username, e), lst))
    profile = UserProfile(user=user,
                          creator=creator,
                          urlfilter=' '.join(urlfilter.split()),
                          entitlements=entls,
                          expiration_date=expires)
    profile.save()
    return secret

@login_required
def user_self(req):
    # FIXME: Move to api_user() -- this is GET user/U with
    # representation html.
    lst = []
    for t in Torrent.objects.all().order_by('-creation_date')[:40]:
        if t.auth(req.user.username, 'r') and t.expiration_date > dt.now():
            lst.append(t)

    return render_to_response('share/user.html', 
                              make_response_dict(req,{'torrents': lst}))

