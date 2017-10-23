import requests


def send_minidump(address, dump_path, product, version, platform):
    with open(dump_path, 'rb') as f:
        data = {'product': product, 'version': version, 'platform': platform}
        files = {'upload_file_minidump': f}
        r = requests.post("{}/crash-report".format(address), data=data, files=files)
    return r
