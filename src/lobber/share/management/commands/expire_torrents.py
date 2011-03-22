# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 17:14:05 2011

@author: lundberg
"""

from django.core.management.base import NoArgsCommand
from lobber.share.models import Torrent
import datetime
import lobber.log
from lobber.settings import LOBBER_LOG_FILE
logger = lobber.log.Logger("share", LOBBER_LOG_FILE)

class Command(NoArgsCommand):
    help = 'Deletes torrents that has expiration_data < now().'

    def handle(self, **options):
        q = Torrent.objects.filter(expiration_date__lt=datetime.datetime.now())
        for t in q:
            #logger.debug('removing torrent %s' % t)
            t.remove()
