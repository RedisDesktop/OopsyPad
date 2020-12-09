#!/bin/sh
set -e

export LC_ALL=en_US.utf-8
export LANG=en_US.utf-8

# oopsy_celery_worker run
oopsy_run_server --host 0.0.0.0 --port 8000
# oopsy_celery_worker stop