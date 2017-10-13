import json
import mongoengine as mongo
from mongoengine import fields
import os
from werkzeug.utils import secure_filename

DUMPS_DIR = "dumps"
SYM_FILES_DIR = "symbols"
STACK_TRACES_DIR = "stacktraces"
ALLOWED_EXTENSIONS = 'dmp'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class Minidump(mongo.Document):
    # product version platform upload_file_minidump
    product = fields.StringField()  # Crashed application name
    version = fields.StringField()  # Crashed application version
    platform = fields.StringField()  # OS name
    filename = fields.StringField()
    minidump = fields.FileField()  # Google Breakpad minidump

    def save_minidump(self, request):

        if not os.path.isdir(DUMPS_DIR):
            os.makedirs(DUMPS_DIR)

        if 'minidump' in request.files:
            file = request.files['minidump']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                self.filename = filename
                target_path = self.get_minidump_path()
                file.save(target_path)
                # Q: do we need this file field at all?
                with open(target_path, 'rb') as minidump:
                    if self.minidump:
                        self.minidump.replace(minidump)
                    else:
                        self.minidump.put(minidump)

    def get_minidump_path(self):
        return os.path.join(DUMPS_DIR, self.filename)

    def get_stacktrace(self):

        raise NotImplementedError()

    @classmethod
    def create_minidump(cls, request):

        data = json.loads(request.form['data'])
        minidump = cls(product=data['product'],
                       version=data['version'],
                       platform=data['platform'])
        try:
            cls.save_minidump(minidump, request)
        except Exception as e:
            print(e)

        minidump.save()
        return minidump

    def __str__(self):
        return "<Minidump: {} {} {} {}>".format(self.product, self.version, self.platform, self.filename)


class SymFile(mongo.Document):
    project = fields.StringField()
    version = fields.StringField()
    platform = fields.StringField()
    sym_filename = fields.StringField()
    sym_file = fields.FileField()

    def save_sym_file(self, request):
        if not os.path.isdir(SYM_FILES_DIR):
            os.makedirs(SYM_FILES_DIR)
        if 'symfile' in request.files:
            file = request.files['symfile']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                self.sym_filename = filename
                target_path = self.get_sym_file_path()
                file.save(target_path)

    def get_sym_file_path(self):
        return os.path.join(SYM_FILES_DIR, self.project, self.sym_filename)
