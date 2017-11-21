#!/usr/bin/env bash

celery -D -A oopsypad.server.worker.celery worker -f celery.log
