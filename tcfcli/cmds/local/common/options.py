# -*- coding: utf-8 -*-

import click
import os
from tcfcli.help.message import CommonHelp as help

_DEAFULT_TEMPLATE_FILE = 'template.[yaml|yml]'
DEF_TMP_FILENAME = "template.yaml"

def get_template_abspath(ctx, param, template_name):
    if template_name == _DEAFULT_TEMPLATE_FILE:
        template_name = 'template.yaml'

        tmp = 'template.yml'
        if os.path.exists(tmp):
            template_name = tmp

    return os.path.abspath(template_name)


def template_click_option():
    """
    Click Option for template option
    """
    return click.option('--template', '-t',
                        default=DEF_TMP_FILENAME,
                        type=click.Path(exists=True),
                        envvar="TCF_TEMPLATE_FILE",
                        callback=get_template_abspath,
                        show_default=True)


def invoke_common_options(f):
    invoke_options = [
        template_click_option(),

        click.option('--env-vars', '-n',
                     help=help.INVOKE_ENV_VARS,
                     type=click.Path(exists=True)),

        click.option('--debug-port', '-d',
                     help=help.INVOKE_DEBUG_PORT,
                     envvar="TCF_DEBUG_PORT"),

        click.option('--debugger-path',
                     help=help.INVOKE_DEBUGGER_PATH),

        click.option('--debug-args',
                     help=help.INVOKE_DEBUG_ARGS,
                     envvar="DEBUGGER_ARGS"),

        click.option('--docker-volume-basedir', '-v',
                     help=help.INVOKE_DOCKER_VOLUME_BASEDIR,
                     envvar="TCF_DOCKER_VOLUME_BASEDIR"),

        click.option('--docker-network',
                     help=help.INVOKE_DOCKER_NETWORK,
                     envvar="TCF_DOCKER_NETWORK"),

        click.option('--log-file', '-l',
                     help=help.INVOKE_LOG_FILE),

        click.option('--skip-pull-image',
                     is_flag=True,
                     help=help.INVOKE_SKIP_PULL_IMAGE,
                     envvar="TCF_SKIP_PULL_IMAGE"),

        click.option('--region', help=help.INVOKE_REGION),

    ]

    for option in reversed(invoke_options):
        option(f)

    return f


def service_common_options(port):
    def construct_options(f):
        service_options = [
            click.option('--host',
                         default="127.0.0.1",
                         help="Local hostname or IP address bind to (default: '127.0.0.1')"),
            click.option("--port", "-p",
                         default=port,
                         help="Local port number to listen on (default: '{}')".format(str(port)))
        ]

        for option in reversed(service_options):
            option(f)

        return f

    return construct_options
