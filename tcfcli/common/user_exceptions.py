# -*- coding: utf-8 -*-

import click
from builtins import str as text
from click.utils import echo
from click._compat import get_text_stderr


class UserException(click.ClickException):

    def __init__(self, message):
        super(UserException, self).__init__(str(message))

    def format_message(self):
        return str(self.message)

    def show(self, file=None):
        if file is None:
            file = get_text_stderr()
        echo(click.style("[x]", bg="red") + click.style(u' %s' % text(self.format_message()), fg="red"),
             file=file)

    exit_code = 1


class CloudAPIException(UserException):
    pass


class InvokeContextException(UserException):
    pass


class TemplateNotFoundException(UserException):
    pass


class DeployException(UserException):
    pass


class InvokeException(UserException):
    pass


class TimeoutException(UserException):
    pass


class OutTemplateAlreadyExist(UserException):
    pass


class ContextException(UserException):
    pass


class NoApiDefinition(UserException):
    pass


class InvalidTemplateException(UserException):
    pass


class UploadToCosFailed(UserException):
    pass


class UploadFailed(UserException):
    pass


class FunctionNotFound(UserException):
    pass


class InvalidCodeDirs(UserException):
    pass


class UserConfigException(UserException):
    pass


class InvalidEnvParameters(UserException):
    pass


class InvalidOptionValue(UserException):
    pass


class InvalidResourceException(UserException):
    pass


class InvalidEventException(UserException):
    pass


class InvalidEnvVarsException(UserException):
    pass


class LogsException(UserException):
    pass


class ArgsException(UserException):
    pass


class NamespaceException(UserException):
    pass


class DeleteException(UserException):
    pass


class InitException(UserException):
    pass


class TCSDKException(UserException):
    pass


class RollbackException(UserException):
    pass


class PackageException(UserException):
    pass


class EventFileNotFoundException(UserException):
    pass


class EventFileNameFormatException(UserException):
    pass


class LoadEventFileException(UserException):
    pass


class OutputDirNotFound(UserException):
    pass


class InvalidDocumentException(Exception):
    def __init__(self, causes):
        self._causes = sorted(causes)

    @property
    def message(self):
        return "Invalid Specification Document. Number of errors found: {}.".format(len(self.causes))

    @property
    def causes(self):
        return self._causes
