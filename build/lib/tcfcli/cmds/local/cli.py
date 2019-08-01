# -*- coding: utf-8 -*-

import click
from .invoke.cli import invoke
from .start_api.cli import start_api
from .generate_event.cli import generate_event
from tcfcli.help.message import LocalHelp as help


@click.group(name='local', short_help=help.SHORT_HELP)
# @click.command(short_help="Run your SCF function locally for quick development.")
def local():
    """
        \b
        The scf cli completes the local trigger run by the local invoke subcommand. The scf command line tool will start the container instance according to the specified function template configuration file, mount the code directory to the specified directory of the container instance, and run the code through the specified trigger event to implement the local cloud function simulation run.
        \b
        Before running local debugging, make sure that Docker is installed and started in your local environment. The installation and configuration process of Docker can refer to the installation and configuration.
            * https://cloud.tencent.com/document/product/583/33449
        \b
        Common usage:
        \b
            * Startup function runs locally
              $ scf local generate-event cos post | scf local invoke --template template.yaml
            \b
            * Startup function runs locally and outputs test events via a file
              $ scf local invoke --template template.yaml --event event.json
    """
    pass


local.add_command(invoke)
local.add_command(generate_event)

# local.add_command(start_api)
