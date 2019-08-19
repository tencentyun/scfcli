# -*- coding: utf-8 -*-

import sys
import click
from builtins import str as text


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

    def success(self):
        if "--no-color" in sys.argv or "-nc" in sys.argv:
            click.secho(click.style("[o]") + click.style(u' %s' % self.format_message()))
        else:
            click.secho(click.style("[o]", bg="green") + click.style(u' %s' % self.format_message()), fg="green")

    def warning(self):
        if "--no-color" in sys.argv or "-nc" in sys.argv:
            click.secho(click.style("[!]") + click.style(u' %s' % self.format_message()))
        else:
            click.secho(click.style("[!]", bg="magenta") + click.style(u' %s' % self.format_message()), fg="magenta")

    def information(self):
        if "--no-color" in sys.argv or "-nc" in sys.argv:
            click.secho(click.style("[*]") + click.style(u' %s' % self.format_message()))
        else:
            click.secho(click.style("[*]", bg="yellow") + click.style(u' %s' % self.format_message()), fg="yellow")

    def process(self):
        if "--no-color" in sys.argv or "-nc" in sys.argv:
            click.secho(click.style("[>]") + click.style(u' %s' % self.format_message()))
        else:
            click.secho(click.style("[>]", bg="cyan") + click.style(u' %s' % self.format_message()), fg="cyan")

    def out_infor(self):
        if "--no-color" in sys.argv or "-nc" in sys.argv:
            click.secho(click.style("    ") + click.style(u' %s' % self.format_message()))
        else:
            click.secho(click.style("    ") + click.style(u' %s' % self.format_message()), fg="cyan")

    def exception(self):
        if "--no-color" in sys.argv or "-nc" in sys.argv:
            click.secho(click.style("[x]") + click.style(u' %s' % self.format_message()))
        else:
            click.secho(click.style("[x]", bg="red") + click.style(u' %s' % self.format_message()), fg="red")

    def echo(self):
        if "--no-color" in sys.argv or "-nc" in sys.argv:
            click.secho(u'%s' % self.format_message(), bold=self.bold, dim=self.dim,
                        underline=self.underline, blink=self.blink, reverse=self.reverse, reset=self.reset,
                        file=self.file, nl=self.nl, err=self.err, color=self.color, )
        else:
            click.secho(u'%s' % self.format_message(), fg=self.fg, bg=self.bg, bold=self.bold, dim=self.dim,
                        underline=self.underline, blink=self.blink, reverse=self.reverse, reset=self.reset,
                        file=self.file, nl=self.nl, err=self.err, color=self.color, )

    def style(self):
        if "--no-color" in sys.argv or "-nc" in sys.argv:
            return click.style(u'%s' % self.format_message(), bold=self.bold, dim=self.dim,
                               underline=self.underline, blink=self.blink, reverse=self.reverse, reset=self.reset,)
        else:
            return click.style(u'%s' % self.format_message(), fg=self.fg, bg=self.bg, bold=self.bold, dim=self.dim,
                               underline=self.underline, blink=self.blink, reverse=self.reverse, reset=self.reset,)
