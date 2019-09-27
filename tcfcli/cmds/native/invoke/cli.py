# -*- coding: utf-8 -*-

import click
import traceback
from tcfcli.cmds.native.common.invoke_context import InvokeContext
from tcfcli.help.message import NativeHelp as help
from tcfcli.common.operation_msg import Operation

DEF_TMP_FILENAME = "template.yaml"

STD_IN = '-'


@click.command(name='invoke', short_help=help.INVOKE_SHORT_HELP)
@click.option('--event', '-e', type=click.Path(), default=STD_IN, help=help.INVOKE_EVENT)
@click.option('--no-event', is_flag=True, default=False, help=help.INVOKE_NO_ENENT)
@click.option('--env-vars', '-n', help=help.INVOKE_ENV_VARS, type=click.Path(exists=True))
@click.option('--debug-port', '-d', help=help.INVKOE_DEBUG_PORT, default=None)
@click.option('--debug-args', help=help.INVOKE_DEBUG_ARGS, default="")
@click.option('--quiet', '-q', is_flag=True, default=False, help=help.INVOKE_QUIET)
@click.option('--template', '-t', default=DEF_TMP_FILENAME, type=click.Path(exists=True),
              envvar="TCF_TEMPLATE_FILE", show_default=True, help=help.INVOKE_TEMPLATE)
@click.argument('namespace_identifier', required=False)
@click.argument('function_identifier', required=False)
@click.option('--no-color', '-nc', is_flag=True, default=False, help=help.NOCOLOR)
def invoke(template, namespace_identifier, function_identifier, env_vars, event, no_event, debug_port, debug_args,
           quiet, no_color):
    '''
    \b
    Execute your scf in a environment natively.
    \b
    Common usage:
        \b
        * Startup function runs locally
          $ scf native invoke -t template.yaml
    '''
    do_invoke(template, namespace_identifier, function_identifier, env_vars, event, no_event, debug_port, debug_args,
              quiet)


def do_invoke(template, namespace, function, env_vars, event, no_event, debug_port, debug_args, quiet):
    if no_event:
        event_data = "{}"
    else:
        Operation('Enter an event:', color="green").echo()
        with click.open_file(event, 'r', encoding="utf-8") as f:
            event_data = f.read()
    try:
        with InvokeContext(
                template_file=template,
                namespace=namespace,
                function=function,
                env_file=env_vars,
                debug_port=debug_port,
                debug_args=debug_args,
                event=event_data,
                is_quiet=quiet
        ) as context:
            context.invoke()
    except Exception as e:
        Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
        raise e


def _get_event(event_file):
    if event_file == STD_IN:
        Operation('read event from stdin').echo()

    with click.open_file(event_file, 'r') as f:
        return f.read()
