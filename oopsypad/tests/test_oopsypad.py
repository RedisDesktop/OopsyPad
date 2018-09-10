import unittest
from unittest import mock

from flask import url_for
from flask_testing import LiveServerTestCase
import pymongo
import pytest
from selenium import webdriver

from oopsypad.server import config, demo, models
from oopsypad.server.app import create_app
from oopsypad.tests.utils import fake_create_stacktrace_worker

TEST_APP = 'test_app'
TEST_APP_VERSION = '1.0.0'
TEST_PLATFORM = 'Linux'


class TestBase(LiveServerTestCase):
    def create_app(self):
        mock.patch.object(models.Minidump, 'create_stacktrace',
                          new=fake_create_stacktrace_worker).start()
        app = create_app(config_name=config.TEST)
        return app

    @staticmethod
    def drop_db():
        pymongo.MongoClient('mongodb://localhost:27017/').drop_database(
            config.TestConfig.MONGODB_SETTINGS.get('DB'))

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.delete_all_cookies()
        self.browser.quit()
        mock.patch.stopall()
        self.drop_db()

    def get_element(self, parent=None,
                    element_id=None, element_class=None, element_xpath=None):
        if not parent:
            parent = self.browser
        if element_id:
            return parent.find_element_by_id(element_id)
        if element_class:
            return parent.find_element_by_class_name(element_class)
        if element_xpath:
            return parent.find_element_by_xpath(element_xpath)

    def get_element_text(self, parent, element_id=None, element_class=None):
        if element_id:
            return self.get_element(parent=parent,
                                    element_id=element_id).text
        if element_class:
            return self.get_element(parent=parent,
                                    element_class=element_class).text

    def click_element(self, element_id=None, element_xpath=None):
        if element_id:
            self.get_element(element_id=element_id).click()
        if element_xpath:
            self.get_element(element_xpath=element_xpath).click()

    def type_text(self, text, element_id=None, element_xpath=None):
        if element_id:
            self.get_element(element_id=element_id).send_keys(text)
        if element_xpath:
            self.get_element(element_xpath=element_xpath).send_keys(text)


@pytest.mark.first
class OopsyPadTest(TestBase):

    def test_issue_is_accessible_via_web_ui(self):
        # Login
        login_url = '{}{}'.format(self.get_server_url(),
                                  url_for('security.login'))
        self.browser.get(login_url)
        self.type_text('admin@test.com', element_id='email')
        self.type_text(demo.PSW, element_id='password')
        self.click_element(element_id='submit')

        # Get project overview page
        projects_url = '{}{}'.format(self.get_server_url(),
                                     url_for('project.index_view'))
        self.browser.get(projects_url)
        self.click_element(
            element_xpath='//a[contains(text(), "Details")]')

        # Check latest minidump info
        minidump = models.Minidump.get_last_n_project_minidumps(
            n=1, project_name=TEST_APP)[0]

        latest_dumps_table = self.get_element(element_id='latest-dumps-table')
        col_time = self.get_element_text(parent=latest_dumps_table,
                                         element_class='col-time')
        col_platform = self.get_element_text(parent=latest_dumps_table,
                                             element_class='col-platform')
        col_reason = self.get_element_text(parent=latest_dumps_table,
                                           element_class='col-reason')

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
        issue = models.Issue.get_top_n_project_issues(n=1,
                                                      project_name=TEST_APP)[0]
        issues_table = self.get_element(element_id='issues-table')
        col_version = self.get_element_text(parent=issues_table,
                                            element_class='col-version')
        col_platform = self.get_element_text(parent=issues_table,
                                             element_class='col-platform')
        col_total = self.get_element_text(parent=issues_table,
                                          element_class='col-total')
        col_reason = self.get_element_text(parent=issues_table,
                                           element_class='col-reason')

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
        issue_details_table = self.get_element(
            element_id='issue-details-table')
        issue_platform = self.get_element_text(parent=issue_details_table,
                                               element_id='issue-platform')
        issue_version = self.get_element_text(parent=issue_details_table,
                                              element_id='issue-version')
        issue_reason = self.get_element_text(parent=issue_details_table,
                                             element_id='issue-reason')

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
        stacktraces_table = self.get_element(element_id='stacktraces-table')
        col_time = self.get_element_text(parent=stacktraces_table,
                                         element_class='col-time')
        stacktrace = self.get_element_text(parent=stacktraces_table,
                                           element_class='stacktrace')

        self.assertEqual(col_time, minidump.get_time(),
                         'Minidump time is {} (must be {}).'.format(
                             col_time, minidump.get_time()))
        self.assertEqual(stacktrace, minidump.stacktrace.rstrip(),
                         'Stack trace doesn\'t match.')


if __name__ == '__main__':
    unittest.main()
