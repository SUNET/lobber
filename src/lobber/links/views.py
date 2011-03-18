from time import gmtime, strftime

from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from lobber.settings import NORDUSHARE_URL, LOBBER_LOG_FILE
from lobber.share.models import Torrent, UserProfile
from lobber.notify import notifyJSON
import lobber.log
from django.shortcuts import get_object_or_404
from lobber.links.forms import LinkForm, LinkMessageForm
from lobber.multiresponse import respond_to
from lobber.share.users import create_key_user_profile
from django.core.mail import send_mail

logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

@login_required
def send_link_mail(request,pid,tid):
    t = get_object_or_404(Torrent,pk=tid)
    keyp = get_object_or_404(UserProfile,pk=pid)
    if not keyp.creator == request.user:
        return HttpResponseNotAllowed("Only the key owner may look at this")
    
    if request.method == 'POST':
        form = LinkMessageForm(request.POST)
        if form.is_valid():        
            link = '%s/torrent/%d?lkey=%s' % (NORDUSHARE_URL, t.id, keyp.get_username())
            msg = form.cleaned_data['message']
            msg += "\n"
            msg = "Follow this link to download the data: "+link+"\n\n"
            send_mail(request.user.get_full_name()+" has shared some data with you", 
                      msg, 
                      request.user.email, 
                      [form.cleaned_data['to']])
            return HttpResponseRedirect("/torrent/%d" % (t.id))
    else:
        form = LinkMessageForm()
    
    return respond_to(request,{"text/html": "links/message.html"},{'form': form,'torrent': t})

@login_required
def show_torrent_link(request,pid,tid):
    t = get_object_or_404(Torrent,pk=tid)
    keyp = get_object_or_404(UserProfile,pk=pid)
    if not keyp.creator == request.user:
        return HttpResponseNotAllowed("Only the key owner may look at this")
    
    link = '%s/torrent/%d.torrent?lkey=%s' % (NORDUSHARE_URL, t.id, keyp.get_username())
    return respond_to(request, {"text/html": "links/show.html"}, {'link': link,'pid': keyp.id,'key': keyp.get_username(),'torrent': t})

@login_required
def show_tag_link(request,pid,tag):
    keyp = get_object_or_404(UserProfile,pk=pid)
    if not keyp.creator == request.user:
        return HttpResponseNotAllowed("Only the key owner may look at this")
    
    rsslink = '%s/torrent/tag/%s.rss?lkey=%s' % (NORDUSHARE_URL, tag, keyp.get_username())
    return respond_to(request, {"text/html": "links/show.html"}, {'link': rsslink,'pid':keyp.id,'key': keyp.get_username(),'tag': tag})

@login_required
def link_to_torrent(request,tid):
    t = get_object_or_404(Torrent,pk=tid)
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            keyp = create_key_user_profile(creator=request.user,
                                          urlfilter='/torrent/%d.torrent[^/]*$ /torrent/%d$' % (t.id,t.id),
                                          tagconstraints='',
                                          entitlements='user:%s:$self' % request.user.username,
                                          expires=form.cleaned_data['expires'])
            return HttpResponseRedirect("/link/%d/torrent/%d" % (keyp.id,t.id))
    else:
        form = LinkForm()
    
    return respond_to(request,{"text/html": "links/create.html"},{'torrent': t,'form': form})

@login_required
def link_to_tag(request,tag):
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            keyp = create_key_user_profile(creator=request.user,
                                           urlfilter='/torrent/tag/%s /torrent/.*[^/]+$' % tag,
                                           tagconstraints=tag,
                                           entitlements='user:%s:$self' % request.user.username)

            return HttpResponseRedirect("/link/%d/tag/%s" % (keyp.id,tag))
    else:
        form = LinkForm()
    
    return respond_to(request,{"text/html": "links/create.html"},{'tag': tag,'form': form})