import calendar
from datetime import datetime
import os
import random
import warnings

from dateutil.relativedelta import relativedelta
from flask import current_app, escape, flash, jsonify, Markup, redirect, request
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.base import MenuLink
from flask_admin.contrib.mongoengine import helpers, ModelView
from flask_admin.contrib.mongoengine.view import DEFAULT_FORMATTERS
from flask_admin.model.template import macro
from flask_security import current_user
from mongoengine import GridFSProxy
from wtforms import StringField, validators

from oopsypad.server import models
from oopsypad.server.helpers import last_12_months


def date_format(view, value):
    return value.strftime('%d-%m-%Y %-I:%M %p')


def grid_formatter(view, value):
    if not value.grid_id:
        return ''

    args = helpers.make_gridfs_args(value)

    return Markup(
        '<a href="{url}" target="_blank" '
        'title="{size}k ({content_type})">'
        '<i class="fa fa-file glyphicon glyphicon-file"></i>'
        '{name}</a> '.format(
            url=view.get_url('.api_file_view', **args),
            name=escape(value.name),
            size=value.length // 1024,
            content_type=escape(value.content_type)))


CUSTOM_TYPE_FORMATTERS = DEFAULT_FORMATTERS
CUSTOM_TYPE_FORMATTERS.update({
    datetime: date_format,
    GridFSProxy: grid_formatter
})


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
        if models.User.objects.count() == 0:
            return redirect(current_app.config['SETUP_ADMIN_URL'])
        return self.render('admin/index.html')


class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        flash('Access denied.', 'warning')
        return redirect('/')


class DeveloperModelView(ModelView):
    def is_accessible(self):
        return (current_user.has_role('admin') or
                current_user.has_role('developer'))


class ProjectView(AdminModelView):
    can_delete = False
    can_view_details = True
    column_display_actions = False
    column_editable_list = ['name']
    column_formatters = dict(actions=macro('render_actions'))
    column_labels = dict(min_version='Minimum Version')
    column_list = ['name', 'min_version', 'allowed_platforms', 'actions']
    create_modal = True
    create_modal_template = 'admin/add_project_modal.html'
    create_template = 'admin/add_project.html'
    edit_template = 'admin/edit_project.html'
    form_args = dict(
        min_version={'label': 'Minimum required version of crashed app'},
        allowed_platforms={'label': 'Allowed platforms'})
    form_create_rules = ('name',)
    form_edit_rules = ('min_version', 'allowed_platforms')
    form_overrides = dict(min_version=StringField)
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


class CrashReportView(DeveloperModelView):
    can_create = False
    can_delete = False
    can_edit = False
    column_display_actions = False
    column_filters = ('product', 'version', 'platform', 'date_created',
                      'crash_reason')
    column_list = ['product', 'version', 'platform', 'date_created',
                   'crash_reason']
    list_template = 'admin/crash_report_list.html'


class IssueView(DeveloperModelView):
    can_create = False
    can_delete = False
    can_edit = False
    can_view_details = True
    column_default_sort = ('total', True)
    column_display_actions = False
    column_filters = ('product', 'platform', 'reason')
    column_formatters = dict(actions=macro('render_actions'))
    column_list = ['platform', 'version', 'reason', 'total', 'actions']
    form_args = dict(total={'label': 'Total Crash Reports'})
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


class UserView(AdminModelView):
    column_list = ['email', 'active', 'roles']
    form_edit_rules = ['email', 'roles', 'active']
    form_overrides = dict(email=StringField)


class SymfileView(AdminModelView):
    can_edit = False
    can_view_details = True
    column_editable_list = ['version']
    column_labels = dict(symfile_name='Filename',
                         symfile_id='ID')
    column_type_formatters = CUSTOM_TYPE_FORMATTERS
    form_excluded_columns = ['product', 'platform', 'date_created',
                             'symfile_id', 'symfile_name']
    form_overrides = dict(version=StringField)

    def on_model_change(self, form, model, is_created=None):
        if hasattr(form, 'symfile') and form.symfile:
            symfile = form.symfile.data
            symfile.stream.seek(0)
            try:
                symfile_first_line = symfile.stream.readline().decode()
                _, platform, _, symfile_id, product = symfile_first_line.split()
            except Exception as e:
                current_app.logger.exception(
                    'Unable to parse symfile: {}'.format(e))
                raise validators.ValidationError(
                    'Unable to parse symfile invalid content.')

            existing_symfile = models.Symfile.objects(
                symfile_id=symfile_id).first()
            if existing_symfile:
                raise validators.ValidationError(
                    'Symfile with this ID already exists.')
            if is_created:
                model.product = product
                models.version = form.version.data
                model.platform = platform
                model.symfile_id = symfile_id
                model.save_symfile(symfile)
                symfile.close()

    def on_model_delete(self, model):
        if all(getattr(model, p)
               for p in ['product', 'symfile_name', 'symfile_name']):

            symfile = os.path.join(model.get_symfile_path(), model.symfile_name)
            if os.path.isfile(symfile):
                try:
                    os.remove(symfile)
                    current_app.logger.info(
                        'Symfile {} for {} {} ({}) was deleted.'.format(
                            symfile,
                            model.product,
                            model.version,
                            model.platform))
                except Exception as e:
                    current_app.logger.exception(
                        'Unable to delete symfile: {}'.format(e))


admin = Admin(
    name='OopsyPad',
    template_mode='bootstrap3',
    index_view=CustomAdminView(template='index.html', url='/')
)


admin.add_link(AuthenticatedMenuLink(name='Logout', url='/logout'))
admin.add_link(NotAuthenticatedMenuLink(name='Login', url='/login'))

with warnings.catch_warnings():
    warnings.filterwarnings(action='ignore',
                            message='Fields missing from ruleset',
                            category=UserWarning)
    admin.add_view(ProjectView(models.Project, name='Projects'))
    admin.add_view(AdminModelView(models.Platform, name='Platforms'))
    admin.add_view(SymfileView(models.Symfile, name='Symfiles',
                               menu_icon_type='glyph',
                               menu_icon_value='glyphicon-file'))
    admin.add_view(CrashReportView(models.Minidump, name='Crash Reports',
                                   endpoint='crash-reports',
                                   menu_icon_type='glyph',
                                   menu_icon_value='glyphicon-fire'))
    admin.add_view(IssueView(models.Issue, name='Issues',
                             menu_icon_type='glyph',
                             menu_icon_value='glyphicon-flash'))
    admin.add_view(UserView(models.User, name='Users',
                            menu_icon_type='glyph',
                            menu_icon_value='glyphicon-user'))
