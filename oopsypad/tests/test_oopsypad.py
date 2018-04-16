import unittest
from unittest import mock

from flask import url_for
from flask_testing import LiveServerTestCase
import pymongo
from selenium import webdriver

from oopsypad import server
from oopsypad.server import models
from oopsypad.server.app import create_app


HOST = '127.0.0.1'
LIVESERVER_PORT = 8000
TEST_APP = 'test_app'
TEST_APP_VERSION = '1.0.0'
TEST_PLATFORM = 'Linux'


def fake_create_stacktrace_worker(minidump):
    minidump = models.Minidump.get_by_id(minidump.id)
    minidump.get_stacktrace()
    minidump.parse_stacktrace()


class TestBase(LiveServerTestCase):
    def create_app(self):
        self.patch_celery_worker = mock.patch.object(
            server.models.Minidump, 'create_stacktrace',
            new=fake_create_stacktrace_worker)
        self.patch_celery_worker.start()
        app = create_app(config_name='test')
        app.config['LIVESERVER_PORT'] = LIVESERVER_PORT
        return app

    def drop_db(self):
        pymongo.MongoClient('mongodb://localhost:27017/').drop_database(
            self.app.config['MONGODB_SETTINGS']['DB'])

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.delete_all_cookies()
        self.browser.quit()
        if hasattr(self, 'patch_celery_worker'):
            self.patch_celery_worker.stop()
        self.drop_db()

    def click_element(self, element_id=None, element_xpath=None):
        if element_id:
            self.browser.find_element_by_id(element_id).click()
        if element_xpath:
            self.browser.find_element_by_xpath(element_xpath).click()

    def type_text(self, text, element_id=None, element_xpath=None):
        if element_id:
            self.browser.find_element_by_id(element_id).send_keys(text)
        if element_xpath:
            self.browser.find_element_by_xpath(element_xpath).send_keys(text)


class OopsyPadTest(TestBase):

    def test_issue_is_accessable_via_webui(self):
        # Login
        login_url = self.get_server_url() + url_for('security.login')
        self.browser.get(login_url)
        self.type_text('test@test.com', element_id='email')
        self.type_text('test', element_id='password')
        self.click_element(element_id='submit')

        # Get project overview page
        projects_url = self.get_server_url() + url_for('project.index_view')
        self.browser.get(projects_url)
        self.click_element(
            element_xpath='//a[contains(text(), "View Crash Report")]')

        # Check latest minidump info
        minidump = models.Minidump.get_last_n_project_minidumps(
            n=1, project_name=TEST_APP)[0]
        latest_dumps_table = self.browser.find_element_by_id(
            'latest-dumps-table')
        col_time = latest_dumps_table.find_element_by_class_name(
            'col-time').text
        col_platform = latest_dumps_table.find_element_by_class_name(
            'col-platform').text
        col_reason = latest_dumps_table.find_element_by_class_name(
            'col-reason').text

        self.assertEqual(
            col_time, minidump.get_time(),
            'Minidump time is {} (must be {}).'.format(
                col_time, minidump.get_time()))
        self.assertEqual(col_platform, TEST_PLATFORM,
                         'Minidump platform is {} (must be {}).'.format(
                             col_platform, TEST_PLATFORM))
        self.assertEqual(col_reason, minidump.crash_reason,
                         'Minidump crash reason is {} (must be {}).')

        # Check issue info
        issue = models.Issue.get_top_n_project_issues(
            n=1, project_name=TEST_APP)[0]
        issues_table = self.browser.find_element_by_id('issues-table')
        col_version = issues_table.find_element_by_class_name(
            'col-version').text
        col_platform = issues_table.find_element_by_class_name(
            'col-platform').text
        col_total = issues_table.find_element_by_class_name('col-total').text
        col_reason = issues_table.find_element_by_class_name('col-reason').text

        self.assertEqual(col_version, issue.version,
                         'Issue version is {} (must be {}).'.format(
                             col_version, issue.version))
        self.assertEqual(col_platform, issue.platform,
                         'Issue platform is {} (must be {}).'.format(
                             col_platform, issue.platform))
        self.assertEqual(int(col_total), issue.total,
                         'Issue total is {} (must be {})'.format(
                             col_total, issue.total))
        self.assertEqual(col_reason, issue.reason,
                         'Issue crash reason is {} (must be {}).')

        # Check issue page
        self.click_element(element_id='view-all-issues')
        self.click_element(element_xpath='//a[contains(text(), "View")]')

        # Issue details
        issue_details_table = self.browser.find_element_by_id(
            'issue-details-table')
        issue_platform = issue_details_table.find_element_by_id(
            'issue-platform').text
        issue_version = issue_details_table.find_element_by_id(
            'issue-version').text
        issue_reason = issue_details_table.find_element_by_id(
            'issue-reason').text

        self.assertEqual(issue_platform, issue.platform,
                         'Issue platform is {} (must be {}).'.format(
                             issue_platform, issue.platform))
        self.assertEqual(issue_version, issue.version,
                         'Issue version is {} (must be {}).'.format(
                             issue_version, issue.version))
        self.assertEqual(issue_reason, issue.reason,
                         'Issue reason is {} (must be {}).'.format(
                             issue_reason, issue.reason))

        # Issue stack traces
        stacktraces_table = self.browser.find_element_by_id(
            'stacktraces-table')
        col_time = stacktraces_table.find_element_by_class_name(
            'col-time').text
        stacktrace = stacktraces_table.find_element_by_class_name(
            'stacktrace').text

        self.assertEqual(
            col_time, minidump.get_time(),
            'Minidump time is {} (must be {}).'.format(
                col_time, minidump.get_time()))
        self.assertEqual(stacktrace, minidump.stacktrace.rstrip(),
                         'Stack trace doesn\'t match.')


if __name__ == '__main__':
    unittest.main()
