import click
from tcfcli.cmds.local.generate_event.generate_event_service import GenerateEventService


@click.command(name="generate-event", cls=GenerateEventService)
def generate_event():
    """
    \b
    Simulate a service generation event

    Common usage:

        \b
        Generate a cmq event:
        \b
        $ scf local generate-event cmq notification  --owner  19911112
        \b
        Use the | to send to invoke
        \b
        scf local generate-event cmq notification  --owner  19911112 | scf local invoke -t template.yaml
    """
    pass
