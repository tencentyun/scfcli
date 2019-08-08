# -*- coding: utf-8 -*-

import os
import sys
import time
import re
import json
import click
from io import BytesIO
import shutil
import hashlib

import tcfcli.common.base_infor as infor
from tcfcli.help.message import DeployHelp as help
from tcfcli.common.operation_msg import Operation
from tcfcli.common.template import Template
from tcfcli.common.user_exceptions import *
from tcfcli.libs.utils.scf_client import ScfClient
from tcfcli.common import tcsam
from tcfcli.common.user_config import UserConfig
from tcfcli.common.tcsam.tcsam_macro import TcSamMacro as tsmacro
from zipfile import ZipFile, ZIP_DEFLATED
from tcfcli.libs.utils.cos_client import CosClient

_CURRENT_DIR = '.'
_BUILD_DIR = os.path.join(os.getcwd(), '.tcf_build')
DEF_TMP_FILENAME = 'template.yaml'

REGIONS = infor.REGIONS
SERVICE_RUNTIME = infor.SERVICE_RUNTIME


@click.command(short_help=help.SHORT_HELP)
@click.option('--template-file', '-t', default=DEF_TMP_FILENAME, type=click.Path(exists=True), help=help.TEMPLATE_FILE)
@click.option('--cos-bucket', '-c', type=str, help=help.COS_BUCKET)
@click.option('--name', '-n', type=str, help=help.NAME)
@click.option('--namespace', '-ns', type=str, help=help.NAMESPACE)
@click.option('--region', '-r', type=str, help=help.REGION)
@click.option('--forced', '-f', is_flag=True, default=False, help=help.FORCED)
@click.option('--skip-event', is_flag=True, default=False, help=help.SKIP_EVENT)
@click.option('--without-cos', is_flag=True, default=False, help=help.WITHOUT_COS)
@click.option('--history', is_flag=True, default=False, help=help.HISTORY)
def deploy(template_file, cos_bucket, name, namespace, region, forced, skip_event, without_cos, history):
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

    if region and region not in REGIONS:
        raise ArgsException("The region must in %s." % (", ".join(REGIONS)))
    else:
        region = region if region else UserConfig().region
        if history:
            package = Package(template_file, cos_bucket, name, region, namespace, without_cos, history)
            resource = package.do_package()
        else:
            package = Package(template_file, cos_bucket, name, region, namespace, without_cos)
            resource = package.do_package()
        if resource == None:
            return
        if name and "'%s'" % str(name) not in str(resource):
            raise DeployException("Couldn't find the function in YAML, please add this function in YAML.")
        else:
            deploy = Deploy(resource, namespace, region, forced, skip_event)
            deploy.do_deploy()
            Operation("Deploy success").success()

        try:
            shutil.rmtree(_BUILD_DIR)
        except Exception as e:
            pass


class Function(object):
    def __init__(self, region, namespace, function, resources):
        self.region = region if region else UserConfig().region
        self.namespace = namespace
        self.function = function
        self.resources = resources

    def recursion_dict(self, information, num):
        for eveKey, eveValue in information.items():
            try:
                eveValue = json.loads(eveValue)
            except:
                pass
            finally:
                if isinstance(eveValue, dict):
                    Operation(" " * num + "%s:" % (str(eveKey))).out_infor()
                    self.recursion_dict(eveValue, num + 2)
                else:
                    Operation(" " * num + "%s: %s" % (str(eveKey), str(eveValue))).out_infor()

    def format_information(self, information):
        click.secho(u"[+] Function Base Information: ", fg="cyan")
        Operation("Name: %s" % self.function).out_infor()
        Operation("Version: %s" % information["FunctionVersion"]).out_infor()
        Operation("Status: %s" % information["Status"]).out_infor()
        Operation("FunctionId: %s" % information["FunctionId"]).out_infor()
        Operation("Region: %s" % self.region).out_infor()
        Operation("Namespace: %s" % information["Namespace"]).out_infor()
        Operation("MemorySize: %d" % information["MemorySize"]).out_infor()
        Operation("Runtime: %s" % information["Runtime"]).out_infor()
        Operation("Timeout: %d" % information["Timeout"]).out_infor()
        Operation("Handler: %s" % information["Handler"]).out_infor()
        serviceid_list = []
        if information["Triggers"]:
            click.secho(u"[+] Trigger Information: ", fg="cyan")
            for eve_trigger in information["Triggers"]:
                try:
                    if eve_trigger['Type'] == 'apigw':
                        serviceid_list.append(json.loads(eve_trigger['TriggerDesc'])["service"]["serviceId"])
                except Exception as e:
                    pass
                click.secho(click.style(u"    > %s - %s:" % (text(str(eve_trigger["Type"]).upper()),
                                                             text(eve_trigger["TriggerName"]))), fg="cyan")
                self.recursion_dict(eve_trigger, 2)

        function = self.resources[self.namespace][self.function]
        proper = function.get(tsmacro.Properties, {})
        events = proper.get(tsmacro.Events, {})
        temp_list = []

        for eve_event in events:
            if "ServiceId" in events[eve_event]['Properties']:
                temp_list.append(events[eve_event]['Properties']["ServiceId"])

        id_list = []
        for eve_service_id in serviceid_list:
            if eve_service_id not in temp_list:
                id_list.append(eve_service_id)

        if id_list:
            Operation("If you don't want to create the new gateway next time.").information()
            Operation("Please add these ServiceId into the YAML: " + ", ".join(id_list)).information()

    def get_information(self):
        scf_client = ScfClient(region=self.region)
        result = scf_client.get_function(namespace=self.namespace, function_name=self.function)
        if result:
            self.format_information(json.loads(result))


