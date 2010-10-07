#! /bin/sh

dir="$1"
if [ -d "$dir" ]; then
    shift
else
    dir=`pwd`
fi

django-admin shell --settings=lobber.settings --pythonpath=${dir} $*
