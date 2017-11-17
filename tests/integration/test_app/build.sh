#!/bin/bash

mkdir bin
qmake "DESTDIR=./bin/"
make -s -j 2

git clone https://github.com/RedisDesktop/CrashReporter.git
cd CrashReporter
qmake "DESTDIR=./../bin/" \
      'DEFINES+=APP_NAME=\\\"test_app\\\"' \
      'DEFINES+=CRASH_SERVER_URL=\\\"http://127.0.0.1:8080/crash-report\\\"' \
      'DEFINES+=APP_VERSION=\\\"1.0.0\\\"'
make -s -j 2
