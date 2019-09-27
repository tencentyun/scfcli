# -*- coding: utf-8 -*-

import os
import zipfile
import traceback
from tcfcli.common.operation_msg import Operation
from tcfcli.common.user_exceptions import *
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
    def _runtime_format_vaild(runtime):
        if runtime.lower() not in list(Init.RUNTIMES.keys()):
            raise InitException("runtime {runtime} not support".format(runtime=runtime))
        return runtime.lower()

    @staticmethod
    def _type_format_vaild(type):
        type_map = {"event": "Event", "http": "HTTP"}
        if type.lower() not in list(type_map.keys()):
            raise InitException("type {type} not support".format(runtime=type))
        return type_map[type.lower()]

    @staticmethod
    def do_cli(location, runtime, output_dir, name, namespace, no_input, type):

        Operation('''      _____  ______ ______ ______ __     ____
     / ___/ / ____// ____// ____// /    /  _/
     \__ \ / /    / /_   / /    / /     / /  
    ___/ // /___ / __/  / /___ / /___ _/ /   
   /____/ \____//_/     \____//_____//___/ ''').echo()

        Operation("[+] Initializing project...", fg="green").echo()
        params = {
            "template": location if location else Init._runtime_path(runtime),
            "output_dir": output_dir,
            "no_input": no_input,
        }
        Operation("Template: %s" % params["template"]).process()
        Operation("Output-Dir: %s" % params["output_dir"]).process()
        if name is not None:
            params["no_input"] = True
            params['extra_context'] = {'project_name': name, 'runtime': runtime, 'namespace': namespace, 'type': type}
            Operation("Project-Name: %s" % params['extra_context']["project_name"]).process()
            Operation("Type: %s" % params['extra_context']["type"]).process()
            Operation("Runtime: %s" % params['extra_context']["runtime"]).process()
        try:
            cookiecutter(**params)
        except exceptions.CookiecutterException as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            # raise click.Abort()
            raise InitException(e)
        if runtime in infor.SERVICE_RUNTIME:
            Operation("[*] Project initing,please wait.....", fg="green").echo()
            zipfile_path = os.path.join(os.path.abspath(output_dir), name, 'node_modules.zip')
            zipobj = zipfile.ZipFile(zipfile_path, mode="r")
            zipobj.extractall(os.path.join(os.path.abspath(output_dir), name))
            zipobj.close()
            os.remove(zipfile_path)
        Operation("[*] Project initialization is complete", fg="green").echo()
        Operation(
            "You could 'cd %s', and start this project." % (params['extra_context']["project_name"])).information()


@click.command(short_help=help.SHORT_HELP)
@click.option('-l', '--location', help=help.LOCATION)
@click.option('-r', '--runtime', type=str, default="python3.6", help=help.RUNTIME)
@click.option('-o', '--output-dir', default='.', type=click.Path(), help=help.OUTPUT_DIR)
@click.option('-n', '--name', default="hello_world", help=help.NAME)
@click.option('-ns', '--namespace', default="default", help=help.NAMESPACE)
@click.option('-N', '--no-input', is_flag=True, help=help.NO_INPUT)
# @click.option('--type', default='Event', help=help.TYPE)
@click.option('--no-color', '-nc', is_flag=True, default=False, help=help.NOCOLOR)
def init(location, runtime, output_dir, name, namespace, no_input, no_color, type='Event'):
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


    runtime = Init._runtime_format_vaild(runtime)
    type = Init._type_format_vaild(type)
    if runtime not in TYPE_SUPPORT_RUNTIME[type]:
        # raise InitException("{type} not support runtime: {runtime}".format(type=type, runtime=runtime))
        raise InitException("not support runtime: {runtime}".format(runtime=runtime))
        # return
    Init.do_cli(location, runtime, output_dir, name, namespace, no_input, type)
