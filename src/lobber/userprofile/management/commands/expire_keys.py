# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 17:17:05 2011

@author: lundberg
"""

from django.core.management.base import NoArgsCommand
from lobber.userprofile.models import UserProfile
import datetime
import lobber.log
from lobber.settings import LOBBER_LOG_FILE
logger = lobber.log.Logger("userprofile", LOBBER_LOG_FILE)

class Command(NoArgsCommand):
    help = 'Deletes keys that has expiration_data < now().'

    def handle(self, **options):
        q = UserProfile.objects.filter(expiration_date__lt=datetime.datetime.now())
        for p in q:
            u = p.user
            if u.username.startswith('key:'):
                #logger.debug('removing user profile %s and user %s' % (p, u))
                u.delete()
                p.delete()

