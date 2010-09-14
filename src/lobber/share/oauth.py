'''
Created on Sep 14, 2010

@author: leifj
'''
from lobber.multiresponse import respond_to, json_response
from oauth_provider.models import Consumer
from lobber.share.forms import CreateConsumerForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

@login_required
def consumers(request):  
    if request.method == 'POST':
        form = CreateConsumerForm(request.POST)
        if form.is_valid():
            consumer = Consumer.objects.create_consumer(form.cleaned_data['name'], request.user)
            consumer.description = form.cleaned_data['description']
            consumer.save()
            return respond_to(request,{'text/html': HttpResponseRedirect("/consumers")})
    else:
        form = CreateConsumerForm()
            
    consumers = Consumer.objects.filter(user=request.user)
    return respond_to(request,
                      {"text/html": 'share/consumers.html'},
                      {'consumers': consumers,'form': form})
    
    
def delete_consumer(request,key):
    consumer = get_object_or_404(Consumer,key=key)
    consumer.delete()
    return HttpResponseRedirect("/consumers")