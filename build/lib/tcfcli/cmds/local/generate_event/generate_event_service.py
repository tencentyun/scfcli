# -*- coding: utf-8 -*-

import click
from tcfcli.cmds.local.generate_event.events_metadata import EVENTS_METADATA, EVENTS_HELP
from tcfcli.cmds.local.generate_event.generate_event_action import GenerateEventAction


class GenerateEventService(click.MultiCommand):
    '''
    this is a test
    '''

    def format_commands(self, ctx, formatter):
        """Extra format methods for multi methods that adds all the commands
        after the options.
        """
        rows = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command.  Ignore it
            if cmd is None:
                continue

            help = EVENTS_HELP[subcommand]
            rows.append((subcommand, help))

        if rows:
            with formatter.section('Commands'):
                formatter.write_dl(rows)

    def get_command(self, ctx, cmd):
        if cmd not in EVENTS_METADATA:
            return None
        return GenerateEventAction(cmd, EVENTS_METADATA[cmd])

    def list_commands(self, ctx):
        return sorted(EVENTS_METADATA.keys())
