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

def add_tag(request):
        t = Torrent.objects.get(id=request.REQUEST['tid'])
        Tag.objects.add_tag(t,request.REQUEST['name'])
        return HttpResponse()

def get_tags(request):
        t = Torrent.objects.get(id=request.REQUEST['tid'])
        lst = map(lambda t: t.name, t.tags)
        return HttpResponse("\n".join(lst))

def remove_tag(request):
        pprint(request.REQUEST['tid'])
        t = Torrent.objects.get(id=request.REQUEST['tid'])
        if t is None:
            return
        pprint(t)
        lst = map(lambda t: t.name, t.tags)
        name = request.REQUEST['name']
        pprint(name)
        pprint(lst)
        pprint("hej")
        if name in lst:
            lst = lst.remove(name)
            pprint(lst)
            tags = ""
            if lst is not None:
                tags = " ".join(lst)
            pprint("hoho:" + tags)
            Tag.objects.update_tags(t,tags)
        
        return HttpResponse()