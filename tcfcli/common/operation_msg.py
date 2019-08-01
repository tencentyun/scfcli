# -*- coding: utf-8 -*-

import click
from builtins import str as text

import platform
version = platform.python_version()
if version < '3':
    import sys

    reload(sys)
    sys.setdefaultencoding("utf-8")

class Operation():
    def __init__(self, message):
        self.message = message

    def format_message(self):
        return self.message

    def success(self):
        click.secho(click.style("[o]", bg="green") + click.style(u' %s' % text(self.format_message()), fg="green"))

    def warning(self):
        click.secho(click.style("[!]", bg="magenta") + click.style(u' %s' % text(self.format_message()), fg="magenta"))

    def information(self):
        click.secho(click.style("[*]", bg="yellow") + click.style(u' %s' % text(self.format_message()), fg="yellow"))

    def process(self):
        click.secho(click.style("[>]", bg="cyan") + click.style(u' %s' % text(self.format_message()), fg="cyan"))
