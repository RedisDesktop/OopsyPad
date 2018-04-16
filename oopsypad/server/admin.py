import calendar
from datetime import datetime
import random
import warnings

from dateutil.relativedelta import relativedelta
from flask import jsonify, request, redirect, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.base import MenuLink
from flask_admin.contrib.mongoengine import ModelView
from flask_admin.model.template import macro
from flask_security import current_user

from oopsypad.server.helpers import last_12_months
from oopsypad.server import models


def get_random_color():
    return '#%06x' % random.randint(0, 0xFFFFFF)


def get_decorated_data(labels, data, data_labels=None):
    result = {'labels': labels}
    datasets = []
    for i, d in enumerate(data):
        clr = get_random_color()
        ds = {
            'fillColor': clr,
            'strokeColor': clr,
            'highlightFill': clr,
            'highlightStroke': 'rgba(220,220,220,1)',
            'data': d
        }
        if data_labels:
            ds.update({'label': data_labels[i]})

        datasets.append(ds)
    result['datasets'] = datasets
    return result


def get_last_12_months_labels():
    today = datetime.today()
    labels = [(today - relativedelta(months=months)).month
              for months in last_12_months()]
    return [calendar.month_name[m] for m in labels]


class AuthenticatedMenuLink(MenuLink):
    def is_accessible(self):
        return current_user.is_authenticated


class NotAuthenticatedMenuLink(MenuLink):
    def is_accessible(self):
        return not current_user.is_authenticated


class CustomAdminView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')


class CustomModelView(ModelView):
    def is_accessible(self):
        return current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        flash('Access denied for non-admins.', 'warning')
        return redirect('/')


class ProjectView(CustomModelView):
    action_disallowed_list = ['delete']
    can_view_details = True
    column_display_actions = False
    column_editable_list = ['name']
    column_formatters = dict(actions=macro('render_actions'))
    column_list = ('name', 'actions')
    create_modal = True
    create_modal_template = 'admin/add_project_modal.html'
    create_template = 'admin/add_project.html'
    edit_template = 'admin/edit_project.html'
    form_args = {
        'min_version': {'label': 'Minimum required version of crashed app'},
        'allowed_platforms': {'label': 'Allowed platforms'}
    }
    form_create_rules = {'name'}
    form_edit_rules = ('min_version', 'allowed_platforms')
    list_template = 'admin/project_list.html'

    @expose('/details/')
    def details_view(self):
        project = models.Project.objects.get(id=request.args.get('id'))
        minidump_versions = models.Minidump.get_versions_per_product(
            product=project.name)
        last_10_minidumps = models.Minidump.get_last_n_project_minidumps(
            n=10, project_name=project.name)
        issues = models.Issue.get_top_n_project_issues(
            n=10, project_name=project.name)
        return self.render('admin/project_overview.html',
                           project=project,
                           versions=minidump_versions,
                           latest_crash_reports=last_10_minidumps,
                           top_issues=issues
                           )

    @expose('/_crash_reports')
    def crash_reports_chart(self):
        version = request.args.get('version')
        project = models.Project.objects.get(id=request.args.get('id'))
        platforms = project.get_allowed_platforms()
        if version and 'All' not in version:
            project_minidumps = models.Minidump.objects(product=project.name,
                                                        version=version)
        else:
            project_minidumps = models.Minidump.objects(product=project.name)
        data = {}
        for platform in platforms:
            platform_minidumps = project_minidumps(platform=platform)
            data[platform] = \
                models.Minidump.get_last_12_months_minidumps_counts(
                    platform_minidumps)

        labels = get_last_12_months_labels()
        return jsonify(
            result=get_decorated_data(labels=labels,
                                      data=data.values(),
                                      data_labels=list(data.keys())
                                      ))


class CrashReportView(CustomModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_display_actions = False
    column_list = ('product', 'version', 'platform', 'date_created',
                   'crash_reason')
    column_filters = ('product', 'version', 'platform', 'date_created',
                      'crash_reason')
    list_template = 'admin/crash_report_list.html'


class IssueView(CustomModelView):
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_default_sort = ('total', True)
    column_display_actions = False
    column_filters = ('product', 'platform', 'reason')
    column_formatters = dict(actions=macro('render_actions'))
    column_list = ('platform', 'version', 'reason', 'total', 'actions')
    form_args = {
        'total': {'label': 'Total Crash Reports'},
    }
    list_template = 'admin/issue_list.html'
    page_size = 10

    @expose('/details/')
    def details_view(self):
        issue = models.Issue.objects.get(id=request.args.get('id'))
        minidumps = models.Minidump.objects(product=issue.product,
                                            version=issue.version,
                                            platform=issue.platform,
                                            crash_reason=issue.reason)
        page_num = int(request.args.get('page') or 1)
        per_page = 10
        return self.render('admin/issue_details.html',
                           issue=issue,
                           column_details_list=self.column_details_list,
                           minidumps=minidumps.paginate(page=page_num,
                                                        per_page=per_page),
                           per_page=per_page)


admin = Admin(
    name='OopsyPad',
    template_mode='bootstrap3',
    index_view=CustomAdminView(
        template='index.html',
        url='/')
)


admin.add_link(AuthenticatedMenuLink(name='Logout', url='/logout'))
admin.add_link(NotAuthenticatedMenuLink(name='Login', url='/login'))

with warnings.catch_warnings():
    warnings.filterwarnings(action='ignore',
                            message='Fields missing from ruleset',
                            category=UserWarning)
    admin.add_view(ProjectView(models.Project, name='Projects'))
    admin.add_view(CustomModelView(models.Platform, name='Platforms'))
    admin.add_view(CrashReportView(
        models.Minidump, name='Crash Reports', endpoint='crash-reports'))
    admin.add_view(IssueView(models.Issue, name='Issues'))
