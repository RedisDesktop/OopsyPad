import click
import requests


@click.command()
@click.argument('address')
@click.argument('dump_path')
@click.argument('product')
@click.argument('version')
@click.argument('platform')
def upload_minidump(address, dump_path, product, version, platform):
    """
    \b
    ADDRESS
        OopsyPad host address.
    DUMP_PATH
        Minidump file path.
    PRODUCT
        Product name.
    VERSION
        Product version.
    PLATFORM
        Platform that the product is running on (Linux, MacOS, Windows).
    """
    send_minidump(address, dump_path, product, version, platform)


def send_minidump(address, dump_path, product, version, platform):
    with open(dump_path, 'rb') as f:
        data = {'product': product, 'version': version, 'platform': platform}
        files = {'upload_file_minidump': f}
        r = requests.post("{}/crash-report".format(address), data=data, files=files)
    return r
