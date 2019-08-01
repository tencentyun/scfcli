# -*- coding: utf-8 -*-
import click
import platform

click.disable_unicode_literals_warning = True

version = platform.python_version()
if version < '3':
    import sys

    reload(sys)
    sys.setdefaultencoding("utf-8")
