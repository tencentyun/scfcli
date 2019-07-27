import click
import os
import sys
import time
from io import BytesIO

from tcfcli.help.message import DeployHelp as help
from tcfcli.common.template import Template
from tcfcli.common.user_exceptions import TemplateNotFoundException, InvalidTemplateException, ContextException
from tcfcli.common.user_exceptions import CloudAPIException
from tcfcli.libs.utils.scf_client import ScfClient
from tcfcli.common import tcsam
from tcfcli.common.user_config import UserConfig
from tcfcli.common.tcsam.tcsam_macro import TcSamMacro as tsmacro
from zipfile import ZipFile, ZIP_DEFLATED
from tcfcli.libs.utils.cos_client import CosClient

_CURRENT_DIR = '.'
_BUILD_DIR = './.tcf_build'
DEF_TMP_FILENAME = 'template.yaml'


@click.command(short_help=help.SHORT_HELP)
@click.option('--template-file', '-t', default=DEF_TMP_FILENAME, type=click.Path(exists=True), help=help.TEMPLATE_FILE)
@click.option('--cos-bucket', '-c', type=str, help=help.COS_BUCKET)
@click.option('--name', '-n', type=str, help=help.NAME)
@click.option('--namespace', '-ns', type=str, help=help.NAMESPACE)
@click.option('--region', '-r', type=str, help=help.REGION)
@click.option('--forced', '-f', is_flag=True, default=False, help=help.FORCED)
@click.option('--skip-event', is_flag=True, default=False, help=help.SKIP_EVENT)
def deploy(template_file, cos_bucket, name, namespace, region, forced, skip_event):
    '''
        \b
        Scf cli completes the function package deployment through the deploy subcommand. The scf command line tool deploys the code package, function configuration, and other information specified in the configuration file to the cloud or updates the functions of the cloud according to the specified function template configuration file.
        \b
        The execution of the scf deploy command is based on the function template configuration file. For the description and writing of the specific template file, please refer to the template file description.
            * https://cloud.tencent.com/document/product/583/33454
        \b
        Common usage:
            \b
            * Deploy the package
              $ scf deploy
            \b
            * Package the configuration file, and specify the COS bucket as "temp-code-1253970226"
              $ scf deploy --cos-bucket temp-code-1253970226
    '''

    package = Package(template_file, cos_bucket, name, region, namespace)
    resource = package.do_package()

    deploy = Deploy(resource, namespace, region, forced, skip_event)
    deploy.do_deploy()


class Package(object):

    def __init__(self, template_file, cos_bucket, function, region, deploy_namespace):
        self.template_file = template_file
        self.template_file_dir = ""
        self.cos_bucket = cos_bucket
        self.check_params()
        template_data = tcsam.tcsam_validate(Template.get_template_data(self.template_file))
        self.resource = template_data.get(tsmacro.Resources, {})
        self.function = function
        self.deploy_namespace = deploy_namespace
        self.region = region

    def do_package(self):
        for ns in self.resource:
            for func in list(self.resource[ns]):
                if func == tsmacro.Type:
                    continue

                if self.function is not None and func != self.function:
                    self.resource[ns].pop(func)
                    continue

                code_url = self._do_package_core(
                    self.resource[ns][func][tsmacro.Properties].get(tsmacro.CodeUri, ""),
                    ns,
                    func,
                    self.region
                )
                if "cos_bucket_name" in code_url:
                    self.resource[ns][func][tsmacro.Properties]["CosBucketName"] = code_url["cos_bucket_name"]
                    self.resource[ns][func][tsmacro.Properties]["CosObjectName"] = code_url["cos_object_name"]
                    click.secho("Upload function zip file '{}' to COS bucket '{}' success".
                                format(os.path.basename(code_url["cos_object_name"]),
                                       code_url["cos_bucket_name"]), fg="green")
                elif "zip_file" in code_url:
                    self.resource[ns][func][tsmacro.Properties]["LocalZipFile"] = code_url["zip_file"]

        # click.secho("Generate resource '{}' success".format(self.resource), fg="green")
        return self.resource

    def check_params(self):
        if not self.template_file:
            click.secho("FAM Template Not Found", fg="red")
            raise TemplateNotFoundException("Missing option --template-file")
        if not os.path.isfile(self.template_file):
            click.secho("FAM Template Not Found", fg="red")
            raise TemplateNotFoundException("template-file Not Found")

        self.template_file = os.path.abspath(self.template_file)
        self.template_file_dir = os.path.dirname(os.path.abspath(self.template_file))
        uc = UserConfig()
        if self.cos_bucket and self.cos_bucket.endswith("-" + uc.appid):
            self.cos_bucket = self.cos_bucket.replace("-" + uc.appid, '')

    def _do_package_core(self, func_path, namespace, func_name, region=None):
        zipfile, zip_file_name, zip_file_name_cos = self._zip_func(func_path, namespace, func_name)
        code_url = dict()

        if self.cos_bucket:
            CosClient(region).upload_file2cos(bucket=self.cos_bucket, file=zipfile.read(),
                                              key=zip_file_name_cos)
            code_url["cos_bucket_name"] = self.cos_bucket
            code_url["cos_object_name"] = "/" + zip_file_name_cos
        else:
            code_url["zip_file"] = os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name)

        return code_url

    def _zip_func(self, func_path, namespace, func_name):
        buff = BytesIO()
        if not os.path.exists(func_path):
            raise ContextException("Function file or path not found by CodeUri '{}'".format(func_path))

        if self.deploy_namespace and self.deploy_namespace != namespace:
            namespace = self.deploy_namespace

        zip_file_name = str(namespace) + '-' + str(func_name) + '-latest.zip'
        zip_file_name_cos = str(namespace) + '-' + str(func_name) + '-latest' + time.strftime(
            "-%Y-%m-%d-%H-%M-%S", time.localtime(int(time.time()))) + '.zip'
        cwd = os.getcwd()
        os.chdir(self.template_file_dir)
        os.chdir(func_path)

        with ZipFile(buff, mode='w', compression=ZIP_DEFLATED) as zip_object:
            for current_path, sub_folders, files_name in os.walk(_CURRENT_DIR):
                if current_path == _BUILD_DIR:
                    continue
                for file in files_name:
                    zip_object.write(os.path.join(current_path, file))

        os.chdir(cwd)
        buff.seek(0)
        buff.name = zip_file_name

        if not os.path.exists(_BUILD_DIR):
            os.mkdir(_BUILD_DIR)
        zip_file_path = os.path.join(_BUILD_DIR, zip_file_name)

        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)

        # a temporary support for upload func from local zipfile
        with open(zip_file_path, 'wb') as f:
            f.write(buff.read())
            buff.seek(0)
        click.secho("Compress function '{}' to zipfile '{}' success".format(zip_file_path, zip_file_name))

        return buff, zip_file_name, zip_file_name_cos


