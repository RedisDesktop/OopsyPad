from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.mongoengine import ModelView
from flask_admin.model.template import macro
from oopsypad.server import models


class CustomAdminView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')


class ProjectView(ModelView):
    action_disallowed_list = ['delete']
    can_view_details = True
    column_display_actions = False
    column_editable_list = ['name']
    column_formatters = dict(actions=macro('render_actions'))
    column_list = ('name', 'actions')
    create_modal = True
    create_modal_template = 'admin/add_project_modal.html'
    create_template = 'admin/add_project.html'
    details_template = 'admin/project_overview.html'
    edit_template = 'admin/edit_project.html'
    form_args = {
        'min_version': {'label': 'Minimum required version of crashed app'},
        'allowed_platforms': {'label': 'Allowed platforms'}
    }
    form_create_rules = {'name'}
    form_edit_rules = ('min_version', 'allowed_platforms')
    list_template = '/admin/project_list.html'


admin = Admin(
    name='OopsyPad',
    template_mode='bootstrap3',
    index_view=CustomAdminView(
        template='index.html',
        url="/")
)

admin.add_view(ProjectView(models.Project, name='Projects'))
admin.add_view(ModelView(models.Platform, name='Platforms'))
