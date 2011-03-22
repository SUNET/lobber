# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 16:11:05 2011

@author: lundberg
"""

from django.core.management.base import BaseCommand, CommandError
from lobber.tracker.models import PeerInfo
from datetime import datetime, timedelta
import lobber.log
from lobber.settings import LOBBER_LOG_FILE
logger = lobber.log.Logger("tracker", LOBBER_LOG_FILE)


class Command(BaseCommand):
    args = '<time_out>'
    help = 'Deletes peers that has not been seen in <time_out> minutes.'
    
    def timed_out(self, pi, hours=0, minutes=0, seconds=0):
        '''
        Checks when a peer was last seen. Returns True if the peer has timed out
        and False if it is still valid.
        '''
        time_out = timedelta(hours=hours, minutes=minutes, seconds=seconds)
        if pi.last_seen < (datetime.now() - time_out):
            return True
        return False

    def handle(self, *args, **options):
        try:
            minutes = int(args[0])
        except Exception as e:
            raise CommandError(e)
        for pi in PeerInfo.objects.all():
            if self.timed_out(pi, minutes=minutes):
                #logger.debug('removing peer %s' % pi)
                pi.delete()