class Deploy(object):
    def __init__(self, resource, namespace, region=None, forced=False, skip_event=False):
        self.resources = resource
        self.namespace = namespace
        self.region = region
        self.forced = forced
        self.skip_event = skip_event

    def do_deploy(self):
        for ns in self.resources:
            if not self.resources[ns]:
                continue
            click.secho("Deploy namespace '{ns}' begin".format(ns=ns))
            for func in self.resources[ns]:
                if func == tsmacro.Type:
                    continue
                self._do_deploy_core(self.resources[ns][func], func, ns, self.region,
                                     self.forced, self.skip_event)
            click.secho("Deploy namespace '{ns}' end".format(ns=ns))

    def _do_deploy_core(self, func, func_name, func_ns, region, forced, skip_event=False):
        # check namespace exit, create namespace
        if self.namespace and self.namespace != func_ns:
            func_ns = self.namespace

        rep = ScfClient(region).get_ns(func_ns)
        if not rep:
            click.secho("{ns} not exists, create it now".format(ns=func_ns), fg="red")
            err = ScfClient(region).create_ns(func_ns)
            if err is not None:
                if sys.version_info[0] == 3:
                    s = err.get_message()
                else:
                    s = err.get_message().encode("UTF-8")
                click.secho("Create namespace '{name}' failure. Error: {e}.".format(
                    name=func_ns, e=s), fg="red")
                sys.exit(1)

        err = ScfClient(region).deploy_func(func, func_name, func_ns, forced)
        if err is not None:
            # if sys.version_info[0] == 3:
            s = err.get_message()
            # else:
            #    s = err.get_message().encode("UTF-8")
            if sys.version_info[0] == 2 and isinstance(s, str):
                s = s.encode("utf8")
            err_msg = u"Deploy function '{name}' failure, {e}.".format(name=func_name, e=s)

            if err.get_request_id():
                err_msg += (u"\nRequestId: {}".format(err.get_request_id().encode("UTF-8")))
            raise CloudAPIException(err_msg)

        click.secho("Deploy function '{name}' success".format(name=func_name), fg="green")
        if not skip_event:
            self._do_deploy_trigger(func, func_name, func_ns, region)

    def _do_deploy_trigger(self, func, func_name, func_ns, region=None):
        proper = func.get(tsmacro.Properties, {})
        events = proper.get(tsmacro.Events, {})
        hasError = None
        for trigger in events:
            err = ScfClient(region).deploy_trigger(events[trigger], trigger, func_name, func_ns)
            if err is not None:
                hasError = err
                if sys.version_info[0] == 3:
                    s = err.get_message()
                else:
                    s = err.get_message().encode("UTF-8")

                click.secho(
                    "Deploy trigger '{name}' failure. Error: {e}.".format(name=trigger,
                                                                          e=s), fg="red")
                if err.get_request_id():
                    click.secho("RequestId: {}".format(err.get_request_id().encode("UTF-8")), fg="red")
                continue
            click.secho("Deploy trigger '{name}' success".format(name=trigger), fg="green")
        if hasError is not None:
            sys.exit(1)
