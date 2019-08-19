# -*- coding: utf-8 -*-

import click
import sys
from click.utils import echo
from builtins import str as text


class TcSamException(click.ClickException):

    def __init__(self, message):
        super(TcSamException, self).__init__(str(message))

    def format_message(self):
        return self.message

    def show(self, file=None):
        if "--no-color" in sys.argv or "-nc" in sys.argv:
            echo(click.style("[×]") + click.style(u' %s' % text(self.format_message())), file=file)
        else:
            echo(click.style("[×]", bg="red") + click.style(u' %s' % text(self.format_message()), fg="red"), file=file)


exit_code = 1
