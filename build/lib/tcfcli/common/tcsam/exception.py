# -*- coding: utf-8 -*-

from click import ClickException
import click
from builtins import str as text


class TcSamException(ClickException):
    def format_message(self):
        return self.message

    def show(self):
        click.secho(click.style("[×]", bg="red") + click.style(u' %s' % text(self.format_message()), fg="red"))


exit_code = 1
