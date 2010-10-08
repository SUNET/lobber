#! /bin/sh

# Expire torrents and key users which have passed their best date.

# BUGS:
# - Must be run from lobber/src (with argument '.' or `pwd`) when
# database is mysqlite.
# - settings.BASE_DIR must contain an absolute path when database is
# mysqlite, or removing User objects will fail with 'OperationalError:
# no such table: share_datalocation'

usage() {
    echo "usage: `basename $0`: base_dir"
    exit 1
}

base_dir="$1"; [ -d "$base_dir" ] || usage
shift
${base_dir}/dev-django-admin.sh ${base_dir} shell < ${base_dir}/scripts/expire.py
