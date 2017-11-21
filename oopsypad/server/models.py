from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask_mongoengine import BaseQuerySet
import json
import mongoengine as mongo
from mongoengine import fields
from mongoengine.queryset.visitor import Q
import os
import subprocess
from werkzeug.utils import secure_filename

from oopsypad.server.config import Config, CWD
from oopsypad.server.helpers import last_12_months

DUMPS_DIR = Config.DUMPS_DIR
SYMFILES_DIR = Config.SYMFILES_DIR
STACKWALKER = os.path.join(CWD, '../../3rdparty/minidump-stackwalk/stackwalker')


class Minidump(mongo.Document):
    product = fields.StringField()  # Crashed application name
    version = fields.StringField()  # Crashed application version
    platform = fields.StringField()  # OS name
    filename = fields.StringField()
    minidump = fields.FileField()  # Google Breakpad minidump (upload_file_minidump)
    stacktrace = fields.StringField()
    stacktrace_json = fields.DictField()
    date_created = fields.DateTimeField()
    crash_reason = fields.StringField()
    crash_address = fields.StringField()
    crash_thread = fields.IntField()
    meta = {'ordering': ['-date_created'],
            'queryset_class': BaseQuerySet}

    def save_minidump(self, request):
        if not os.path.isdir(DUMPS_DIR):
            os.makedirs(DUMPS_DIR)
        try:
            file = request.files['upload_file_minidump']
            self.filename = secure_filename(file.filename)
            target_path = self.get_minidump_path()
            file.save(target_path)
            with open(target_path, 'rb') as minidump:
                if self.minidump:
                    self.minidump.replace(minidump)
                else:
                    self.minidump.put(minidump)
            self.save()
        except (KeyError, AttributeError) as e:
            raise e

    def get_minidump_path(self):
        return os.path.join(DUMPS_DIR, self.filename)

    def get_stacktrace(self):
        minidump_path = self.get_minidump_path()
        with open(os.devnull, 'w') as devnull:
            minidump_stackwalk_output = subprocess.check_output(['minidump_stackwalk', minidump_path, SYMFILES_DIR],
                                                                stderr=devnull)
        self.stacktrace = minidump_stackwalk_output.decode()
        self.save()

    def parse_stacktrace(self):
        minidump_path = self.get_minidump_path()
        with open(os.devnull, 'w') as devnull:
            stackwalker_output = subprocess.check_output([STACKWALKER, '--pretty', minidump_path, SYMFILES_DIR],
                                                         stderr=devnull)
        self.stacktrace_json = json.loads(stackwalker_output.decode())
        crash_info = self.stacktrace_json['crash_info']
        self.crash_reason = crash_info['type']
        self.crash_address = crash_info['address']
        self.crash_thread = crash_info['crashing_thread']
        self.save()
        Issue.create_or_update_issue(product=self.product,
                                     version=self.version,
                                     platform=self.platform,
                                     reason=self.crash_reason)

    def create_stacktrace(self):
        from oopsypad.server.worker import process_minidump
        process_minidump.delay(str(self.id))

    def get_time(self):
        return self.date_created.strftime('%d.%m.%Y %H:%M')

    @classmethod
    def get_by_id(cls, minidump_id):
        return cls.objects.get(id=minidump_id)

    @classmethod
    def create_minidump(cls, request):
        data = request.form
        minidump = cls(product=data['product'],
                       version=data['version'],
                       platform=data['platform'],
                       date_created=datetime.now())

        minidump.save_minidump(request)
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
                Q(date_created__lte=one_more_months_ago) & Q(date_created__gte=months_ago)).count()
            counts.append(months_ago_minidumps_count)
        return counts

    @classmethod
    def get_versions_per_product(cls, product):
        return sorted(list(set([i.version for i in cls.objects(product=product)])))

    @classmethod
    def get_last_n_project_minidumps(cls, n, project_name):
        project_minidumps = cls.objects(product=project_name)
        return project_minidumps[:n]

    def __str__(self):
        return "<Minidump: {} {} {} {}>".format(self.product,
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

    def save_symfile(self, request):
        try:
            file = request.files['symfile']
            self.symfile_name = secure_filename(file.filename)
            target_path = self.get_symfile_path()
            if not os.path.isdir(target_path):
                os.makedirs(target_path)
            file.save(os.path.join(target_path, self.symfile_name))
            self.save()
        except(KeyError, AttributeError) as e:
            raise e

    def get_symfile_path(self):
        return os.path.join(SYMFILES_DIR, self.product, self.symfile_id)

    @classmethod
    def create_symfile(cls, request, product, id):
        data = request.form
        try:
            symfile = cls.objects.get(symfile_id=id)
        except mongo.DoesNotExist:
            symfile = cls(product=product,
                          symfile_id=id,
                          version=data['version'],
                          platform=data['platform'],
                          date_created=datetime.now())
            symfile.save_symfile(request)
            platform = Platform.create_platform(name=data['platform'])
            Project.create_project(name=product, min_version=data['version'], allowed_platforms=[platform])
        return symfile

    def __str__(self):
        return "<Symfile: {} {} {} {}>".format(self.product,
                                               self.version,
                                               self.platform,
                                               self.symfile_id)


class Project(mongo.Document):
    name = fields.StringField(required=True, unique=True)
    min_version = fields.StringField()
    allowed_platforms = fields.ListField(fields.ReferenceField('Platform'))

    def get_allowed_platforms(self):
        return [i.name for i in self.allowed_platforms]

    @classmethod
    def create_project(cls, name, min_version, allowed_platforms):
        try:
            project = cls.objects.get(name=name)
            if min_version < project.min_version:
                project.min_version = min_version
            for p in allowed_platforms:
                if p not in project.allowed_platforms:
                    project.allowed_platforms.append(p)
        except mongo.DoesNotExist:
            project = cls(name=name,
                          min_version=min_version,
                          allowed_platforms=allowed_platforms)
        project.save()
        return project

    def __str__(self):
        return "<Project: {} {} {}>".format(self.name,
                                            self.min_version,
                                            self.allowed_platforms)


class Platform(mongo.Document):
    # platforms = ['Linux', 'MacOS', 'Windows']
    name = fields.StringField(required=True, unique=True)
    # name = fields.StringField(required=True, unique=True, choices=platforms)

    @classmethod
    def create_platform(cls, name):
        try:
            platform = Platform.objects.get(name=name)
        except mongo.DoesNotExist:
            platform = cls(name=name)
            platform.save()
        return platform

    def __str__(self):
        return self.name


class Issue(mongo.Document):
    product = fields.StringField()
    version = fields.StringField()
    platform = fields.StringField()
    reason = fields.StringField()
    total = fields.IntField(default=1)
    meta = {'ordering': ['-total']}

    @classmethod
    def create_or_update_issue(cls, product, version, platform, reason):
        try:
            issue = cls.objects.get(product=product,
                                    version=version,
                                    platform=platform,
                                    reason=reason)
        except mongo.DoesNotExist:
            issue = None
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
        return "<Issue: {} {} {} {} {}>".format(self.product,
                                                self.version,
                                                self.platform,
                                                self.reason,
                                                self.total)
