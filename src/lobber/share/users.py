from datetime import datetime as dt
import binascii

from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from lobber.multiresponse import make_response_dict
from lobber.settings import LOBBER_LOG_FILE
from lobber.share.models import Torrent, UserProfile
import lobber.log

logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

def create_key_user(creator, urlfilter, tagconstraints, entitlements, expires=None):
    """
    Create a user profile named key:<random text>.  

    Each space separated entitlement in ENTITLEMENTS is checked.
    Invalid entitlements are stripped.  Valid entitlements are
    - user:<CREATOR> and "below" (i.e. user:<CREATOR>:$self)
    - exact match of any entitlement carried by CREATOR

    Also, '$self' is substituted for the name of the newly created key-user.
    """
    creator_profile = None
    try:
        creator_profile = creator.profile.get()
    except ObjectDoesNotExist:
        pass
    if not creator_profile:
        return None

    secret = binascii.hexlify(open('/dev/urandom').read(13))
    username = 'key:%s' % secret

    user = User.objects.create_user(username, 'nomail@dev.null')
    urlfilter = ' '.join(urlfilter.split())
    tagconstraints = ' '.join(tagconstraints.split())

    entls = []
    lst = map(lambda s: s.replace('$self', username), entitlements.split())
    for e in lst:
        if e.startswith('user:%s' % creator.username):
            entls.append(e)
        elif e in creator_profile.get_entitlements():
            entls.append(e)
    entitlements=' '.join(entls)

    profile = UserProfile(user=user,
                          creator=creator,
                          urlfilter=urlfilter,
                          tagconstraints=tagconstraints,
                          entitlements=entitlements,
                          expiration_date=expires)
    profile.save()
    return secret

@login_required
def user_self(req):
    # FIXME: Move to api_user() -- this is GET user/U with
    # representation html.
    lst = []
    for t in Torrent.objects.all().order_by('-creation_date')[:40]:
        if t.authz(req.user, 'r') and t.expiration_date > dt.now():
            lst.append(t)

    return render_to_response('share/user.html', 
                              make_response_dict(req,{'torrents': lst}))

