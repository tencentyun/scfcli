# -*- coding: utf-8 -*-

import click
from tcfcli.cmds.native.common.start_api_context import StartApiContext
from tcfcli.help.message import NativeHelp as help

DEF_TMP_FILENAME = "template.yaml"


@click.command(name='start-api', short_help=help.START_API_SHORT_HElP)
@click.option('--env-vars', '-n', help='JSON file contains function environment variables.',
              type=click.Path(exists=True))
@click.option('--template', '-t', default=DEF_TMP_FILENAME, type=click.Path(exists=True),
              envvar="TCF_TEMPLATE_FILE", show_default=True)
@click.option('--debug-port', '-d', help=help.START_API_DEBUG_PORT, default=None)
@click.option('--debug-args', help=help.START_API_DEBUG_ARGS, default="")
@click.argument('namespace_identifier', required=False)
@click.argument('function_identifier', required=False)
def startapi(template, namespace_identifier, function_identifier, env_vars, debug_port, debug_args):
    '''
    \b
    Execute your scf in a environment natively.
    \b
    Common usage:
        \b
        $ scf native start-api -t template.yaml
    '''
    start(template, namespace_identifier, function_identifier, env_vars, debug_port, debug_args)


def start(template, namespace, function, env_vars, debug_port, debug_args):
    try:
        with StartApiContext(
                template_file=template,
                namespace=namespace,
                debug_port=debug_port,
                debug_args=debug_args,
                function=function,
                env_file=env_vars,
        ) as context:
            context.start()
    except Exception as e:
        raise e
