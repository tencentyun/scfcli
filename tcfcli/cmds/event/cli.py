# -*- coding: utf-8 -*-

import click
from .list.cli import list
from .get.cli import get
from tcfcli.help.message import EventHelp as help


@click.group(name='event', short_help=help.SHORT_HELP)
def event():
    '''
        \b
        Scf remote function event manage.
        \b
        Common usage:
            \b
            * Show the SCF function event list
              $ scf event list --name Function1
            \b
            * Get a function event
              $ scf event get --name test  --event event
    '''
    pass


event.add_command(list)
event.add_command(get)
