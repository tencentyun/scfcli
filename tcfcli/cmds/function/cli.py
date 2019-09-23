# -*- coding: utf-8 -*-

import click
from .delete.cli import delete
from .list.cli import list
from .information.cli import info
from tcfcli.help.message import FunctionHelp as help


@click.group(name='function', short_help=help.SHORT_HELP)
def function():
    '''
        \b
        Scf remote function manage.
        \b
        Common usage:
            \b
            * Show the SCF function list
              $ scf function list
            \b
            * Delete a function
              $ scf function delete --name functionname --region ap-guangzhou --namespace default
    '''
    pass


function.add_command(delete)
function.add_command(list)
function.add_command(info)
