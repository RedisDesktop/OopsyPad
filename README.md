# OopsyPad

## Be aware of your apps' Oopsies.
OopsyPad is a Breakpad minidumps processing tool for [RedisDesktopManager](https://github.com/uglide/RedisDesktopManager).

## Requirements
- `Python 3`

## Installation
```shell
git clone --recursive https://github.com/RedisDesktop/OopsyPad.git
cd OopsyPad/
./3rdparty/build.sh
pip install .
```

## Usage
To run the server use `oopsy_run_server` command.
```shell
oopsy_run_server
```
Optionally you can specify `host` and `port` which by default are `127.0.0.1` and `5000` respectively.
```shell
oopsy_run_server --host example.com --port 5050
```
After that run worker for minidump processing.
```shell
celery -A oopsypad.server.worker._celery worker
```

### Symbol files
Symbol files are necessary to decode minidump's binary data into human-readable stack trace.

To generate symbol file and send it to the server use `send_symfile` function __or__ `oopsy_send_symfile` command.
Here the required arguments are the `path` to the product executable file, a `name` for the resulting symbol file, site host `address` where `oopsypad` is hosted and the `version` of the product.
Calling `send_symfile`:
```python
from oopsypad.client.symfile import send_symfile
send_symfile(path='/path/to/product/executable',
             name='rdm.sym',
             address='http://example.com',
             version='0.9')
```
Or the same thing for command line:
```shell
oopsy_send_symfile path/to/product/executable rdm.sym http://example.com 0.9
```

### Minidumps processing
Send minidumps for processing by calling the `send_minidump` function as in example below __or__ with `oopsy_send_minidump` command __or__ by sending a POST request to the `/crash-report` endpoint with the minidump file specified as an `upload_file_minidump` parameter as well as a `product` name, its `version` and a `platform`.

Example of using the `send_minidump` function:
```python
from oopsypad.client.minidump import send_minidump
send_minidump(address='http://example.com',
              dump_path='/path/to/minidump',
              product='rdm',
              version='0.9',
              platform='Linux')
```
Using command line:
```shell
oopsy_send_minidump http://example.com /path/to/minidump rdm 0.9 Linux
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
You may want to add some extra settings for OopsyPad.
To do so you should specify the path to your configuration file as `OOPSYPAD_SETTINGS` environment variable:
```shell
export OOPSYPAD_SETTINGS=/path/to/settings/file
```
