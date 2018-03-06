# OopsyPad 
[![Build Status](https://travis-ci.org/RedisDesktop/OopsyPad.svg?branch=master)](https://travis-ci.org/RedisDesktop/OopsyPad)

### Be aware of your apps' Oopsies.
OopsyPad is a Breakpad minidumps processing tool for [RedisDesktopManager](https://github.com/uglide/RedisDesktopManager).

## Requirements
- `Python 3`
- `MongoDB`
- `build-essential libcurl4-gnutls-dev pkg-config` for building breakpad deps

## Installation
```shell
git clone --recursive https://github.com/RedisDesktop/OopsyPad.git
cd OopsyPad/
./3rdparty/build.sh
pip install .
```
Install and run [`MongoDB`](https://docs.mongodb.com/manual/installation/).

## Usage

To run the server use `oopsy_run_server` command.
```shell
oopsy_run_server
```
Optionally you can specify `host`, `port` and `workers` (which by default are `127.0.0.1`, `8000` and `4` respectively) as well as any of other [gunicorn options](http://docs.gunicorn.org/en/stable/settings.html).
```shell
oopsy_run_server --host example.com --port 5050
```
After that run worker for minidump processing.
```shell
./run_celery_worker.sh
```
In case the file is not executable yet:
```shell
chmod +x run_celery_worker.sh
```

### OOPSY_HOST 
To use client shell commands you need to specify OOPSY_HOST environment variable which is OopsyPad host address.
```shell
export OOPSY_HOST=http://example.com
```

### Symbol files
Symbol files are necessary to decode minidump's binary data into human-readable stack trace.

To generate symbol file and send it to the server use `send_symfile` function __or__ `oopsy_send_symfile` command.
Here the required arguments are the `bin-path` to the product executable file, a `symfile-name` for the resulting symbol file, site host `address` where `oopsypad` is hosted and the `version` of the product.

`send_symfile` call example:
```python
from oopsypad.client.symfile import send_symfile
send_symfile(bin_path='/path/to/product/executable',
             symfile_name='rdm.sym',
             address='http://example.com',
             version='0.9')
```
`oopsy_send_symfile` command:
```shell
oopsy_send_symfile path/to/product/executable rdm.sym 0.9
```

### Projects
Before sending any dump files to the server you'll first need to send your project information including name, minimum allowed version `-v` and allowed platforms `-p` using `oopsy_admin project add` command, e.g.:
```shell
oopsy_admin project add rdm -v 0.9 -p Linux -p MacOS -p Windows
```
To delete unwanted project use `oopsy_admin project delete` command:
```shell
oopsy_admin project delete notrdm
```
To list all projects use:
```shell
oopsy_admin project list
```

### Minidumps processing
Send minidumps for processing by calling the `send_minidump` function as in example below 
__or__ with `oopsy_send_minidump` command 
__or__ by sending a POST request to the `/crash-report` endpoint with a `product` name, its `version` and a `platform` parameters and the minidump file specified as an `upload_file_minidump` parameter.

`send_minidump` function usage:
```python
from oopsypad.client.minidump import send_minidump
send_minidump(address='http://example.com',
              dump_path='/path/to/minidump',
              product='rdm',
              version='0.9',
              platform='Linux')
```
`oopsy_send_minidump` command:
```shell
oopsy_send_minidump /path/to/minidump rdm 0.9 Linux
```
POST request using `curl`:
```shell
curl -X POST \
     -F upload_file_minidump=@/path/to/minidump \
     -F product=rdm \
     -F version=0.9 \
     -F platform=Linux \
     http://example.com/crash-report
```

## Configuration
There are `prod` (default), `test` and `dev` environments available. To change configuration set environment variable `OOPSY_ENV`, e.g.:
```shell
export OOPSY_ENV=test
```
You may want to add some extra settings for OopsyPad.
To do so you should specify the path to your configuration file as `OOPSYPAD_SETTINGS` environment variable:
```shell
export OOPSYPAD_SETTINGS=/path/to/settings/file
```
