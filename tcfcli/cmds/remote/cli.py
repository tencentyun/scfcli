# -*- coding: utf-8 -*-

import click
from .invoke.cli import invoke
from tcfcli.help.message import RemoteHelp as help


@click.group(name='remote', short_help=help.SHORT_HELP)
def remote():
    '''
        \b
        Scf remote function invoke.
        \b
        Common usage:
            \b
            * Invoke the remote SCF function
              $ scf remote invoke -n test -e .event.json -l tail
    '''
    pass


remote.add_command(invoke)
