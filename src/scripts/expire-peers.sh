#! /bin/sh

usage() {
    echo "usage: `basename $0`: base_dir"
    exit 1
}

base_dir="$1"; [ -d "$base_dir" ] || usage
shift
${base_dir}/dev-django-admin.sh ${base_dir} shell \
    < ${base_dir}/scripts/expire-peers.py
