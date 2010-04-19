from django.http import HttpResponse
from django.core import serializers
from tagging.models import Tag
from lobber.share.models import Torrent

def list_tags(request):
        try:
                tags = Tag.objects.filter(name__istartswith=request.GET['term']).values_list('name', flat=True)
        except MultiValueDictKeyError:
                pass

        return HttpResponse('\n'.join(tags), mimetype='text/plain')

def add_tag(request):
        t = Torrent.objects.get(tid=request.POST['tid'])
	Tag.objects.add_tag(t,request.POST['name'])
        return HttpResponse()

def get_tags(request):
        t = Torrent.objects.get(tid=request.POST['tid'])
        qs = Tag.objects.get_for_object(t)
        return HttpResponse("\n".join(qs.values_list('name', flat=True).order_by('count')))

def remove_tag(request):
        t = Torrent.objects.get(tid=request.POST['tid'])
        qs = Tag.objects.get_for_object(t)
        tags = qs.values_list('name', flat=True)
        tags.remove(request.POST['name'])
        Tag.objects.update_tags(t,tags)
