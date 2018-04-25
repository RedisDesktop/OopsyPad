from datetime import datetime
from dateutil.relativedelta import relativedelta
import hashlib
import hmac
import json
import os
import subprocess

from flask import current_app
from flask_mongoengine import MongoEngine, BaseQuerySet
from flask_security import UserMixin, RoleMixin
import mongoengine as mongo
from mongoengine import fields
from mongoengine.queryset.visitor import Q
from werkzeug.utils import secure_filename

from oopsypad.server.config import Config
from oopsypad.server.helpers import last_12_months

DUMPS_DIR = Config.DUMPS_DIR
SYMFILES_DIR = Config.SYMFILES_DIR

db = MongoEngine()


class Role(mongo.Document, RoleMixin):
    name = mongo.StringField(max_length=80, unique=True)

    description = mongo.StringField(max_length=255)

    def __str__(self):
        return self.name


class User(mongo.Document, UserMixin):
    email = mongo.StringField(unique=True, required=True)

    password = mongo.StringField(required=True)

    active = mongo.BooleanField(default=False)

    confirmed_at = mongo.DateTimeField()

    roles = mongo.ListField(mongo.ReferenceField(Role), default=[])

    auth_token = mongo.StringField()

    def save(self, *args, **kwargs):
        if not self.roles:
            if User.objects.count() == 0:
                self.roles = [Role.objects(name='admin').first()]
            else:
                self.roles = [Role.objects(name='developer').first()]
        if not self.auth_token:
            with current_app.app_context():
                self.auth_token = hmac.new(
                    current_app.config['SECRET_KEY'].encode('utf8'),
                    str(self.id).encode('utf8'),
                    hashlib.sha512
                ).hexdigest()

        return super().save(**kwargs)


class Minidump(mongo.Document):
    product = fields.StringField()  # Crashed application name

    version = fields.StringField()  # Crashed application version

    platform = fields.StringField()  # OS name

    filename = fields.StringField()

    minidump = fields.FileField()  # Google Breakpad minidump

    file_path = fields.StringField()

    stacktrace = fields.StringField()

    stacktrace_json = fields.DictField()

    date_created = fields.DateTimeField()

    crash_reason = fields.StringField()

    crash_address = fields.StringField()

    crash_thread = fields.IntField()

    meta = {'ordering': ['-date_created'],
            'queryset_class': BaseQuerySet}

    def save_minidump_file(self, minidump_file):
        if not os.path.isdir(DUMPS_DIR):
            os.makedirs(DUMPS_DIR)
        try:
            self.filename = secure_filename(minidump_file.filename)
            target_path = self.get_target_minidump_path()
            minidump_file.save(target_path)
            with open(target_path, 'rb') as minidump:
                if self.minidump:
                    self.minidump.replace(minidump)
                else:
                    self.minidump.put(minidump)
            self.file_path = target_path
            self.save()
        except Exception as e:
            current_app.logger.exception(
                'Cannot save minidump file: {}'.format(e))

    def get_target_minidump_path(self):
        return os.path.join(DUMPS_DIR, self.filename)

    def get_stacktrace(self):
        minidump_path = self.file_path
        try:
            minidump_stackwalk_output = subprocess.check_output(
                [Config.MINIDUMP_STACKWALK, minidump_path, SYMFILES_DIR],
                stderr=subprocess.DEVNULL)
            self.stacktrace = minidump_stackwalk_output.decode()
            self.save()
        except subprocess.CalledProcessError as e:
            current_app.logger.exception(
                'Cannot get stacktrace: {}'.format(e))

    def parse_stacktrace(self):
        minidump_path = self.file_path
        try:
            stackwalker_output = subprocess.check_output(
                [Config.STACKWALKER, '--pretty', minidump_path, SYMFILES_DIR],
                stderr=subprocess.DEVNULL)

            self.stacktrace_json = json.loads(stackwalker_output.decode())
            crash_info = self.stacktrace_json.get('crash_info')
            if not crash_info:
                current_app.logger.error(
                    'Cannot parse stacktrace: No crash info provided.')
                return
            self.crash_reason = crash_info.get('type')
            self.crash_address = crash_info.get('address')
            self.crash_thread = crash_info.get('crashing_thread')
            self.save()

            Issue.create_or_update_issue(product=self.product,
                                         version=self.version,
                                         platform=self.platform,
                                         reason=self.crash_reason)
        except subprocess.CalledProcessError as e:
            current_app.logger.exception(
                'Cannot parse stacktrace: {}'.format(e))

    def create_stacktrace(self):
        from oopsypad.server.worker import process_minidump
        process_minidump.delay(str(self.id))

    def get_time(self):
        return self.date_created.strftime('%d.%m.%Y %H:%M')

    @classmethod
    def get_by_id(cls, minidump_id):
        return cls.objects(id=minidump_id).first()

    @classmethod
    def create_minidump(cls, product, version, platform, minidump_file):
        minidump = cls(product=product,
                       version=version,
                       platform=platform,
                       date_created=datetime.now())

        minidump.save_minidump_file(minidump_file)
        minidump.create_stacktrace()
        return minidump

    @classmethod
    def get_last_12_months_minidumps_counts(cls, queryset):
        today = datetime.today().replace(day=1)
        counts = []
        for months in last_12_months():
            months_ago = today - relativedelta(months=months)
            one_more_months_ago = today - relativedelta(months=months - 1)
            months_ago_minidumps_count = queryset.filter(
                Q(date_created__lte=one_more_months_ago)
                & Q(date_created__gte=months_ago)).count()
            counts.append(months_ago_minidumps_count)
        return counts

    @classmethod
    def get_versions_per_product(cls, product):
        return sorted(list(set([i.version
                                for i in cls.objects(product=product)])))

    @classmethod
    def get_last_n_project_minidumps(cls, n, project_name):
        project_minidumps = cls.objects(product=project_name)
        return project_minidumps[:n]

    def __str__(self):
        return 'Minidump: {} {} {} {}'.format(self.product,
                                              self.version,
                                              self.platform,
                                              self.filename)


