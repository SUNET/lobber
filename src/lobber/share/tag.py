from tagging.models import Tag
from lobber.share.models import Torrent
from django.utils.datastructures import MultiValueDictKeyError
from torrent import find_torrents
from lobber.multiresponse import respond_to, json_response
from django.contrib.auth.decorators import login_required
from lobber.notify import notifyJSON
from django.shortcuts import get_object_or_404
from lobber.share.torrent import torrentdict
from lobber.share.forms import formdict
from lobber.share.models import user_profile
import lobber.log

logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

@login_required
def tag_usage(request):
        r = None
        try:
		tags = []
		if request.GET.has_key('search'): 
			tags = filter(lambda x: x.name.startswith(request.GET['search']),Tag.objects.usage_for_model(Torrent,counts=False))
		else:
			tags = Tag.objects.usage_for_model(Torrent,counts=True)
		tagnames = [tag.name for tag in tags]
		profile = user_profile(request.user)
		tagnames.extend(profile.get_entitlements())
		r = json_response(tagnames)
        except MultiValueDictKeyError,e:
		logger.error(e)
        return r
    
@login_required
def tags(request,tid):
        t = get_object_or_404(Torrent,pk=tid)
        
        if request.method == 'POST':
            to_tags = request.POST.getlist('tags[]')
            from_tags = [tag.name for tag in Tag.objects.get_for_object(t)]
            Tag.objects.update_tags(t,' '.join(to_tags))
            
            # figure out the diff and notify subscribers
            for tag in from_tags:
                if not tag in to_tags:
                    notifyJSON("/torrent/tag/remove",tag)
            for tag in to_tags:
                if not tag in from_tags:
                    notifyJSON("/torrent/tag/add",tag)
        
        d = torrentdict(request,t,formdict())
        return respond_to(request, {'application/json': json_response(d.get('tags')),
                                    'text/html': "share/torrent.html" },d)
    
@login_required
def list_torrents_for_tag(request,name):
        return respond_to(request,
                          {'text/html': 'share/index.html',
                           'application/rss+xml': 'share/rss2.xml',
                           'text/rss': 'share/rss2.xml'},
                          {'torrents': find_torrents(request.user, [('tag',[name])]),
                           'title': 'Torrents tagged with '+name,
                           'tag': name,
                           'description': 'Torrents tagged with '+name})
