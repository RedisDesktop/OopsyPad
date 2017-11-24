import click
import requests


@click.command(name='oopsy_send_minidump')
@click.argument('address')
@click.argument('dump-path')
@click.argument('product')
@click.argument('version')
@click.argument('platform')
def oopsy_send_minidump(address, dump_path, product, version, platform):
    """
    \b
    ADDRESS
        OopsyPad host address.
    DUMP-PATH
        Minidump file path.
    PRODUCT
        Product name.
    VERSION
        Product version.
    PLATFORM
        Platform that the product is running on (Linux, MacOS, Windows).
    """
    response = send_minidump(address, dump_path, product, version, platform)
    print(response.text)


def send_minidump(address, dump_path, product, version, platform):
    with open(dump_path, 'rb') as f:
        data = {'product': product, 'version': version, 'platform': platform}
        files = {'upload_file_minidump': f}
        r = requests.post("{}/crash-report".format(address), data=data, files=files)
    return r
