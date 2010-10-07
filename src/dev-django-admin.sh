#! /bin/sh

django-admin shell --settings=lobber.settings --pythonpath=`pwd` $*
