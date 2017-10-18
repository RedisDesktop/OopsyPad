import mongoengine as mongo
from mongoengine import fields
import os
import shutil
from werkzeug.utils import secure_filename

DUMPS_DIR = "dumps"
SYM_FILES_DIR = "symbols"
STACK_TRACES_DIR = "stacktraces"


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

    def get_stack_trace(self):

        raise NotImplementedError()

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
    sym_file_name = fields.StringField()
    sym_file_id = fields.StringField()
    sym_file = fields.FileField()

    def save_sym_file(self, request):
        if 'symfile' in request.files:
            file = request.files['symfile']
            if file:
                self.sym_file_name = secure_filename(file.filename)
                file.save(self.sym_file_name)
                with open(self.sym_file_name, 'r') as f:
                    _, self.platform, _, self.sym_file_id, self.product = f.readline().split()
                target_path = self.get_sym_file_path()
                if not os.path.isdir(target_path):
                    os.makedirs(target_path)
                shutil.move(self.sym_file_name, target_path)

    def get_sym_file_path(self):
        return os.path.join(SYM_FILES_DIR, self.product, self.sym_file_id)

    @classmethod
    def create_sym_file(cls, request):
        data = request.form
        sym_file = cls(version=data['version'])
        try:
            cls.save_sym_file(sym_file, request)
            sym_file.save()
        except Exception as e:
            print(e)
        sym_file.save()
        return sym_file

    def __str__(self):
        return "<SymFile: {} {} {} {}>".format(self.product,
                                               self.version,
                                               self.platform,
                                               self.sym_file_id)
