# -*- coding: utf-8 -*-

import click
from tcfcli.help.message import ConfigureHelp as help
from .set.cli import set
from .get.cli import get
from .add.cli import add
from .change.cli import change


@click.group(name='configure', short_help=help.SHORT_HELP)
def configure():
    """
        \b
        You need to perform initial configuration and configure the account information in the configuration file of scf cli for subsequent use.
        \b
        Common usage:
            \b
            * Configure your account parameters
              $ scf configure set
            \b
            * Modify a configuration item
              $ scf configure set --region ap-shanghai
            \b
            * Get the configured information
              $ scf configure get
            \b
            * Configure change your user
              $ scf configure change
            \b
            * Add a user.
              $ scf configure add
    """


configure.add_command(get)
configure.add_command(set)
configure.add_command(add)
configure.add_command(change)
