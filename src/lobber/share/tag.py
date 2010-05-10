from django.http import HttpResponse, HttpResponseRedirect
from tagging.models import Tag
from lobber.share.models import Torrent
from django.utils.datastructures import MultiValueDictKeyError
from orbited import json
from pprint import pprint
from torrent import find_torrents
from lobber.multiresponse import respond_to, json_response
from django.contrib.auth.decorators import login_required
from lobber.notify import notifyJSON
from django.core.exceptions import ObjectDoesNotExist
from lobber.share.forms import TagForm
from tagging.utils import parse_tag_input

@login_required
def tag_usage(request):
        q = request.GET['search']
        r = None
        try:
            tags = filter(lambda x: x.name.startswith(q),Tag.objects.usage_for_model(Torrent,counts=True))
            r = json_response([{'tag': tag.name, 'freq': tag.count} for tag in tags])
        except MultiValueDictKeyError,e:
            pprint(e)
        return r
    
@login_required
def tags(request,tid):
        t = Torrent.objects.get(id=tid)
        if t is None:
            return HttpResponse(status=404)
        
        if request.method == 'GET':
            try:
                tags = map(lambda t: t.name,t.readable_tags(request.user))
                return respond_to(request, {'application/json': lambda dict: json_response(dict.get('tags')),
                                            'text/html': "share/tags.html" }, {'tags': tags, 'form': TagForm()})
            except Exception,e:
                pprint(e)
                raise e
        
        if request.method == 'POST':
            form = TagForm(request.POST)
            if not form.is_valid():
                return respond_to(request, {'application/json': json_response(dict.get('form').errors),
                                            'text/html': "share/tags.html" }, {'tags': tags, 'form': form})
            
            try:
                to_tags = parse_tag_input(form.cleaned_data['tags'])
                from_tags = Tag.objects.get_for_object(t)
                Tag.objects.update_tags(t, form.cleaned_data['tags'])
                
                # figure out the diff and notify subscribers
                for tag in from_tags:
                    if not tag in to_tags:
                        notifyJSON("/torrent/tag/remove",tag)
                for tag in to_tags:
                    if not tag in from_tags:
                        notifyJSON("/torrent/tag/add",tag)
            except Exception,e:
                pprint(e)
            
            return respond_to(request, {'application/json': HttpResponse("Tagged "+t.name+" with "+to_tags.join(',')),
                                        'text/html': HttpResponseRedirect("/torrent/#"+tid)})
            

        raise "Bad method: "+request.method
        
@login_required
def list_torrents_for_tag(request,name):
        return respond_to(request,
                          {'text/html': 'share/index.html',
                           'application/rss+xml': 'share/rss2.xml',
                           'text/rss': 'share/rss2.xml'},
                          {'torrents': find_torrents(request.user, [('tag',[name])]),
                           'title': 'Torrents tagged with '+name,
                           'description': 'Torrents tagged with '+name})
