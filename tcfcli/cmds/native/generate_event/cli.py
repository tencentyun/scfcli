# -*- coding: utf-8 -*-

import click
from tcfcli.cmds.local.generate_event.generate_event_service import GenerateEventService


@click.command(name="generate-event", cls=GenerateEventService, short_help="Simulate a service generation event.")
def generate_event():
    """
    \b
    Simulate a service generation event.
    \b
    Common usage:
        \b
        * Generate a cmq event
        \b
          $ scf native generate-event cmq notification  --owner  19911112
        \b
        * Use the | to send to invoke
        \b
          $ scf native generate-event cmq notification  --owner  19911112 | scf local invoke -t template.yaml
    """
    pass
