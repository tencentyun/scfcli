# -*- coding: utf-8 -*-

import sys
import platform
import click

click.disable_unicode_literals_warning = True

version = platform.python_version()
if version < '3':
    import sys

    reload(sys)
    sys.setdefaultencoding("utf-8")
