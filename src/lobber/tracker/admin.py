from django.contrib import admin
from lobber.tracker.models import PeerInfo

class PeerInfoAdmin(admin.ModelAdmin):
    list_display = ('peer_id', 'info_hash', 'address', 'state', 'last_seen')

admin.site.register(PeerInfo, PeerInfoAdmin)
