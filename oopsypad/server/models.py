from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import hashlib
import hmac
import json
import os
import subprocess

from flask import current_app, url_for
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

    crash_location = fields.StringField()

    process_uptime = fields.IntField()

    crash_thread = fields.IntField()

    meta = {'ordering': ['-date_created'],
            'queryset_class': BaseQuerySet}

    @property
    def download_link(self):
        return url_for('crash-reports.download_minidump',
                       minidump_id=str(self.minidump.grid_id))

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

    def parse_process_uptime(self):
        line_start = 'Process uptime: '
        stacktrace_lines = self.stacktrace.split('\n')
        try:
            process_uptime_line = list(
                filter(lambda line: str.startswith(line, line_start),
                       stacktrace_lines))[0]
            raw_uptime = process_uptime_line.replace(line_start, '')

            if 'not available' not in raw_uptime.lower():
                if 'seconds' in raw_uptime:
                    uptime_seconds = int(raw_uptime.split()[0])
                else:
                    days, raw_hms = raw_uptime.split(' days ')
                    hms = datetime.strptime(raw_hms, '%H:%M:%S.%f')
                    uptime_seconds = timedelta(
                        days=int(days), hours=hms.hour, minutes=hms.minute,
                        seconds=hms.second).total_seconds()
                self.process_uptime = uptime_seconds
            self.save()
        except Exception as e:
            current_app.logger.exception(
                'Cannot parse process uptime: {}'.format(e))

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

            self.crash_reason = crash_info.get('type').split()[0]
            self.crash_address = crash_info.get('address')
            self.crash_thread = crash_info.get('crashing_thread')

            crashing_thread = self.stacktrace_json.get('crashing_thread')
            frame = crashing_thread.get('frames')[0]
            module = frame.get('module')
            module_offset = frame.get('module_offset')
            if module and module_offset:
                self.crash_location = '{} + {}'.format(module, module_offset)
            else:
                self.crash_location = self.crash_address
            self.save()

            self.parse_process_uptime()

            Issue.create_or_update_issue(product=self.product,
                                         version=self.version,
                                         platform=self.platform,
                                         reason=self.crash_reason,
                                         location=self.crash_location)
        except (subprocess.CalledProcessError, IndexError) as e:
            current_app.logger.exception(
                'Cannot parse stacktrace: {}'.format(e))

    def create_stacktrace(self):
        from oopsypad.server.worker import process_minidump
        process_minidump.delay(str(self.id))

    def remove_minidump(self):
        if self.file_path:
            if os.path.isfile(self.file_path):
                try:
                    os.remove(self.file_path)
                except OSError as e:
                    current_app.logger.exception(
                        'Cannot remove minidump: {}'.format(e))
        if self.minidump:
            self.minidump.delete()
            self.save()
        self.delete()

    def get_time(self):
        return self.date_created.strftime('%d-%m-%Y %H:%M')

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

    version = fields.StringField(required=True)

    platform = fields.StringField(required=True)

    symfile_name = fields.StringField(required=True)

    symfile_id = fields.StringField(required=True)

    symfile = fields.FileField(required=True)

    date_created = fields.DateTimeField()

    def save_symfile(self, symfile):
        try:
            self.symfile_name = secure_filename(symfile.filename)
            target_path = self.get_symfile_path()
            if not os.path.isdir(target_path):
                os.makedirs(target_path)
            symfile_path = os.path.join(target_path, self.symfile_name)
            symfile.save(symfile_path)
            with open(symfile_path, 'rb') as file:
                self.symfile.put(file,
                                 content_type='application/octet-stream',
                                 filename=self.symfile_name)
            self.save()
        except Exception as e:
            current_app.logger.exception(
                'Cannot save symfile: {}'.format(e))

    def get_symfile_path(self):
        if str(self.platform).lower() == "windows":
            product_name = "%s.pdb" % self.product
        else:
            product_name = self.product
        
        return os.path.join(SYMFILES_DIR, product_name, self.symfile_id)

    @classmethod
    def create_symfile(cls, product, version, platform, symfile_id, file):
        symfile = cls.objects(symfile_id=symfile_id).first()
        if not symfile:
            symfile = cls(product=product,
                          version=version,
                          platform=platform,
                          symfile_id=symfile_id,
                          date_created=datetime.now())
            symfile.save_symfile(file)
        return symfile

    def save(self, *args, **kwargs):
        if not self.date_created:
            self.date_created = datetime.now()
        return super().save(**kwargs)

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

    location = fields.StringField()

    total = fields.IntField(default=1)

    meta = {'ordering': ['-total']}

    @property
    def last_seen(self):
        minidump = self.get_minidumps().only('date_created').order_by(
            '-date_created').first()
        if minidump:
            return minidump.date_created

    @property
    def avg_uptime(self):
        minidumps = self.get_minidumps().filter(process_uptime__exists=True)
        if minidumps:
            return int(minidumps.average('process_uptime'))
        return 0

    def resolve_issue(self):
        minidumps = self.get_minidumps()
        for minidump in minidumps:
            minidump.remove_minidump()
        self.delete()

    def get_minidumps(self):
        minidumps = Minidump.objects(
            product=self.product,
            version=self.version,
            platform=self.platform,
            crash_reason=self.reason,
            crash_location=self.location
        )
        return minidumps

    @classmethod
    def create_or_update_issue(cls, product, version, platform, reason,
                               location):
        issue = cls.objects(product=product,
                            version=version,
                            platform=platform,
                            reason=reason,
                            location=location).first()
        if issue:
            issue.total += 1
        else:
            issue = cls(product=product,
                        version=version,
                        platform=platform,
                        reason=reason,
                        location=location)
        issue.save()
        return issue

    @classmethod
    def get_top_n_project_issues(cls, n, project_name):
        return cls.objects(product=project_name)[:n]

    def __str__(self):
        return 'Issue: {} {} {} {} {} {} {}'.format(
            self.product, self.version, self.platform, self.reason,
            self.location, self.total,
            self.last_seen.strftime('%d-%m-%Y %H:%M'))
