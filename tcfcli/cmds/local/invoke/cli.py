# -*- coding: utf-8 -*-

import click
from tcfcli.common.operation_msg import Operation
from tcfcli.cmds.local.common.invoke_context import InvokeContext
from tcfcli.cmds.local.common.options import invoke_common_options
from tcfcli.common.user_exceptions import UserException
from tcfcli.help.message import LocalHelp as help

STD_IN = '-'


@click.command(short_help=help.SHORT_HELP)
@click.option('--event', '-e', type=click.Path(), default=STD_IN, help=help.INVOKE_EVENT)
@click.option('--no-event', is_flag=True, default=False, help=help.INVOKE_NO_ENENT)
@invoke_common_options
@click.option('--quiet', '-q', is_flag=True, default=False, help=help.INVOKE_QUIET)
@click.argument('namespace_identifier', required=False)
@click.argument('function_identifier', required=False)
@click.option('--no-color', '-nc', is_flag=True, default=False, help=help.NOCOLOR)
def invoke(template, namespace_identifier, function_identifier, event, no_event, env_vars, debug_port, debug_args,
           debugger_path, docker_volume_basedir, docker_network, log_file, skip_pull_image, region, quiet, no_color):
    '''
    \b
    Execute your scf in a docker environment locally.
    \b
    Common usage:
        \b
        * Startup function runs locally
          $ scf local invoke -t template.yaml
    '''
    do_invoke(template, namespace_identifier, function_identifier, event, no_event, env_vars, debug_port, debug_args,
              debugger_path,
              docker_volume_basedir, docker_network, log_file, skip_pull_image, region, quiet)


def do_invoke(template, namespace_identifier, function_identifier, event, no_event, env_vars, debug_port, debug_args,
              debugger_path,
              docker_volume_basedir, docker_network, log_file, skip_pull_image, region, quiet):
    if no_event and event != STD_IN:
        raise UserException('event is conflict with no_event, provide only one.')

    if no_event:
        event_data = '{}'
    else:
        event_data = _get_event(event)

    try:
        with InvokeContext(template_file=template,
                           function_identifier=function_identifier,
                           env_vars_file=env_vars,
                           debug_port=debug_port,
                           debug_args=debug_args,
                           debugger_path=debugger_path,
                           docker_volume_basedir=docker_volume_basedir,
                           docker_network=docker_network,
                           log_file=log_file,
                           skip_pull_image=skip_pull_image,
                           region=region,
                           namespace=namespace_identifier,
                           is_quiet=quiet
                           ) as context:

            context.local_runtime_manager.invoke(context.functions_name, event_data, context.stdout, context.stderr)

    except Exception as e:
        raise e


def _get_event(event_file):
    if event_file == STD_IN:
        Operation('read event from stdin').process()

    with click.open_file(event_file, 'r') as f:
        return f.read()
