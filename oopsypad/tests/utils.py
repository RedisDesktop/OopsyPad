from oopsypad.server import models


def fake_create_stacktrace_worker(minidump):
    minidump = models.Minidump.get_by_id(minidump.id)
    minidump.get_stacktrace()
    minidump.parse_stacktrace()
