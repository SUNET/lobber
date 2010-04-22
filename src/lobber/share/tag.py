from django.http import HttpResponse
from tagging.models import Tag
from lobber.share.models import Torrent
from django.utils.datastructures import MultiValueDictKeyError
from orbited import json
from pprint import pprint

def list_tags(request):
        try:
                tags = map(lambda x: x.name,Tag.objects.filter(name__istartswith=request.GET['term']))
        except MultiValueDictKeyError:
                pass

        r = HttpResponse(json.encode(tags), mimetype='text/x-json')
        
        r['Cache-Control'] = 'no-cache, must-revalidate' 
        r['Pragma'] = 'no-cache'

        return r

def add_tag(request,tid,name):
        t = Torrent.objects.get(id=tid)
        if t is None:
            return HttpResponse(status=404)
        
        if not t.authz_tag(request.user,'w',name):
            return HttpResponse("Not authorized to add tag",status=401)
        
        Tag.objects.add_tag(t,name)
        return HttpResponse(name)

def get_tags(request,tid):
        t = Torrent.objects.get(id=tid)
        if t is None:
            return HttpResponse(status=404)
        
        tags = map(lambda t: t.name,t.readable_tags(request.user))
        r = HttpResponse(json.encode(tags), mimetype='text/x-json')
        
        r['Cache-Control'] = 'no-cache, must-revalidate' 
        r['Pragma'] = 'no-cache'

        return r

def remove_tag(request,tid,name):
        t = Torrent.objects.get(id=tid)
        if t is None:
            return HttpResponse(status=404)
        
        if not t.authz_tag(request.user,'d',name):
            return HttpResponse("Not authorized to remove tag",status=401)
            
        tags = map(lambda x: x.name, t.tags)
        pprint(tags)
        if name in tags:
            tags.remove(name)
            tags_str = ""
            if tags is not None:
                tags_str = " ".join(tags)
            pprint(tags_str)
            Tag.objects.update_tags(t,tags_str)
            
        r = HttpResponse(json.encode(tags), mimetype='text/x-json')
        
        r['Cache-Control'] = 'no-cache, must-revalidate' 
        r['Pragma'] = 'no-cache'

        return r
        