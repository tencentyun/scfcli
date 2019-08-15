# -*- coding: utf-8 -*-

import click
from builtins import str as text


class Operation(object):
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

    def out_infor(self):
        click.secho(click.style("    ") + click.style(u' %s' % text(self.format_message()), fg="cyan"))

    def exception(self):
        click.secho(click.style("[x]", bg="red") + click.style(u' %s' % text(self.format_message()), fg="red"))
