# -*- coding: utf-8 -*-

import click
from .list.cli import list
from .get.cli import get
from .update.cli import update
from tcfcli.help.message import EventdataHelp as help


@click.group(name='eventdata', short_help=help.SHORT_HELP)
def eventdata():
    '''
        \b
        Scf remote function event manage.
        \b
        Common usage:
            \b
            * Show the SCF function event list
              $ scf eventdata list --name Function1
            \b
            * Get a function event
              $ scf eventdata get --name test  --event event
            \b
            * Update eventdata to remote function
              $ scf eventdata update --name test  --dir .
    '''
    pass


eventdata.add_command(list)
eventdata.add_command(get)
eventdata.add_command(update)
