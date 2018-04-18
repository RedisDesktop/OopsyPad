import base64
import os
import unittest
from unittest.mock import patch

from ddt import ddt, data, unpack
from flask import url_for
from flask_testing import LiveServerTestCase
import pymongo
import requests

from oopsypad.client.admin import save_token
from oopsypad.client.symfile import send_symfile
from oopsypad.client.minidump import send_crash_report
from oopsypad.server import config, demo, models
from oopsypad.server.app import create_app
from oopsypad.tests.utils import fake_create_stacktrace_worker

TEST_APP = 'test_app'
MIN_VERSION = '0.8'
LINUX = 'Linux'
ALLOWED_PLATFORMS = [LINUX, 'MacOS', 'Windows']


class TestBase(LiveServerTestCase):

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
    @data((demo.ADMIN_TOKEN, 201),
          (demo.DEV_TOKEN, 403),
          (demo.SYM_TOKEN, 201))
    @unpack
    def test_send_symfile(self, token, status_code):
        save_token(token)
        response = send_symfile(
            bin_path=os.path.join(config.Config.ROOT_DIR, 
                                  'tests', 'integration', 'test_app', 'bin', 
                                  'test_app'),
            symfile_name='{}.sym'.format(TEST_APP),
            address=self.get_server_url(),
            version='0.9')
        self.assertEqual(response.status_code, status_code)
        if token != demo.DEV_TOKEN:
            print(response.json())
            self.assertEqual(response.json(), {'ok': 'Symbol file was saved.'})


@ddt
class CrashReportTest(TestBase):

    def send_crash_report_response(self, product, version, platform):

        minidump_path = os.path.join(config.Config.ROOT_DIR, 'oopsypad',
                                     'tests', 'fixtures', 'minidump.dmp')
        response = send_crash_report(address=self.get_server_url(),
                                     dump_path=minidump_path,
                                     product=product,
                                     version=version,
                                     platform=platform)
        return response

    @data(
        (TEST_APP, '0.7', LINUX, 'bad version',
         {'error': 'You use an old version. Please download at least {} '
                   'release.'.format(MIN_VERSION)}),
        (TEST_APP, '0.9', 'What?', 'bad platform',
         {'error': 'What? platform is not allowed for {}.'.format(TEST_APP)}),
        ('fffuuuu', '0.9', LINUX, 'bad product',
         {'error': 'fffuuuu project does not exist.'})
    )
    @unpack
    def test_send_crash_report_validation(self, product, version, platform,
                                          fail_reason, error):
        response = self.send_crash_report_response(product, version, platform)
        print(response.json())

        self.assertEqual(response.status_code, 400,
                         'Minidump {} validation failed: {}'.format(
                             fail_reason, response.json()))
        self.assertEqual(response.json(), error, 'Wrong error.')

    def test_send_crash_report(self):
        product, version, platform = TEST_APP, '0.9', LINUX
        response = self.send_crash_report_response(product, version, platform)
        print(response.json())

        self.assertEqual(response.status_code, 201,
                         'Minidump send failed with {} code: {}'.format(
                             response.status_code,
                             response.json()))
        self.assertEqual(response.json(), {'ok': 'Thank you!'})

    def test_minidump_content(self):
        product, version, platform = TEST_APP, '0.9', 'Windows'
        response = self.send_crash_report_response(product, version, platform)
        print(response.json())

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
    @data((demo.ADMIN_EMAIL, demo.ADMIN_TOKEN),
          (demo.DEV_EMAIL, demo.DEV_TOKEN),
          (demo.SYM_EMAIL, demo.SYM_TOKEN))
    @unpack
    def test_get_token(self, email, token):
        url = '{}{}'.format(self.get_server_url(),
                            url_for('oopsypad.get_auth_token'))
        response = requests.get(url, auth=(email, demo.PSW))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('token'), token)


@ddt
class ProjectsTest(TestBase):
    @data((demo.ADMIN_TOKEN, 201),
          (demo.DEV_TOKEN, 403),
          (demo.SYM_TOKEN, 403))
    @unpack
    def test_project_add(self, token, status_code):
        headers = {'Authorization': base64.b64encode(token.encode())}
        url = '{}{}'.format(self.get_server_url(),
                            url_for('oopsypad_api.add_project', name=TEST_APP))
        response = requests.post(url, headers=headers,
                                 json={'min_version': MIN_VERSION,
                                       'allowed_platforms': ALLOWED_PLATFORMS})
        self.assertEqual(response.status_code, status_code)
        if token == demo.ADMIN_TOKEN:
            self.assertIsNotNone(response.json().get('ok'))

    @data((demo.ADMIN_TOKEN, 202),
          (demo.DEV_TOKEN, 403),
          (demo.SYM_TOKEN, 403))
    @unpack
    def test_project_delete(self, token, status_code):
        headers = {'Authorization': base64.b64encode(token.encode())}
        url = '{}{}'.format(self.get_server_url(),
                            url_for('oopsypad_api.delete_project',
                                    name=TEST_APP))
        response = requests.delete(url, headers=headers,
                                   json={'min_version': MIN_VERSION,
                                         'allowed_platforms':
                                             ALLOWED_PLATFORMS})
        self.assertEqual(response.status_code, status_code)
        if token == demo.ADMIN_TOKEN:
            self.assertIsNotNone(response.json().get('ok'))

    @data((demo.ADMIN_TOKEN, 200),
          (demo.DEV_TOKEN, 403),
          (demo.SYM_TOKEN, 403))
    @unpack
    def test_project_list(self, token, status_code):
        headers = {'Authorization': base64.b64encode(token.encode())}
        url = '{}{}'.format(self.get_server_url(),
                            url_for('oopsypad_api.list_projects'))
        response = requests.get(url, headers=headers,
                                json={'min_version': MIN_VERSION,
                                      'allowed_platforms': ALLOWED_PLATFORMS})
        self.assertEqual(response.status_code, status_code)
        if token == demo.ADMIN_TOKEN:
            self.assertIsNotNone(response.json().get('projects'))


if __name__ == '__main__':
    unittest.main()
