# -*- coding: utf-8 -*-

import sys
import click
from builtins import str as text
from tcfcli.common.user_config import UserConfig


class Operation(object):
    def __init__(self, message, fg=None, bg=None, bold=None, dim=None, underline=None, blink=None, reverse=None,
                 reset=True, file=None, nl=True, err=False, color=None, ):
        self.message = message
        self.fg = fg
        self.bg = bg
        self.bold = bold
        self.dim = dim
        self.underline = underline
        self.blink = blink
        self.reverse = reverse
        self.reset = reset
        self.file = file
        self.nl = nl
        self.err = err
        self.color = color

    def format_message(self):
        return text(self.message)

    def new_style(self, msg, bg=None, fg=None):
        if "--no-color" in sys.argv or "-nc" in sys.argv or UserConfig().section_map[UserConfig.OTHERS]['no_color'].upper() == 'TRUE':
            return click.style(u'%s' % msg)
        else:
            return click.style(u'%s' % msg, bg=bg, fg=fg)

    def success(self):
        click.secho(self.new_style("[o]", bg="green") + self.new_style(u' %s' % self.format_message(), fg="green"))

    def begin(self):
        click.secho(self.new_style("[+]", bg="green") + self.new_style(u' %s' % self.format_message(), fg="green"))

    def warning(self):
        click.secho(self.new_style("[!]", bg="magenta") + self.new_style(u' %s' % self.format_message(), fg="magenta"))

    def information(self):
        click.secho(self.new_style("[*]", bg="yellow") + self.new_style(u' %s' % self.format_message(), fg="yellow"))

    def process(self):
        click.secho(self.new_style("[>]", bg="cyan") + self.new_style(u' %s' % self.format_message(), fg="cyan"))

    def out_infor(self):
        click.secho(self.new_style("    ") + self.new_style(u' %s' % self.format_message(), fg="cyan"))

    def exception(self):
        click.secho(self.new_style("[x]", bg="red") + self.new_style(u' %s' % self.format_message(), fg="red"))

    def echo(self):
        if "--no-color" in sys.argv or "-nc" in sys.argv or UserConfig().section_map[UserConfig.OTHERS]['no_color'].startswith('True'):
            click.secho(u'%s' % self.format_message(), bold=self.bold, dim=self.dim,
                        underline=self.underline, blink=self.blink, reverse=self.reverse, reset=self.reset,
                        file=self.file, nl=self.nl, err=self.err, color=self.color, )
        else:
            click.secho(u'%s' % self.format_message(), fg=self.fg, bg=self.bg, bold=self.bold, dim=self.dim,
                        underline=self.underline, blink=self.blink, reverse=self.reverse, reset=self.reset,
                        file=self.file, nl=self.nl, err=self.err, color=self.color, )

    def style(self):
        if "--no-color" in sys.argv or "-nc" in sys.argv or UserConfig().section_map[UserConfig.OTHERS]['no_color'].startswith('True'):
            return click.style(u'%s' % self.format_message(), bold=self.bold, dim=self.dim,
                               underline=self.underline, blink=self.blink, reverse=self.reverse, reset=self.reset, )
        else:
            return click.style(u'%s' % self.format_message(), fg=self.fg, bg=self.bg, bold=self.bold, dim=self.dim,
                               underline=self.underline, blink=self.blink, reverse=self.reverse, reset=self.reset, )