class Package(object):

    def __init__(self, template_file, cos_bucket, function, region, deploy_namespace, without_cos, history=None):
        self.template_file = template_file
        self.template_file_dir = ""
        self.cos_bucket = cos_bucket
        self.check_params()
        template_data = tcsam.tcsam_validate(Template.get_template_data(self.template_file))
        self.resource = template_data.get(tsmacro.Resources, {})
        self.function = function
        self.deploy_namespace = deploy_namespace
        self.region = region
        self.without_cos = without_cos
        self.history = history

    def do_package(self):
        region = self.region
        for ns in self.resource:
            for func in list(self.resource[ns]):
                if func == tsmacro.Type:
                    continue

                if self.function is not None and func != self.function:
                    self.resource[ns].pop(func)
                    continue

                if self.history:
                    function_list = CosClient(self.region).get_object_list(
                        bucket="scf-deploy-" + region,
                        prefix=str(ns) + "-" + str(func)
                    )

                    if isinstance(function_list, dict) and 'Contents' in function_list:
                        rollback_dict = {}
                        function_list_data = function_list['Contents']
                        if function_list_data:
                            click.secho(
                                "[+] Please select a historical deployment Number for the historical version deployment.",
                                fg="cyan")
                            i = 0
                            for eve_obj in reversed(function_list_data):
                                i = i + 1
                                if i > 15:
                                    break
                                click.secho("  [%s] %s" % (
                                    i, text(eve_obj["LastModified"].replace(".000Z", "").replace("T", " "))), fg="cyan")
                                rollback_dict[str(i)] = eve_obj["Key"]
                            number = click.prompt(click.style("Please input number(Like: 1)", fg="cyan"))
                            if number not in rollback_dict:
                                raise RollbackException(
                                    "Please enter the version number correctly, for example the number 1.")
                            else:
                                code_url = {
                                    'cos_bucket_name': "scf-deploy-" + region,
                                    'cos_object_name': rollback_dict[number]
                                }
                                msg = "Select function zip file '{}' on COS bucket '{}' success.".format(
                                    os.path.basename( \
                                        code_url["cos_object_name"]), code_url["cos_bucket_name"])
                                Operation(msg).success()
                        else:
                            raise RollbackException(
                                "The historical version is not queried. The deployment history version code only takes effect when you use using-cos.")
                    else:
                        raise RollbackException(
                            "The historical version is not queried. The deployment history version code only takes effect when you use using-cos.")

                else:
                    code_url = self._do_package_core(
                        self.resource[ns][func][tsmacro.Properties].get(tsmacro.CodeUri, ""),
                        ns,
                        func,
                        self.region
                    )

                if "cos_bucket_name" in code_url:
                    self.resource[ns][func][tsmacro.Properties]["CosBucketName"] = code_url["cos_bucket_name"]
                    self.resource[ns][func][tsmacro.Properties]["CosObjectName"] = code_url["cos_object_name"]
                elif "zip_file" in code_url:
                    # if self.resource[ns][func][tsmacro.Properties][tsmacro.Runtime][0:].lower() in SERVICE_RUNTIME:
                    # error = "Service just support cos to deploy, please set using-cos by 'scf configure set --using-cos y'"
                    # raise UploadFailed(error)
                    self.resource[ns][func][tsmacro.Properties]["LocalZipFile"] = code_url["zip_file"]

        # click.secho("Generate resource '{}' success".format(self.resource), fg="green")
        return self.resource

    def check_params(self):
        if not self.template_file:
            # click.secho("FAM Template Not Found", fg="red")
            raise TemplateNotFoundException("FAM Template Not Found. Missing option --template-file")
        if not os.path.isfile(self.template_file):
            # click.secho("FAM Template Not Found", fg="red")
            raise TemplateNotFoundException("FAM Template Not Found, template-file Not Found")

        self.template_file = os.path.abspath(self.template_file)
        self.template_file_dir = os.path.dirname(os.path.abspath(self.template_file))

        uc = UserConfig()
        if self.cos_bucket and self.cos_bucket.endswith("-" + uc.appid):
            self.cos_bucket = self.cos_bucket.replace("-" + uc.appid, '')

    def file_size_infor(self, size):
        # click.secho(str(size))
        if size >= 20 * 1024 * 1024:
            Operation('Your package is too large and needs to be uploaded via COS.').warning()
            Operation(
                'You can use --cos-bucket BucketName to specify the bucket, or you can use the "scf configure set" to set the default to open the cos upload.').warning()
            raise UploadFailed("Upload faild")
        elif size >= 8 * 1024 * 1024:
            Operation("Package size is over 8M, it is highly recommended that you upload using COS. ").information()
            return

    def _do_package_core(self, func_path, namespace, func_name, region=None):

        zipfile, zip_file_name, zip_file_name_cos = self._zip_func(func_path, namespace, func_name)
        code_url = dict()

        file_size = os.path.getsize(os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name))
        Operation("Package name: %s, package size: %s kb" % (zip_file_name, str(file_size / 1000))).process()

        default_bucket_name = ""
        if UserConfig().using_cos.startswith("True"):
            cos_bucket_status = True
            default_bucket_name = "scf-deploy-" + region + "-" + str(UserConfig().appid)
        else:
            cos_bucket_status = False

        if self.without_cos:
            self.file_size_infor(file_size)
            Operation("Uploading this package without COS.").process()
            code_url["zip_file"] = os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name)
            Operation("Upload success").success()

        elif self.cos_bucket:
            bucket_name = self.cos_bucket + "-" + UserConfig().appid
            Operation("Uploading this package to COS, bucket_name: %s" % (bucket_name)).process()
            CosClient(region).upload_file2cos(bucket=self.cos_bucket, file=zipfile.read(), key=zip_file_name_cos)
            Operation("Upload success").success()
            code_url["cos_bucket_name"] = self.cos_bucket
            code_url["cos_object_name"] = "/" + zip_file_name_cos
            msg = "Upload function zip file '{}' to COS bucket '{}' success.".format(os.path.basename( \
                code_url["cos_object_name"]), code_url["cos_bucket_name"])
            Operation(msg).success()
        elif cos_bucket_status:

            Operation("By default, this package will be uploaded to COS.").information()
            Operation("Default COS-bucket: " + default_bucket_name).information()
            Operation("If you don't want to upload the package to COS by default, you could change your configure!") \
                .information()

            # 根据region设置cos_client
            cos_client = CosClient(region)
            Operation("Checking you COS-bucket.").process()
            # 获取COS bucket
            cos_bucket_status = cos_client.get_bucket(default_bucket_name)

            if cos_bucket_status == -1:
                Operation("reating default COS-bucket: " + default_bucket_name).process()
                create_status = cos_client.create_bucket(bucket=default_bucket_name)
                if create_status == True:
                    cos_bucket_status = 0
                    Operation("Creating success.").success()
                else:
                    try:
                        if "<?xml" in str(create_status):
                            error_code = re.findall("<Code>(.*?)</Code>", str(create_status))[0]
                            error_message = re.findall("<Message>(.*?)</Message>", str(create_status))[0]
                            Operation("COS client error code: %s, message: %s" % (error_code, error_message)).warning()
                    finally:
                        cos_bucket_status = create_status
                        Operation("Creating faild.").warning()

            if cos_bucket_status != 0:

                Operation("There are some exceptions and the process of uploading to COS is terminated!").warning()
                Operation("This package will be uploaded by TencentCloud Cloud API.").information()
                Operation("Uploading this package.").process()
                code_url["zip_file"] = os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name)
                Operation("Upload success").success()

            else:
                # 获取bucket正常，继续流程

                file_data = zipfile.read()
                md5 = hashlib.md5(file_data).hexdigest()
                is_have = 0

                try:
                    object_list = cos_client.get_object_list(
                        bucket=default_bucket_name,
                        prefix=str(namespace) + "-" + str(func_name)
                    )
                    if isinstance(object_list, dict) and 'Contents' in object_list:
                        for eve_object in object_list["Contents"]:
                            if md5 in eve_object["ETag"]:
                                response = cos_client.copy_object(
                                    default_bucket_name,
                                    eve_object["Key"],
                                    zip_file_name_cos, )
                                is_have = 1
                                break
                except Exception as e:
                    pass

                if is_have == 0:
                    Operation("Uploading to COS, bucket_name:" + default_bucket_name).process()
                    cos_client.upload_file2cos(
                        bucket=default_bucket_name,
                        file=file_data,
                        key=zip_file_name_cos
                    )
                    # cos_client.upload_file2cos2(
                    #     bucket=default_bucket_name,
                    #     file=os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name),
                    #     key=zip_file_name_cos,
                    #     md5=md5,
                    # )

                code_url["cos_bucket_name"] = default_bucket_name.replace("-" + UserConfig().appid, '') \
                    if default_bucket_name and default_bucket_name.endswith(
                    "-" + UserConfig().appid) else default_bucket_name
                code_url["cos_object_name"] = "/" + zip_file_name_cos

            msg = "Upload function zip file '{}' to COS bucket '{}' success.".format(os.path.basename( \
                code_url["cos_object_name"]), code_url["cos_bucket_name"])
            Operation(msg).success()

        else:
            Operation( \
                "If you want to increase the upload speed, you can configure using-cos with command：scf configure set") \
                .information()

            self.file_size_infor(file_size)

            Operation("Uploading this package.").process()
            code_url["zip_file"] = os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name)
            Operation("Upload success").success()

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

        zip_file_path = os.path.join(_BUILD_DIR, zip_file_name)

        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)

        try:
            try:
                os.mkdir(_BUILD_DIR)
            except:
                pass

            if os.path.isdir(func_path):
                os.chdir(func_path)
                with ZipFile(buff, mode='w', compression=ZIP_DEFLATED) as zip_object:
                    for current_path, sub_folders, files_name in os.walk(_CURRENT_DIR):
                        # click.secho(str(current_path))
                        if not str(current_path).startswith("./.") and not str(current_path).startswith(r".\."):
                            for file in files_name:
                                zip_object.write(os.path.join(current_path, file))

                os.chdir(cwd)
                buff.seek(0)
                buff.name = zip_file_name

                if not os.path.exists(_BUILD_DIR):
                    os.mkdir(_BUILD_DIR)

                # a temporary support for upload func from local zipfile
                with open(zip_file_path, 'wb') as f:
                    f.write(buff.read())
                    buff.seek(0)

            else:
                if str(func_path).endswith(".zip"):
                    with open(func_path, "rb") as f:
                        buff.write(f.read())

                    buff.seek(0)
                    buff.name = zip_file_name

                else:

                    with ZipFile(buff, mode='w', compression=ZIP_DEFLATED) as zip_object:
                        zip_object.write(func_path)

                    os.chdir(cwd)
                    buff.seek(0)
                    buff.name = zip_file_name

            # print(zip_file_path)

            # a temporary support for upload func from local zipfile
            with open(zip_file_path, 'wb') as f:
                f.write(buff.read())
                buff.seek(0)
        except Exception as e:
            raise PackageException("Package Error. Please check CodeUri in YAML.")
        Operation("Compress function '{}' to zipfile '{}' success".format(zip_file_path, zip_file_name)).success()

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
            ns_this = ns
            if self.namespace and self.namespace != ns:
                ns_this = self.namespace
            Operation("Deploy namespace '{ns}' begin".format(ns=ns_this)).process()
            for func in self.resources[ns]:
                if func == tsmacro.Type:
                    continue
                self._do_deploy_core(self.resources[ns][func], func, ns, self.region,
                                     self.forced, self.skip_event)
                Function(self.region, ns, func, self.resources).get_information()
            Operation("Deploy namespace '{ns}' end".format(ns=ns_this)).success()

    def _do_deploy_core(self, func, func_name, func_ns, region, forced, skip_event=False):
        # check namespace exit, create namespace
        if self.namespace and self.namespace != func_ns:
            func_ns = self.namespace

        rep = ScfClient(region).get_ns(func_ns)
        if not rep:
            Operation("{ns} not exists, create it now".format(ns=func_ns)).process()
            err = ScfClient(region).create_ns(func_ns)
            if err is not None:
                if sys.version_info[0] == 3:
                    s = err.get_message()
                else:
                    s = err.get_message().encode("UTF-8")
                raise NamespaceException("Create namespace '{name}' failure. Error: {e}.".format(name=func_ns, e=s))

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
                err_msg += (u" RequestId: {}".format(err.get_request_id()))
            raise CloudAPIException(err_msg)

        Operation("Deploy function '{name}' success".format(name=func_name)).success()
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
                if "Param error The path+method already exists under the service" not in str(s):
                    if err.get_request_id():
                        Operation("Deploy trigger '{name}' failure. Error: {e}. RequestId: {id}".
                                  format(name=trigger, e=s, id=err.get_request_id())).warning()
                    else:
                        Operation("Deploy trigger '{name}' failure. Error: {e}.".format(name=trigger, e=s, )).warning()
                continue
            Operation("Deploy trigger '{name}' success".format(name=trigger)).success()
        # if hasError is not None:
        #     sys.exit(1)
