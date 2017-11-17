#!/usr/bin/env bash

celery -D -A oopsypad.server.worker._celery worker
