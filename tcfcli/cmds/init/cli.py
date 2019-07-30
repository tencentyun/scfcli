import os
import click
from cookiecutter.main import cookiecutter
from cookiecutter import exceptions
from tcfcli.help.message import InitHelp as help
import tcfcli.common.base_infor as infor

TYPE = infor.FUNCTION_TYPE
EVENT_RUNTIME_SUPPORT_LIST = infor.EVENT_RUNTIME
HTTP_RUNTIME_SUPPORT_LIST = infor.HTTP_RUNTIME
TYPE_SUPPORT_RUNTIME = {
    'Event': EVENT_RUNTIME_SUPPORT_LIST,
    'HTTP': HTTP_RUNTIME_SUPPORT_LIST
}


class Init(object):
    TEMPLATES_DIR = "templates"
    RUNTIMES = {
        "python3.6": "tcf-demo-python",
        "python2.7": "tcf-demo-python",
        "go1": "tcf-demo-go1",
        "php5": "tcf-demo-php",
        "php7": "tcf-demo-php",
        "nodejs6.10": "tcf-demo-nodejs6.10",
        "nodejs8.9": "tcf-demo-nodejs8.9",
        "nodejs8.9-service": "tcf-demo-nodejs8.9-service"
        # "java8": "gh:tencentyun/tcf-demo-java8"
    }

    @staticmethod
    def _runtime_path(runtime):
        pwd = os.path.dirname(os.path.abspath(__file__))
        runtime_pro = Init.RUNTIMES[runtime]
        return os.path.join(pwd, Init.TEMPLATES_DIR, runtime_pro)

    @staticmethod
    def do_cli(location, runtime, output_dir, name, namespace, no_input, type):

        click.secho("[+] Initializing project...", fg="green")
        params = {
            "template": location if location else Init._runtime_path(runtime),
            "output_dir": output_dir,
            "no_input": no_input,
        }
        click.secho("Template: %s" % params["template"])
        click.secho("Output-Dir: %s" % params["output_dir"])
        if name is not None:
            params["no_input"] = True
            params['extra_context'] = {'project_name': name, 'runtime': runtime, 'namespace': namespace, 'type': type}
            click.secho("Project-Name: %s" % params['extra_context']["project_name"])
            click.secho("Type: %s" % params['extra_context']["type"])
            click.secho("Runtime: %s" % params['extra_context']["runtime"])

        try:
            cookiecutter(**params)
        except exceptions.CookiecutterException as e:
            click.secho(str(e), fg="red")
            raise click.Abort()
        click.secho("[*] Project initialization is complete", fg="green")


@click.command(short_help=help.SHORT_HELP)
@click.option('-l', '--location', help=help.LOCATION)
@click.option('-r', '--runtime', type=str, default="python3.6", help=help.RUNTIME)
@click.option('-o', '--output-dir', default='.', type=click.Path(), help=help.OUTPUT_DIR)
@click.option('-n', '--name', default="hello_world", help=help.NAME)
@click.option('-ns', '--namespace', default="default", help=help.NAMESPACE)
@click.option('-N', '--no-input', is_flag=True, help=help.NO_INPUT)
@click.option('--type', default='Event', type=click.Choice(TYPE), help=help.TYPE)
def init(location, runtime, output_dir, name, namespace, no_input, type):
    """
        \b
        The project initialization operation is performed by the scf init command.
        \b
        Common usage:
            \b
          * Initializes a new scf using Python 3.6 default template runtime
            $ scf init --runtime python3.6
            \b
          * Initializes a new scf project using custom template in a Git repository
            $ scf init --location gh:pass/demo-python
    """
    if runtime not in TYPE_SUPPORT_RUNTIME[type]:
        click.secho("{type} not support runtime: {runtime}".format(type=type, runtime=runtime), fg="red")
        return
    Init.do_cli(location, runtime, output_dir, name, namespace, no_input, type)
