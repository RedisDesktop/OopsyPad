import base64
import json
import os
import unittest
from unittest.mock import patch

from ddt import ddt, data, unpack
from flask_testing import TestCase
import pymongo

from oopsypad.client.symfile import create_symfile
from oopsypad.server import config, demo, models
from oopsypad.server.app import create_app
from oopsypad.tests.utils import fake_create_stacktrace_worker

TEST_APP = 'test_app'
MIN_VERSION = '0.8'
LINUX = 'Linux'
ALLOWED_PLATFORMS = [LINUX, 'MacOS', 'Windows']


class TestBase(TestCase):

    def create_app(self):
        patch.object(models.Minidump, 'create_stacktrace',
                     new=fake_create_stacktrace_worker).start()
        app = create_app(config_name=config.TEST)
        return app

    def setUp(self):
        self.create_test_data()

    def tearDown(self):
        patch.stopall()
        self.drop_db()

    @staticmethod
    def drop_db():
        pymongo.MongoClient('mongodb://localhost:27017/').drop_database(
            config.TestConfig.MONGODB_SETTINGS.get('DB'))

    @staticmethod
    def create_test_data():
        for platform in ALLOWED_PLATFORMS:
            models.Platform.create_platform(name=platform)
        project = models.Project.create_project(name=TEST_APP)
        project.update(min_version=MIN_VERSION,
                       allowed_platforms=models.Platform.objects.all())


@ddt
class SymfileTest(TestBase):
    url = '/api/data/symfile/{product}/{id}'

    @data((demo.ADMIN_TOKEN, 201),
          (demo.DEV_TOKEN, 403),
          (demo.SYM_TOKEN, 201))
    @unpack
    def test_send_symfile(self, token, status_code):
        bin_path = os.path.join('tests', 'integration', 'test_app', 'bin',
                                'test_app')
        symfile_name = '{}.sym'.format(TEST_APP)
        symfile_path = create_symfile(bin_path=bin_path,
                                      symfile_name=symfile_name,
                                      symfile_root=config.Config.SYMFILES_DIR)
        with open(symfile_path, 'r') as f:
            _, platform, _, id, product = f.readline().split()
        with open(symfile_path, 'rb') as f:
            headers = {'Authorization': base64.b64encode(token.encode())}
            data = {'version': '0.9',
                    'platform': platform,
                    'symfile': f}
            url = self.url.format(product=product, id=id)
            response = self.client.post(url, data=data, headers=headers,
                                        content_type='multipart/form-data')

        self.assertEqual(response.status_code, status_code)
        if token != demo.DEV_TOKEN:
            print(response.json)
            self.assertEqual(response.json, {'ok': 'Symbol file was saved.'})


@ddt
class CrashReportTest(TestBase):
    url = '/crash-report'

    def send_crash_report_response(self, product, version, platform):

        minidump_path = os.path.join('oopsypad', 'tests', 'fixtures',
                                     'minidump.dmp')
        with open(minidump_path, 'rb') as f:
            data = {'product': product,
                    'version': version,
                    'platform': platform,
                    'upload_file_minidump': f}
            response = self.client.post(self.url, data=data,
                                        content_type='multipart/form-data')
        return response

    @data(
        (TEST_APP, '0.7', LINUX, 'bad version',
         {'error': 'You use an old version. Please download at least {} '
                   'release.'.format(MIN_VERSION)}),
        (TEST_APP, '0.9', 'What?', 'bad platform',
         {'error': 'What? platform is not allowed for {}.'.format(TEST_APP)}),
        ('fffuuuu', '0.9', LINUX, 'bad product',
         {'error': 'fffuuuu project not found.'})
    )
    @unpack
    def test_send_crash_report_validation(self, product, version, platform,
                                          fail_reason, error):
        response = self.send_crash_report_response(product, version, platform)
        print(response.json)

        self.assertEqual(response.status_code, 400,
                         'Minidump {} validation failed: {}'.format(
                             fail_reason, response.json))
        self.assertEqual(response.json, error, 'Wrong error.')

    def test_send_crash_report(self):
        product, version, platform = TEST_APP, '0.9', LINUX
        response = self.send_crash_report_response(product, version, platform)
        print(response.json)

        self.assertEqual(response.status_code, 201,
                         'Minidump send failed with {} code: {}'.format(
                             response.status_code,
                             response.json))
        self.assertEqual(response.json, {'ok': 'Thank you!'})

    def test_minidump_content(self):
        product, version, platform = TEST_APP, '0.9', 'Windows'
        response = self.send_crash_report_response(product, version, platform)
        print(response.json)

        minidump = models.Minidump.objects(product=product).first()
        print(minidump)

        self.assertEqual(minidump.product, product, 'Wrong product.')
        self.assertEqual(minidump.version, version, 'Wrong version.')
        self.assertEqual(minidump.platform, platform, 'Wrong platform.')
        self.assertEqual(minidump.crash_address, '0xfee1dead',
                         'Wrong crash address.')
        self.assertEqual(minidump.crash_reason, 'SIGSEGV',
                         'Wrong crash reason.')


@ddt
class TokenTest(TestBase):
    url = '/token'

    @data((demo.ADMIN_EMAIL, demo.ADMIN_TOKEN),
          (demo.DEV_EMAIL, demo.DEV_TOKEN),
          (demo.SYM_EMAIL, demo.SYM_TOKEN))
    @unpack
    def test_get_token(self, email, token):
        headers = {'Authorization':  'Basic ' + str(base64.b64encode(
            '{}:{}'.format(email, demo.PSW).encode()).decode())}
        response = self.client.get(self.url, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json.get('token'), token)


@ddt
class ProjectsTest(TestBase):

    @data((demo.ADMIN_TOKEN, 201),
          (demo.DEV_TOKEN, 403),
          (demo.SYM_TOKEN, 403))
    @unpack
    def test_project_add(self, token, status_code):
        url = '/api/projects/{name}'.format(name=TEST_APP)
        headers = {'content-type': 'application/json',
                   'Authorization': base64.b64encode(token.encode())}
        project_data = {'min_version': MIN_VERSION,
                        'allowed_platforms': ALLOWED_PLATFORMS}
        response = self.client.post(url, headers=headers,
                                    data=json.dumps(project_data))

        self.assertEqual(response.status_code, status_code)
        if token == demo.ADMIN_TOKEN:
            self.assertIsNotNone(response.json.get('ok'))

    @data((demo.ADMIN_TOKEN, 202),
          (demo.DEV_TOKEN, 403),
          (demo.SYM_TOKEN, 403))
    @unpack
    def test_project_delete(self, token, status_code):
        url = '/api/projects/{name}/delete'.format(name=TEST_APP)
        headers = {'Authorization': base64.b64encode(token.encode())}
        response = self.client.delete(url, headers=headers)

        self.assertEqual(response.status_code, status_code)
        if token == demo.ADMIN_TOKEN:
            self.assertIsNotNone(response.json.get('ok'))

    @data((demo.ADMIN_TOKEN, 200),
          (demo.DEV_TOKEN, 403),
          (demo.SYM_TOKEN, 403))
    @unpack
    def test_project_list(self, token, status_code):
        url = '/api/projects'
        headers = {'Authorization': base64.b64encode(token.encode())}
        response = self.client.get(url, headers=headers)

        self.assertEqual(response.status_code, status_code)
        if token == demo.ADMIN_TOKEN:
            self.assertIsNotNone(response.json.get('projects'))


if __name__ == '__main__':
    unittest.main()
