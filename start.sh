#!/bin/sh
set -e

oopsy_celery_worker run
oopsy_run_server --host 0.0.0.0 --port 8000
oopsy_celery_worker stop