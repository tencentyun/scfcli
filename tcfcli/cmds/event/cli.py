# -*- coding: utf-8 -*-

import click
from .list.cli import list
from .get.cli import get
from tcfcli.help.message import EventHelp as help


@click.group(name='event', short_help=help.SHORT_HELP)
def event():
    """

    """
    pass


event.add_command(list)
event.add_command(get)
