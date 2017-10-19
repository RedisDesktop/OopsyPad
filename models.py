import mongoengine as mongo
from mongoengine import fields
import os
import shutil
from werkzeug.utils import secure_filename

DUMPS_DIR = "dumps"
SYMFILES_DIR = "symbols"
STACK_TRACES_DIR = "stacktraces"


class Minidump(mongo.Document):
    # product version platform upload_file_minidump
    product = fields.StringField()  # Crashed application name
    version = fields.StringField()  # Crashed application version
    platform = fields.StringField()  # OS name
    filename = fields.StringField()
    minidump = fields.FileField()  # Google Breakpad minidump
    stacktrace = fields.StringField()

    def save_minidump(self, request):
        if not os.path.isdir(DUMPS_DIR):
            os.makedirs(DUMPS_DIR)

        if 'minidump' in request.files:
            file = request.files['minidump']
            if file:
                self.filename = secure_filename(file.filename)
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

    @classmethod
    def create_minidump(cls, request):

        data = request.form
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
        return "<Minidump: {} {} {} {}>".format(self.product,
                                                self.version,
                                                self.platform,
                                                self.filename)


class SymFile(mongo.Document):
    product = fields.StringField()
    version = fields.StringField()
    platform = fields.StringField()
    symfile_name = fields.StringField()
    symfile_id = fields.StringField()
    symfile = fields.FileField()

    def save_symfile(self, request):
        if 'symfile' in request.files:
            file = request.files['symfile']
            if file:
                self.symfile_name = secure_filename(file.filename)
                file.save(self.symfile_name)
                with open(self.symfile_name, 'r') as f:
                    _, self.platform, _, self.symfile_id, self.product = f.readline().split()
                target_path = self.get_symfile_path()
                if not os.path.isdir(target_path):
                    os.makedirs(target_path)
                shutil.move(self.symfile_name, target_path)

    def get_symfile_path(self):
        return os.path.join(SYMFILES_DIR, self.product, self.symfile_id)

    @classmethod
    def create_symfile(cls, request):
        data = request.form
        symfile = cls(version=data['version'])
        try:
            cls.save_symfile(symfile, request)
            symfile.save()
        except Exception as e:
            print(e)
        symfile.save()
        return symfile

    def __str__(self):
        return "<SymFile: {} {} {} {}>".format(self.product,
                                               self.version,
                                               self.platform,
                                               self.symfile_id)