class Symfile(mongo.Document):
    product = fields.StringField()

    version = fields.StringField()

    platform = fields.StringField()

    symfile_name = fields.StringField()

    symfile_id = fields.StringField()

    symfile = fields.FileField()

    date_created = fields.DateTimeField()

    def save_symfile(self, symfile):
        try:
            self.symfile_name = secure_filename(symfile.filename)
            target_path = self.get_symfile_path()
            if not os.path.isdir(target_path):
                os.makedirs(target_path)
            symfile.save(os.path.join(target_path, self.symfile_name))
            self.save()
        except Exception as e:
            current_app.logger.exception(
                'Cannot save symfile: {}'.format(e))

    def get_symfile_path(self):
        return os.path.join(SYMFILES_DIR, self.product, self.symfile_id)

    @classmethod
    def create_symfile(cls, product, version, platform, symfile_id, file):
        symfile = cls.objects(symfile_id=symfile_id).first()
        if not symfile:
            symfile = cls(product=product,
                          symfile_id=symfile_id,
                          version=version,
                          platform=platform,
                          date_created=datetime.now())
            symfile.save_symfile(file)
        return symfile

    def __str__(self):
        return 'Symfile: {} {} {} {}'.format(self.product,
                                             self.version,
                                             self.platform,
                                             self.symfile_id)


class Platform(mongo.Document):
    name = fields.StringField(required=True, unique=True)

    @classmethod
    def create_platform(cls, name):
        platform = Platform.objects(name=name).first()
        if not platform:
            platform = cls(name=name)
            platform.save()
        return platform

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Project(mongo.Document):
    name = fields.StringField(required=True, unique=True)

    min_version = fields.StringField()

    allowed_platforms = fields.ListField(fields.ReferenceField(Platform))

    def get_allowed_platforms(self):
        return [i.name for i in self.allowed_platforms]

    def update_min_version(self, version):
        self.min_version = version
        self.save()

    def add_allowed_platform(self, platform):
        if platform not in self.allowed_platforms:
            self.allowed_platforms.append(platform)
            self.save()

    @classmethod
    def create_project(cls, name):
        project = cls.objects(name=name).first()
        if not project:
            project = cls(name=name)
            project.save()
        return project

    def get_project_dict(self):
        return {'name': self.name,
                'min_version': self.min_version,
                'allowed_platforms': [p.name for p in self.allowed_platforms]}

    def __str__(self):
        return 'Name: {} \n' \
               'Minimum allowed version: {}\n' \
               'Allowed Platforms: {}'.format(
                self.name,
                self.min_version if self.min_version else '~no min version',
                ', '.join([p.name for p in self.allowed_platforms])
                if self.allowed_platforms else '~no allowed platforms')


class Issue(mongo.Document):
    product = fields.StringField()

    version = fields.StringField()

    platform = fields.StringField()

    reason = fields.StringField()

    total = fields.IntField(default=1)

    meta = {'ordering': ['-total']}

    @classmethod
    def create_or_update_issue(cls, product, version, platform, reason):
        issue = cls.objects(product=product,
                            version=version,
                            platform=platform,
                            reason=reason).first()
        if issue:
            issue.total += 1
        else:
            issue = cls(product=product,
                        version=version,
                        platform=platform,
                        reason=reason)
        issue.save()
        return issue

    @classmethod
    def get_top_n_project_issues(cls, n, project_name):
        return cls.objects(product=project_name)[:n]

    def __str__(self):
        return 'Issue: {} {} {} {} {}'.format(self.product,
                                              self.version,
                                              self.platform,
                                              self.reason,
                                              self.total)
