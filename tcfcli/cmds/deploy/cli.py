# -*- coding: utf-8 -*-

import os
import sys
import time
import re
import json
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
@click.option('--update-event', '-ue', is_flag=True, default=False, help=help.UPDATE_EVENT)
def deploy(template_file, cos_bucket, name, namespace, region, forced, skip_event, without_cos, history, update_event):
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
            \b
            * Deploy history package
              $ scf deploy --history
            \b
            * Upgrade the function and urgrade events
              $ scf deploy -f -ue
    '''

    if region and region not in REGIONS:
        raise ArgsException("The region must in %s." % (", ".join(REGIONS)))
    region = region if region else UserConfig().region
    package = Package(template_file, cos_bucket, name, region, namespace, without_cos, history)
    resource = package.do_package()

    if resource == None:
        return

    if name and "'%s'" % str(name) not in str(resource):
        raise DeployException("Couldn't find the function in YAML, please add this function in YAML.")
    else:
        deploy = Deploy(resource, namespace, region, forced, skip_event, update_event)
        deploy.do_deploy()
        Operation("Deploy success").success()

        # delete package dir
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

    def get_information(self):
        scf_client = ScfClient(region=self.region)
        result = scf_client.get_function(namespace=self.namespace, function_name=self.function)
        return result

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

    def format_information(self):
        result = self.get_information()
        if result:
            information = json.loads(result)
            click.secho(u"[+] Function Base Information: ", fg="cyan")
            Operation("Name: %s" % self.function).out_infor()
            Operation("Version: %s" % information["FunctionVersion"]).out_infor()
            Operation("Status: %s" % information["Status"]).out_infor()
            Operation("FunctionId: %s" % information["FunctionId"]).out_infor()
            Operation("Region: %s" % self.region).out_infor()
            Operation("Namespace: %s" % information["Namespace"]).out_infor()
            Operation("Runtime: %s" % information["Runtime"]).out_infor()

            release_serviceid_list = []
            if information["Triggers"]:
                click.secho(u"[+] Trigger Information: ", fg="cyan")
                for eve_trigger in information["Triggers"]:
                    trigger_type = eve_trigger['Type']

                    # release apigateway service_id list
                    try:
                        if trigger_type == 'apigw':
                            release_serviceid_list.append(
                                json.loads(eve_trigger['TriggerDesc'])["service"]["serviceId"])
                    except Exception as e:
                        pass

                    msg = u"    > %s - %s:" % (text(trigger_type).upper(), text(eve_trigger["TriggerName"]))
                    click.secho(click.style(msg), fg="cyan")
                    self.recursion_dict(eve_trigger, 2)

            # yaml apigateway service_id list
            function = self.resources[self.namespace][self.function]
            proper = function.get(tsmacro.Properties, {})
            events = proper.get(tsmacro.Events, {})

            yaml_serviceid_list = []
            for eve_event in events:
                if "ServiceId" in events[eve_event]['Properties']:
                    yaml_serviceid_list.append(events[eve_event]['Properties']["ServiceId"])

            remind_serviceid_list = []
            for eve_service_id in release_serviceid_list:
                if eve_service_id not in yaml_serviceid_list:
                    remind_serviceid_list.append(eve_service_id)

            if remind_serviceid_list:
                Operation("If you don't want to create the new gateway next time.").information()
                Operation("Please add these ServiceId into the YAML: " + ", ".join(remind_serviceid_list)).information()

    def get_function_trigger(self):
        try:
            result = self.get_information()
            if result:
                information = json.loads(result)
                function_runtime = information["Runtime"]

                trigger = {"apigw": [], "timer": [], "cos": [], "cmq": [], "ckafka": []}
                for eve_trigger in information["Triggers"]:
                    try:
                        trigger_desc = json.loads(eve_trigger['TriggerDesc'])
                        if eve_trigger['Type'] == "timer":
                            trigger[eve_trigger['Type']].append({
                                'Type': 'Timer',
                                'Properties': {
                                    'CronExpression': trigger_desc['cron'],
                                    'Enable': True if eve_trigger['Enable'] == 1 else False
                                },
                                'TriggerName': eve_trigger['TriggerName'],
                                "TriggerDesc": trigger_desc,
                            })
                        elif eve_trigger['Type'] == "apigw":
                            trigger[eve_trigger['Type']].append({
                                'TriggerName': eve_trigger['TriggerName'],
                                'Type': 'APIGW',
                                'Properties': {
                                    'StageName': trigger_desc["release"]["environmentName"],
                                    'ServiceId': trigger_desc['service']['serviceId'],
                                    'HttpMethod': trigger_desc["api"]["requestConfig"]["method"],
                                },
                                "TriggerDesc": trigger_desc
                            })
                        elif eve_trigger['Type'] == "ckafka":
                            temp_list = str(eve_trigger['TriggerName']).split("-")
                            name = "-".join(temp_list[0:2])
                            topic = "-".join(temp_list[2:])
                            trigger_desc = json.loads(trigger_desc)
                            trigger[eve_trigger['Type']].append({
                                'TriggerName': eve_trigger['TriggerName'],
                                'Type': 'APIGW',
                                'Properties': {
                                    'Name': name,
                                    'Topic': topic,
                                    'MaxMsgNum': trigger_desc["maxMsgNum"],
                                    'Offset': trigger_desc["offset"],
                                    'Enable': True if eve_trigger['Enable'] == 1 else False,
                                },
                                "TriggerDesc": trigger_desc
                            })
                        elif eve_trigger['Type'] == "cos":
                            trigger[eve_trigger['Type']].append({
                                'TriggerName': eve_trigger['TriggerName'],
                                'Type': 'COS',
                                'Properties': {
                                    'Bucket': eve_trigger['TriggerName'],
                                    'Events': trigger_desc["event"],
                                    'Filter': {
                                        'Prefix': trigger_desc["filter"]["Prefix"],
                                        'Suffix': trigger_desc["filter"]["Suffix"],
                                    },
                                    'Enable': True if eve_trigger['Enable'] == 1 else False,
                                },
                                "TriggerDesc": trigger_desc
                            })
                        elif eve_trigger['Type'] == "cmq":
                            trigger[eve_trigger['Type']].append({
                                'TriggerName': eve_trigger['TriggerName'],
                                'Type': 'CMQ',
                                'Properties': {
                                    'Name': eve_trigger['TriggerName'],
                                },
                                "TriggerDesc": trigger_desc
                            })

                    except Exception as e:
                        pass
                return (function_runtime, trigger)
        except:
            pass

        return None


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
        self.bucket_name = "scf-deploy-" + self.region

    def do_package(self):
        for namespace in self.resource:
            for function in list(self.resource[namespace]):

                if function == tsmacro.Type:
                    continue

                if self.function is not None and function != self.function:
                    self.resource[namespace].pop(function)
                    continue

                if self.history:

                    cos_function = CosClient(self.region).get_object_list(
                        bucket=self.bucket_name,
                        prefix=str(namespace) + "-" + str(function)
                    )

                    if isinstance(cos_function, dict) and 'Contents' in cos_function:
                        rollback_dict = {}
                        cos_function_list = cos_function['Contents']
                        if cos_function_list:
                            msg = "[+] Please select a historical deployment Number for the historical version deployment."
                            click.secho(msg, fg="cyan")
                            function_number = 0
                            for eve_function in reversed(cos_function_list):
                                function_number = function_number + 1
                                if function_number > 15:
                                    break
                                else:
                                    function_name = eve_function["LastModified"].replace(".000Z", "").replace("T", " ")
                                    msg = "  [%s] %s" % (function_number, text(function_name))
                                    click.secho(msg, fg="cyan")
                                    rollback_dict[str(function_number)] = eve_function["Key"]

                            number = click.prompt(click.style("Please input number(Like: 1)", fg="cyan"))
                            if number not in rollback_dict:
                                err_msg = "Please enter the version number correctly, for example the number 1."
                                raise RollbackException(err_msg)
                            else:
                                code_url = {
                                    'cos_bucket_name': "scf-deploy-" + self.region,
                                    'cos_object_name': rollback_dict[number]
                                }
                                msg = "Select function zip file '{}' on COS bucket '{}' success.".format(
                                    os.path.basename(code_url["cos_object_name"]), code_url["cos_bucket_name"])
                                Operation(msg).success()
                        else:
                            err_msg = "The historical version is not queried. The deployment history version code only takes effect when you use using-cos."
                            raise RollbackException(err_msg)
                    else:
                        err_msg = "The historical version is not queried. The deployment history version code only takes effect when you use using-cos."
                        raise RollbackException(err_msg)

                else:
                    code_url = self._do_package_core(
                        self.resource[namespace][function][tsmacro.Properties].get(tsmacro.CodeUri, ""),
                        namespace,
                        function,
                        self.region
                    )

                if "cos_bucket_name" in code_url:
                    bucket_name = code_url["cos_bucket_name"]
                    object_name = code_url["cos_object_name"]
                    self.resource[namespace][function][tsmacro.Properties]["CosBucketName"] = bucket_name
                    self.resource[namespace][function][tsmacro.Properties]["CosObjectName"] = object_name
                elif "zip_file" in code_url:
                    self.resource[namespace][function][tsmacro.Properties]["LocalZipFile"] = code_url["zip_file"]

        return self.resource

    def check_params(self):
        if not self.template_file:
            raise TemplateNotFoundException("FAM Template Not Found. Missing option --template-file")
        if not os.path.isfile(self.template_file):
            raise TemplateNotFoundException("FAM Template Not Found, template-file Not Found")

        self.template_file = os.path.abspath(self.template_file)
        self.template_file_dir = os.path.dirname(os.path.abspath(self.template_file))

        uc = UserConfig()
        if self.cos_bucket and self.cos_bucket.endswith("-" + uc.appid):
            self.cos_bucket = self.cos_bucket.replace("-" + uc.appid, '')

    def file_size_infor(self, size):
        '''
        :param size: file size
        :return:  0: could upload and remind
                  1: could upload
                 -1: raise
        '''
        if size >= 20 * 1024 * 1024:
            return -1
        elif size >= 8 * 1024 * 1024:
            return 0
        else:
            return 1

    def _do_package_core(self, func_path, namespace, func_name, region=None):

        zipfile, zip_file_name, zip_file_name_cos = self._zip_func(func_path, namespace, func_name)
        code_url = dict()

        file_size = os.path.getsize(os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name))
        Operation("Package name: %s, package size: %s kb" % (zip_file_name, str(file_size / 1000))).process()

        default_bucket_name = ""
        if UserConfig().using_cos.startswith("True"):
            using_cos = True
            default_bucket_name = "scf-deploy-" + region + "-" + str(UserConfig().appid)
        else:
            using_cos = False

        if self.without_cos:
            size_infor = self.file_size_infor(file_size)
            if size_infor == -1:
                msg = 'Your package is too large and needs to be uploaded via COS.'
                Operation(msg).warning()
                msg = 'You can use --cos-bucket BucketName to specify the bucket, or you can use the "scf configure set" to set the default to open the cos upload.'
                Operation(msg).warning()
                raise UploadFailed("Upload faild")
            elif size_infor == 0:
                Operation("Package size is over 8M, it is highly recommended that you upload using COS. ").information()
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

        elif using_cos:

            Operation("By default, this package will be uploaded to COS.").information()
            Operation("Default COS-bucket: " + default_bucket_name).information()
            Operation(
                "If you don't want to upload the package to COS by default, you could change your configure!").information()

            cos_client = CosClient(region)
            Operation("Checking you COS Bucket.").process()
            cos_bucket_status = cos_client.get_bucket(default_bucket_name)

            if cos_bucket_status == 0:
                # 未获得到bucket
                Operation("Creating default COS Bucket: " + default_bucket_name).process()
                create_status = cos_client.create_bucket(bucket=default_bucket_name)
                if create_status == True:
                    cos_bucket_status = 1
                    Operation("Creating success. Cos Bucket name:  " + default_bucket_name).success()
                else:
                    Operation("Creating Cos Bucket faild.").warning()
                    cos_bucket_status = create_status
                    try:
                        if "<?xml" in str(create_status):
                            error_code = re.findall("<Code>(.*?)</Code>", str(create_status))[0]
                            error_message = re.findall("<Message>(.*?)</Message>", str(create_status))[0]
                            Operation("COS client error code: %s, message: %s" % (error_code, error_message)).warning()
                    except:
                        pass

            if cos_bucket_status == 1:
                try:
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
                    except:
                        pass

                    if is_have == 0:
                        Operation("Uploading to COS, bucket name: " + default_bucket_name).process()

                        # 普通上传
                        cos_client.upload_file2cos(
                            bucket=default_bucket_name,
                            file=file_data,
                            key=zip_file_name_cos
                        )

                        # 分块上传
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
                except Exception as e:
                    cos_bucket_status = e

            # cos_bucket_status = 2

            if cos_bucket_status not in (0, 1):
                size_infor = self.file_size_infor(file_size)
                if size_infor == -1:
                    Operation("Upload Error.").warning()
                    raise UploadFailed(str(e))
                else:
                    Operation("There are some exceptions and the process of uploading to COS is terminated!").warning()
                    Operation("This package will be uploaded by TencentCloud Cloud API.").information()
                    if size_infor == 0:
                        msg = "Package size is over 8M, it is highly recommended that you upload using COS. "
                        Operation(msg).information()
                    Operation("Uploading this package.").process()
                    code_url["zip_file"] = os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name)
                    Operation("Upload success").success()

        else:
            msg = "If you want to increase the upload speed, you can configure using-cos with command：scf configure set"
            Operation(msg).information()
            size_infor = self.file_size_infor(file_size)
            if size_infor == -1:
                msg = 'Your package is too large and needs to be uploaded via COS.'
                Operation(msg).warning()
                msg = 'You can use --cos-bucket BucketName to specify the bucket, or you can use the "scf configure set" to set the default to open the cos upload.'
                Operation(msg).warning()
                raise UploadFailed("Upload faild")
            elif size_infor == 0:
                Operation("Package size is over 8M, it is highly recommended that you upload using COS. ").information()
            Operation("Uploading this package.").process()
            code_url["zip_file"] = os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name)
            Operation("Upload success").success()

        return code_url

    def _zip_func(self, func_path, namespace, func_name):

        if not os.path.exists(func_path):
            raise ContextException("Function file or path not found by CodeUri '{}'".format(func_path))

        if self.deploy_namespace and self.deploy_namespace != namespace:
            namespace = self.deploy_namespace

        buff = BytesIO()

        zip_file_name = str(namespace) + '-' + str(func_name) + '-latest.zip'
        time_data = time.strftime("-%Y-%m-%d-%H-%M-%S", time.localtime(int(time.time())))
        zip_file_name_cos = str(namespace) + '-' + str(func_name) + '-latest' + time_data + '.zip'

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
                else:
                    (filepath, filename) = os.path.split(func_path)
                    if filepath:
                        os.chdir(filepath)

                    with ZipFile(buff, mode='w', compression=ZIP_DEFLATED) as zip_object:
                        zip_object.write(filename)
                    os.chdir(cwd)

                buff.seek(0)
                buff.name = zip_file_name

            # a temporary support for upload func from local zipfile
            with open(zip_file_path, 'wb') as f:
                f.write(buff.read())
                buff.seek(0)

        except Exception as e:
            raise PackageException("Package Error. Please check CodeUri in YAML.")

        Operation("Compress function '{}' to zipfile '{}' success".format(zip_file_path, zip_file_name)).success()
        return buff, zip_file_name, zip_file_name_cos


class Deploy(object):
    def __init__(self, resource, namespace, region=None, forced=False, skip_event=False, update_event=False):
        self.resources = resource
        self.namespace = namespace
        self.region = region
        self.forced = forced
        self.skip_event = skip_event
        self.update_event = update_event

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

    def trigger_upgrade_message(self, temp_trigger, eve_event):

        if not self.update_event:
            msg = "The %s Event %s in the Yaml file is inconsistent with Release. Please check it." % (
                str(temp_trigger["Type"]).upper(), temp_trigger["TriggerName"])
            Operation(msg).warning()
        else:
            msg = "The %s Event %s in the Yaml file is inconsistent with Release." % (
                str(temp_trigger["Type"]).upper(), temp_trigger["TriggerName"])
            Operation(msg).warning()

        click.secho("[+] This Information: ", fg="cyan")
        self.recursion_dict(temp_trigger, 0)
        click.secho("[+] Release Information: ", fg="cyan")
        self.recursion_dict(eve_event, 0)

        if not self.update_event:
            msg = "This time will skip the modification of the departure."
            msg = msg + " If you want to upgrade all changed events by default,"
            msg = msg + " you can add the parameter --update-event. Like: scf deeploy --update-event"
            Operation(msg).information()

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
                Function(self.region, ns, func, self.resources).format_information()
            Operation("Deploy namespace '{ns}' end".format(ns=ns_this)).success()

    def _do_deploy_core(self, func, func_name, func_ns, region, forced, skip_event=False):
        # check namespace exit, create namespace
        if self.namespace and self.namespace != func_ns:
            func_ns = self.namespace

        function_data = Function(region, func_ns, func_name, self.resources).get_function_trigger()
        trigger_release = None
        if function_data:
            now_runtime = function_data[0]
            trigger_release = function_data[1]

            if func['Properties']['Runtime'] != now_runtime:
                err_msg = "RUNTIME in YAML does not match RUNTIME on the RELEASE (release: %s)" % now_runtime
                raise DeployException(err_msg)

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

        deploy_result = ScfClient(region).deploy_func(func, func_name, func_ns, forced)

        if deploy_result == 1:
            Operation("{ns} {name} already exists, update it now".format(ns=func_ns, name=func_name)).process()
            deploy_result = ScfClient(region).update_config(func, func_name, func_ns)
            if deploy_result == True:
                deploy_result = ScfClient(region).update_code(func, func_name, func_ns)
                deploy_result = 0 if deploy_result == True else deploy_result

        if deploy_result == 0:
            Operation("Deploy function '{name}' success".format(name=func_name)).success()
            if not skip_event:
                self._do_deploy_trigger(func, func_name, func_ns, region, trigger_release)
            return

        elif deploy_result == 2:
            Operation("You can add -f to update the function when it already exists. Example : scf deploy -f").warning()
            raise CloudAPIException("The function already exists.")

        if deploy_result != None:
            err = deploy_result
            s = err.get_message()
            if sys.version_info[0] == 2 and isinstance(s, str):
                s = s.encode("utf8")
            err_msg = u"Deploy function '{name}' failure, {e}.".format(name=func_name, e=s)

            if err.get_request_id():
                err_msg += (u" RequestId: {}".format(err.get_request_id()))

            raise CloudAPIException(err_msg)

    def _do_deploy_trigger(self, func, func_name, func_ns, region=None, trigger_release=None):

        proper = func.get(tsmacro.Properties, {})
        events = proper.get(tsmacro.Events, {})
        hasError = None

        for trigger in events:
            trigger_status = True
            msg = "Deploy %s trigger '%s' failure, this trigger has been created." % (events[trigger]['Type'], trigger)
            if trigger_release:
                try:
                    event_type = str(events[trigger]['Type']).lower()
                    temp_trigger = events[trigger].copy()

                    if event_type == "timer":
                        temp_trigger['TriggerName'] = trigger

                    for eve_event in trigger_release[str(events[trigger]['Type']).lower()]:
                        eve_event_infor = eve_event.copy()
                        eve_event_infor.pop("TriggerDesc", eve_event_infor)
                        change_infor = False
                        tproperty = temp_trigger['Properties']
                        eproperty = eve_event['Properties']

                        if event_type == "timer":
                            if temp_trigger['TriggerName'] == eve_event['TriggerName']:
                                change_infor = True
                        elif event_type == "apigw":
                            if tproperty['ServiceId'] == eproperty['ServiceId'] and tproperty['StageName'] == eproperty[
                                'StageName'] and tproperty['HttpMethod'] == eproperty['HttpMethod']:
                                eve_event_infor.pop("TriggerName")
                                change_infor = True
                        elif event_type == "ckafka":
                            if tproperty['Name'] + "-" + eproperty['Topic'] == tproperty['Name'] + "-" + eproperty[
                                'Topic']:
                                eve_event_infor.pop("TriggerName")
                                change_infor = True
                        elif event_type == "cmq":
                            if tproperty['Name'] == eproperty['Name']:
                                eve_event_infor.pop("TriggerName")
                                change_infor = True
                        elif event_type == "cos":
                            if tproperty['Bucket'] == eproperty['Bucket'] and tproperty['Events'] == eproperty[
                                'Events'] and tproperty['Filter'] == eproperty['Filter']:
                                eve_event_infor.pop("TriggerName")
                                change_infor = True

                        if change_infor:
                            if temp_trigger == eve_event_infor:
                                trigger_status = False
                                Operation(msg).warning()

                            else:
                                if self.update_event:
                                    self.trigger_upgrade_message(temp_trigger, eve_event_infor)
                                    eve_event["Properties"].pop("Enable", eve_event["Properties"])
                                    err = ScfClient(region).remove_trigger(eve_event, func_name, func_ns)
                                    if not err:
                                        Operation("The trigger is being redeployed.").warning()
                                    else:
                                        trigger_status = False
                                        err_msg = "The redeployment trigger failed. Please manually delete the trigger and redeploy."
                                        Operation(err_msg).warning()
                                else:
                                    trigger_status = False
                                    self.trigger_upgrade_message(temp_trigger, eve_event_infor)
                            break
                except Exception as e:
                    print(e)
                    pass

                # if temp_trigger in trigger_release[str(events[trigger]['Type']).lower()]:
                #     trigger_status = False
                #     Operation(msg).warning()

            if trigger_status == True:
                err = ScfClient(region).deploy_trigger(events[trigger], trigger, func_name, func_ns)
                if err is not None:
                    hasError = err
                    if sys.version_info[0] == 3:
                        s = err.get_message()
                    else:
                        s = err.get_message().encode("UTF-8")

                    if err.get_request_id():
                        Operation("Deploy trigger '{name}' failure. Error: {e}. RequestId: {id}".
                                  format(name=trigger, e=s, id=err.get_request_id())).warning()
                    else:
                        msg = "Deploy trigger '{name}' failure. Error: {e}.".format(name=trigger, e=s, )
                        Operation(msg).warning()
                Operation("Deploy trigger '{name}' success".format(name=trigger)).success()
