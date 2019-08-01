# -*- coding: utf-8 -*-

import click
from tcfcli.common import tcsam
from tcfcli.common.template import Template
from tcfcli.help.message import ValidateHelp as help


@click.command(name="validate", short_help=help.SHORT_HELP)
@click.option('--template-file', '-t', type=click.Path(exists=True), help=help.TEMPLATE_FILE)
def validate(template_file):
    '''
    Validate a SCF template.
    '''
    tcsam.tcsam_validate(Template.get_template_data(template_file))
