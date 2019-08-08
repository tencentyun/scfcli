# -*- coding: utf-8 -*-

import click
from .delete.cli import delete
from .list.cli import list
from tcfcli.help.message import FunctionHelp as help


@click.group(name='function', short_help=help.SHORT_HELP)
def function():
    pass


function.add_command(delete)
function.add_command(list)
