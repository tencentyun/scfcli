import click
from tcfcli.cmds.native.common.start_api_context import StartApiContext
from tcfcli.cmds.local.common.options import invoke_common_options
from tcfcli.common.user_exceptions import UserException

DEF_TMP_FILENAME = "template.yaml"


@click.command(name='start-api')
@click.option('--env-vars', '-n', help='JSON file contains function environment variables.', type=click.Path(exists=True))
@click.option('--template', '-t', default=DEF_TMP_FILENAME, type=click.Path(exists=True),
              envvar="TCF_TEMPLATE_FILE", show_default=True)
@click.argument('namespace_identifier', required=False)
@click.argument('function_identifier', required=False)
def startapi(template, namespace_identifier, function_identifier, env_vars):
    '''
    \b
    Execute your scf in a environment natively
    \b
    Common usage:
        \b
        $ scf native start-api -t template.yaml
    '''
    start(template, namespace_identifier, function_identifier, env_vars)


def start(template, namespace, function, env_vars):
    try:
        with StartApiContext(
            template_file=template,
            namespace=namespace,
            function=function,
            env_file=env_vars,
        ) as context:
            context.start()
    except Exception as e:
        raise e
