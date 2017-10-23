# OopsyPad

## Be aware of your apps' Oopsies.
OopsyPad is a Breakpad minidumps processing tool for [RedisDesktopManager](https://github.com/uglide/RedisDesktopManager).
## Requirements
- `Python 3`
## Installation
```shell
pip install oopsypad
```

## Usage
### Symbol files
Symbol files are necessary to decode minidump's binary data into human-readable stack trace.

To generate symbol file and send it to the server use `send_symfile` function.
Here the required arguments are the `path` to the product executable file, a `name` for the resulting symbol file, site host `address` where `oopsypad` is hosted and the `version` of the product.
Calling `send_symfile`:
```python
from oopsypad.client.symfile import send_symfile
send_symfile(path='path/to/product/executable',
             name='rdm.sym',
             address='http://example.com',
             version='0.9')
```
Or the same thing for command line:
```shell
python3 symfile.py --path path/to/product/executable --name rdm.sym --address http://example.com --version 0.9
```
### Minidumps processing
Send minidumps for processing by calling the `send_minidump` function as in example below or by sending a POST request to the `/crash-report` endpoint with the minidump file specified as an `upload_file_minidump` parameter as well as a `product` name, its `version` and a `platform`.

Example of using the `send_minidump` function:
```python
from oopsypad.client.minidump import send_minidump
send_minidump(address='http://example.com',
              dump_path='/path/to/minidump',
              product='rdm',
              version='0.9',
              platform='Linux')
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
