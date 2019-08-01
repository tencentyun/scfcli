# -*- coding: utf-8 -*-

from click import ClickException
import click
from builtins import str as text

import platform
version = platform.python_version()
if version < '3':
    import sys

    reload(sys)
    sys.setdefaultencoding("utf-8")

class TcSamException(ClickException):
    def format_message(self):
        return self.message

    def show(self):
        click.secho(click.style("[×]", bg="red") + click.style(u' %s' % text(self.format_message()), fg="red"))


exit_code = 1
