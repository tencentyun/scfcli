# -*- coding: utf-8 -*-

import os
import sys
import click
import logging
from logging.handlers import RotatingFileHandler
from builtins import str as text
from tcfcli.common.user_config import UserConfig

home = os.path.expanduser('~')
_LOG_FILE_PATH_ = os.path.join(home, '.scfcli_log')
if not os.path.exists(_LOG_FILE_PATH_):
    os.makedirs(_LOG_FILE_PATH_)

_LOG_FILE_ = os.path.join(_LOG_FILE_PATH_, 'scfcli.log')
logger = logging.getLogger()
for eve in logger.handlers:
    logger.handlers.remove(eve)
fh = RotatingFileHandler(_LOG_FILE_, maxBytes=100000, backupCount=10)
fh.setFormatter(logging.Formatter('%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'))
fh.setLevel(level=logging.FATAL)
logger.addHandler(fh)


class Operation(object):
    def __init__(self, message, fg=None, bg=None, bold=None, dim=None, underline=None, blink=None, reverse=None,
                 reset=True, file=None, nl=True, err=False, color=None, err_msg=None, level=None, tofile=True):
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
        self.err_msg = err_msg
        self.level = level
        self.tofile = tofile

    def format_message(self):
        return text(self.message)

    def new_style(self, msg, bg=None, fg=None):
        if "--no-color" in sys.argv or "-nc" in sys.argv or UserConfig().section_map[UserConfig.OTHERS][
            'no_color'].upper() == 'TRUE':
            return click.style(u'%s' % msg)
        else:
            return click.style(u'%s' % msg, bg=bg, fg=fg)

    def success(self):
        if self.tofile:
            self.log(logs="INFO")
        click.secho(self.new_style("[o]", bg="green") + self.new_style(u' %s' % self.format_message(), fg="green"))

    def begin(self):
        self.log(logs="INFO")
        click.secho(self.new_style("[+]", bg="green") + self.new_style(u' %s' % self.format_message(), fg="green"))

    def warning(self):
        self.log(logs="WARNING")
        click.secho(self.new_style("[!]", bg="magenta") + self.new_style(u' %s' % self.format_message(), fg="magenta"))

    def information(self):
        self.log(logs="INFO")
        click.secho(self.new_style("[*]", bg="yellow") + self.new_style(u' %s' % self.format_message(), fg="yellow"))

    def process(self):
        self.log(logs="INFO")
        click.secho(self.new_style("[>]", bg="cyan") + self.new_style(u' %s' % self.format_message(), fg="cyan"))

    def out_infor(self):
        self.log(logs="INFO")
        click.secho(self.new_style("    ") + self.new_style(u' %s' % self.format_message(), fg="cyan"))

    def no_output(self):
        self.log(logs=self.level if self.level else "WARNING")

    def exception(self):
        self.log(logs="ERROR")
        click.secho(self.new_style("[x] [ERROR] ", bg="red") + self.new_style(u' %s' % self.format_message(), fg="red"))

    def echo(self):
        self.log(logs="INFO")
        if "--no-color" in sys.argv or "-nc" in sys.argv or UserConfig().section_map[UserConfig.OTHERS][
            'no_color'].startswith('True'):
            click.secho(u'%s' % self.format_message(), bold=self.bold, dim=self.dim,
                        underline=self.underline, blink=self.blink, reverse=self.reverse, reset=self.reset,
                        file=self.file, nl=self.nl, err=self.err, color=self.color, )
        else:
            click.secho(u'%s' % self.format_message(), fg=self.fg, bg=self.bg, bold=self.bold, dim=self.dim,
                        underline=self.underline, blink=self.blink, reverse=self.reverse, reset=self.reset,
                        file=self.file, nl=self.nl, err=self.err, color=self.color, )

    def style(self):
        if "--no-color" in sys.argv or "-nc" in sys.argv or UserConfig().section_map[UserConfig.OTHERS][
            'no_color'].startswith('True'):
            return click.style(u'%s' % self.format_message(), bold=self.bold, dim=self.dim,
                               underline=self.underline, blink=self.blink, reverse=self.reverse, reset=self.reset, )
        else:
            return click.style(u'%s' % self.format_message(), fg=self.fg, bg=self.bg, bold=self.bold, dim=self.dim,
                               underline=self.underline, blink=self.blink, reverse=self.reverse, reset=self.reset, )

    def log(self, logs):
        if logs == "DEBUG":
            logger.debug(self.message)
        elif logs == "INFO":
            logger.info(self.message)
        elif logs == "WARNING":
            logger.warning(self.message)
        elif logs == "ERROR":
            err_msg = text(self.err_msg) if self.err_msg else self.message
            logger.error(err_msg)
