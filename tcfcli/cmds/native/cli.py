# -*- coding: utf-8 -*-

import click
from .invoke.cli import invoke
from .startapi.cli import startapi
from .generate_event.cli import generate_event
from tcfcli.help.message import NativeHelp as help


@click.group(name='native', short_help=help.SHORT_HELP)
def native():
    """
        \b
        The scf cli completes the local trigger run by the native invoke subcommand. The scf command line tool will run the corresponding cloud in the specified directory of the machine according to the specified function template configuration file, and implement the local cloud function simulation run through the specified trigger event.
        \b
        Native debugging does not need to rely on Docker, just ensure that the environment is already installed on the system. The current native command only supports Node.js and Python runtime. To ensure consistent deployment of the cloud and the local version, it is recommended that the local version of the runtime and the cloud version be the same. For example, if you are using Node.js 6.10 in the cloud, this machine is also recommended to install Node.js 6.x.
        \b
        Common usage:
        \b
            * Startup function runs locally
              $ scf native generate-event cos post | scf native invoke --template template.yaml
            \b
            * Startup function runs locally and outputs test events via a file
              $ scf native invoke --template template.yaml --event event.json

    """
    pass


native.add_command(invoke)
#native.add_command(startapi)
native.add_command(generate_event)
