# OopsyPad 
[![Build Status](https://travis-ci.org/RedisDesktop/OopsyPad.svg?branch=master)](https://travis-ci.org/RedisDesktop/OopsyPad)

### Be aware of your apps' Oopsies.
OopsyPad is a Breakpad minidumps processing tool for [RedisDesktopManager](https://github.com/uglide/RedisDesktopManager).

## Requirements
### Server:
- `Python 3`
- `MongoDB`
- `redis-server` (Celery backend)
- `build-essential libcurl4-gnutls-dev pkg-config` for building breakpad deps
### Client:
- `Python 3`
- OSX: `Xcode`
- Ubuntu: `build-essential libcurl4-gnutls-dev pkg-config`

## Server
### Installation
```shell
git clone --recursive https://github.com/kdeyev/OopsyPad.git
cd OopsyPad/
./3rdparty/build.sh
pip install .
```
Install and run [`MongoDB`](https://docs.mongodb.com/manual/installation/).

> __Note__: In case of using virtualenv keep it inside of the repository directory so the server could access 3rd party binaries.

### Usage

To run the server use `oopsy_run_server` command.
```shell
oopsy_run_server
```
Optionally you can specify `host`, `port` and `workers` (which by default are `127.0.0.1`, `8000` and `4` respectively) as well as any of other [gunicorn options](http://docs.gunicorn.org/en/stable/settings.html).
```shell
oopsy_run_server --host example.com --port 5050
```
After that run Celery worker for minidump processing:
```shell
oopsy_celery_worker run
```
> Restart the worker using the command above each time the server is restarted.

To stop the worker use:
```shell
oopsy_celery_worker stop
```
To show log file contents use:
```shell
oopsy_celery_worker logs
```
For example to show last 10 log entries use `-n` option:
```shell
oopsy_celery_worker logs -n 10
```

### Configuration
There are `prod` (default), `test` and `dev` environments available. To change OopsyPad environment set environment variable `OOPSY_ENV`, e.g.:
```shell
export OOPSY_ENV=test
```
You may want to add some extra settings for OopsyPad.
To do so you should specify the path to your configuration file in `OOPSYPAD_SETTINGS` environment variable:
```shell
export OOPSYPAD_SETTINGS=/path/to/settings/file
```
#### Sentry
To enable Sentry (already enabled for `prod`) you should set `ENABLE_SENTRY = True` and specify `SENTRY_DSN` in your custom configuration file or set `SENTRY_DSN` environment variable.

## Client

### OOPSY_HOST 
To use client shell commands you should specify `OOPSY_HOST` environment variable which is OopsyPad host address.
```shell
export OOPSY_HOST=http://example.com
```

### CLI Authentication
To send symbol files and manage projects with command line you should obtain an authentication token by providing your OopsyPad credentials (email and password) to `oopsy_admin login`. In case if credentials are valid the token will be stored in `~/.oopsy` configuration file.

### Symbol files
> Symbol files are necessary to decode minidump's binary data into human-readable stack trace.

To generate a symbol file use `oopsy_symfile create` command:
```shell
oopsy_symfile create path/to/product/executable rdm.sym
```
Required arguments are:
- `bin-path` - the path to the product executable file
- `symfile-name` - the name for the resulting symbol file

The output will be the path to the generated symbol file which should be used in `oopsy_symfile send` command.
```shell
export SYMFILE_PATH=`oopsy_symfile create path/to/product/executable rdm.sym`
```

To send generated symbol file to the server use `oopsy_symfile send` command:
```shell
oopsy_symfile send $SYMFILE_PATH 0.9
```
Required arguments are:
- `symfile-path` - the path to the resulting symbol file
- `version` of the product

> Symbol file contains a product name and a platform info so there's no need to include them in the command.

### Projects
Before sending any dump files to the server you should send your project information including name, minimum allowed version `-v` and allowed platforms `-p` using `oopsy_admin project add` command:
```shell
oopsy_admin project add rdm -v 0.9 -p Linux -p MacOS -p Windows
```
To delete unwanted project use `oopsy_admin project delete` command:
```shell
oopsy_admin project delete rdm
```
To list all projects use:
```shell
oopsy_admin project list
```

### Minidumps processing
To send minidumps for processing use `oopsy_crash_report` command:
```shell
oopsy_crash_report /path/to/minidump rdm 0.9 Linux
```
Or send a POST request to the `/crash-report` endpoint.
POST request using `curl`:
```shell
curl -X POST \
     -F product=rdm \
     -F version=0.9 \
     -F platform=Linux \
     -F upload_file_minidump=@/path/to/minidump \
     http://example.com/crash-report
```
Required arguments are:
- `product` - product name
- `version` - product version
- `platform` - platform where the crash has occurred
- `upload_file_minidump` - path to the minidump file
