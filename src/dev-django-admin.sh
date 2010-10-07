#! /bin/sh

dir="$1"
if [ -d "$dir" ]; then
    shift
else
    dir=`pwd`
fi

DJANGO_SETTINGS_MODULE=lobber.settings; export DJANGO_SETTINGS_MODULE

env PYTHONPATH=${dir}:$PYTHONPATH django-admin $*
