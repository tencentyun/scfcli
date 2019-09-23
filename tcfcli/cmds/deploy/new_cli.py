# -*- coding: utf-8 -*-

import os
import random
import time
import re
import json
from io import BytesIO
import shutil
import hashlib
import threading
import fnmatch
import multiprocessing
import tcfcli.common.base_infor as infor
from multiprocessing import Process, Manager, queues
from queue import Queue
from zipfile import ZipFile, ZIP_DEFLATED
from tcfcli.help.message import DeployHelp as help
from tcfcli.common.template import Template
from tcfcli.common.user_exceptions import *
from tcfcli.libs.utils.scf_client import ScfClient
from tcfcli.common import tcsam
from tcfcli.common.user_config import UserConfig
from tcfcli.common.tcsam.tcsam_macro import TcSamMacro as tsmacro
from tcfcli.libs.utils.cos_client import CosClient
from tcfcli.common.operation_msg import Operation
from tcfcli.common.cam_role import list_scf_role

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
@click.option('--no-color', '-nc', is_flag=True, default=False, help=help.NOCOLOR)
def deploy(template_file, cos_bucket, name, namespace, region, forced, skip_event, without_cos, history, update_event,
           no_color):
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

    Deploy(template_file, cos_bucket, name, namespace, region, forced, skip_event, without_cos,
           update_event, history).start()


class Deploy(object):
    def __init__(self, template_file, cos_bucket, function, deploy_namespace, region, forced, skip_event, without_cos,
                 update_event, history=None):
        self.user_config = UserConfig()
        self.template_file = template_file
        self.template_file_dir = ""
        self.cos_bucket = cos_bucket
        self.check_params()
        template_data = tcsam.tcsam_validate(Template.get_template_data(self.template_file))
        self.resource = template_data.get(tsmacro.Resources, {})
        self.function = function
        self.deploy_namespace = deploy_namespace
        self.region = region if region else self.user_config.region
        self.cos_region = "ap-guangzhou" if self.region == "ap-guangzhou-open" else self.region
        self.without_cos = without_cos
        self.history = history
        self.bucket_name = "scf-deploy-" + self.region
        self.forced = forced
        self.skip_event = skip_event
        self.update_event = update_event

    def check_params(self):
        if not self.template_file:
            raise TemplateNotFoundException("FAM Template Not Found. Missing option --template-file")
        if not os.path.isfile(self.template_file):
            raise TemplateNotFoundException("FAM Template Not Found, template-file Not Found")

        self.template_file = os.path.abspath(self.template_file)
        self.template_file_dir = os.path.dirname(os.path.abspath(self.template_file))

        if self.cos_bucket and self.cos_bucket.endswith("-" + self.user_config.appid):
            self.cos_bucket = self.cos_bucket.replace("-" + self.user_config.appid, '')

    def start(self):

        # 判断函数是否存在
        if self.function and "'%s'" % str(self.function) not in str(self.resource):
            raise DeployException("Couldn't find the function in YAML, please add this function in YAML.")

        if self.without_cos:
            Operation(
                "Because of --without-cos, this time won't be uploaded packages to the default COS-Bucket.").process()
        elif self.cos_bucket:
            Operation("Because of --cos-bucket, this time will be uploaded packages to the COS-Bucket: %s." % (
                self.cos_bucket)).process()
            cos_client = CosClient(self.cos_bucket)
            Operation("Checking %s COS-Bucket: %s." % (self.region, self.cos_bucket)).process()
            if cos_client.get_bucket(self.cos_bucket) == 0:
                err_msg = "The COS-Bucket %s could not be found in %s. Please check it." % (
                    self.cos_bucket, self.region)
                raise COSBucketException(err_msg)
        elif self.user_config.using_cos.upper().startswith("TRUE"):
            default_bucket = self.bucket_name + "-" + self.user_config.appid
            Operation("By default, this time will be uploaded packages to COS-Bucket.").information()
            Operation("Region: %s, COS-Bucket: %s" % (self.region, default_bucket)).information()
            Operation(
                "If you don't want to upload packages to COS-Bucket by default, you can use the close command: scf configure set --using-cos N").information()
            cos_client = CosClient(self.region)
            Operation("Checking %s COS-Bucket: %s." % (self.region, default_bucket)).process()
            if cos_client.get_bucket(default_bucket) == 0:
                # 未获得到bucket
                Operation("Creating default COS Bucket: " + default_bucket).process()
                create_status = cos_client.create_bucket(bucket=default_bucket)
                if create_status == True:
                    Operation("Creating default COS-Bucket success.").success()
                    Operation("Region: %s, COS-Bucket: %s" % (self.region, default_bucket)).information()
                else:
                    Operation("Creating %s Cos Bucket: %s faild." % (self.region, default_bucket)).warning()
                    try:
                        if "<?xml" in str(create_status):
                            error_code = re.findall("<Code>(.*?)</Code>", str(create_status))[0]
                            error_message = re.findall("<Message>(.*?)</Message>", str(create_status))[0]
                            err_msg = "COS client error code: %s, message: %s" % (error_code, error_message)
                        else:
                            err_msg = str(create_status)
                    except:
                        err_msg = "Failed to create COS-Bucket. Please check if you have related operation permissions."
                    raise COSBucketException(err_msg)
        else:
            Operation(
                "If you want to increase the upload speed, you can use --using-cos, the open command：scf configure set --using-cos Y").information()

        for namespace in self.resource:  # 遍历函数命名空间

            real_namespace = self.deploy_namespace if self.deploy_namespace else namespace
            rep = ScfClient(self.region).get_ns(real_namespace)
            if not rep:
                Operation("%s: Namespace not exists, create it now" % (real_namespace)).process()
                err = ScfClient(self.region).create_ns(real_namespace)
                if err is not None:
                    if sys.version_info[0] == 3:
                        s = err.get_message()
                    else:
                        s = err.get_message().encode("UTF-8")
                    err_msg = "%s: Create namespace failure. Error: %s." % (real_namespace, s)
                    Operation(u' %s' % text(err_msg), fg="red").warning()
                    return False

            li = queues.Queue(1000, ctx=multiprocessing)
            workflow_process = None
            function_count = 0

            for function in list(self.resource[namespace]):  # 遍历函数

                # 去除掉函数类型行
                if function == tsmacro.Type:
                    continue

                # 如果用户指定Function，则只提取用户已有的Function
                if self.function is not None and function != self.function:
                    continue

                function_count = function_count + 1

                # 前置判断完成，进行workflow： package -> deploy function -> deploy trigger
                # 此处采用多进程实现
                # self.workflow(namespace, function, message)
                if self.history:
                    self.workflow(namespace, real_namespace, function, li)
                else:
                    workflow_process = Process(
                        target=self.workflow,
                        args=(namespace, real_namespace, function, li)
                    )
                    workflow_process.start()

            if workflow_process:
                workflow_process.join()

            result_list = []
            while function_count != 0:
                temp_li = li.get()
                result_list.append(temp_li)
                time.sleep(0.1)
                if len(result_list) == function_count:
                    break

            self.function_output(result_list, namespace)

        # 删除缓存目录（临时文件存放）
        try:
            shutil.rmtree(_BUILD_DIR)
        except Exception as e:
            pass

    def workflow(self, namespace, real_namespace, function, li):

        function_message = {
            "function": function,
            "package": None,
            "deploy_function": None,
            "deploy_trigger": None,
        }

        function_resource = self.package(namespace, real_namespace, function)
        if function not in function_resource[real_namespace]:
            function_message["package"] = False
        else:
            function_message["package"] = True
            deploy_result = self.deploy(function_resource[real_namespace][function], real_namespace, function)
            if deploy_result == False:
                function_message["deploy_function"] = False
            else:
                function_message["deploy_function"] = True
                function_message["deploy_trigger"] = deploy_result[1] if len(deploy_result) == 2 else None
        li.put(function_message)
        # message.append(function)

    def package(self, namespace, real_namespace, function):
        function_resource = {
            real_namespace: {
                "Type": "TencentCloud::Serverless::Namespace",
                function: self.resource[namespace][function]
            }
        }

        if self.history:
            code_url = self.package_history(namespace, function)
        else:
            code_url = self.package_core(namespace, real_namespace, function)

        try:
            if "cos_bucket_name" in code_url:  # 使用了cos_bucket或者是using_cos
                bucket_name = code_url["cos_bucket_name"]
                object_name = code_url["cos_object_name"]
                function_resource[real_namespace][function][tsmacro.Properties]["CosBucketName"] = bucket_name
                function_resource[real_namespace][function][tsmacro.Properties]["CosObjectName"] = object_name
            elif "zip_file" in code_url:  # 未使用using_cos或者使用without-cos,
                function_resource[real_namespace][function][tsmacro.Properties]["LocalZipFile"] = code_url["zip_file"]
            else:
                del self.resource[namespace][function]
        except Exception as e:
            Operation("%s - %s: %s" % (real_namespace, function, str(e))).warning()
            del self.resource[namespace][function]

        return function_resource

    def package_core(self, namespace, real_namespace, function):

        template_path, template_name = os.path.split(self.template_file)
        code_uri = self.resource[namespace][function][tsmacro.Properties].get(tsmacro.CodeUri, "")
        function_path = os.path.join(template_path, code_uri)
        zip_result = self.package_zip_core(function_path, real_namespace, function)
        if zip_result[0] == True:
            zip_file, zip_file_name, zip_file_name_cos = zip_result[1:]
        else:
            return

        code_url = dict()

        file_size = os.path.getsize(os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name))
        Operation("%s - %s: Package name: %s, package size: %s kb" % (
            real_namespace, function, zip_file_name, str(file_size / 1000))).process()

        using_cos = True if self.user_config.using_cos.upper().startswith("TRUE") else False

        if self.without_cos:
            size_infor = self.package_zip_size(file_size)
            if size_infor == -1:
                msg = '%s - %s: Your package %s is too large and needs to be uploaded via COS.' % (
                    real_namespace, function, zip_file_name)
                Operation(msg).warning()
                return
            elif size_infor == 0:
                Operation(
                    "%s - %s: Package %s size is over 8M, it is highly recommended that you upload using COS. " % (
                        real_namespace, function, zip_file_name)).information()
            code_url["zip_file"] = os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name)
        elif self.cos_bucket:
            upload_result = CosClient(self.cos_region).upload_file2cos2(bucket=self.cos_bucket, file=zip_file.read(),
                                                                        key=zip_file_name_cos)
            if upload_result == True:
                code_url["cos_bucket_name"] = self.cos_bucket
                code_url["cos_object_name"] = "/" + zip_file_name_cos
                msg = "%s - %s: Upload function zip file %s success." % (
                    real_namespace, function, code_url["cos_object_name"],)
                Operation(msg).success()
            else:
                msg = "%s - %s: Upload function zip file %s failed: %s" % (
                    real_namespace, function, code_url["cos_object_name"], upload_result)
                Operation(msg).warning()
                return
        elif using_cos:
            cos_client = CosClient(self.cos_region)
            try:
                # 获取bucket正常，继续流程
                file_data = zip_file.read()
                md5 = hashlib.md5(file_data).hexdigest()
                is_have = 0  # 判断包是否已经存在COS中
                try:
                    object_list = cos_client.get_object_list(
                        bucket=self.bucket_name,
                        prefix=str(real_namespace) + "-" + str(function)
                    )
                    if isinstance(object_list, dict) and 'Contents' in object_list:
                        for eve_object in object_list["Contents"]:
                            if md5 in eve_object["ETag"]:
                                result = cos_client.copy_object(
                                    self.bucket_name,
                                    eve_object["Key"],
                                    zip_file_name_cos)
                                if "Error" not in str(result):
                                    is_have = 1
                                break
                except Exception as e:
                    pass
                if is_have == 0:
                    upload_result = cos_client.upload_file2cos2(
                        bucket=self.bucket_name,
                        file=os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name),
                        key=zip_file_name_cos,
                        md5=md5,
                    )
                    if upload_result != True:
                        if "your policy or acl has reached the limit" in upload_result:
                            msg = "%s - %s: Your policy or acl has reached the limit, Please clean up COS-Bucket: %s" % (
                                real_namespace, function,self.bucket_name)
                        else:
                            msg = "%s - %s: Upload function zip file %s failed: %s" % (
                                real_namespace, function, zip_file_name_cos , upload_result)
                        Operation(msg).warning()
                        return

                code_url["cos_bucket_name"] = self.bucket_name
                code_url["cos_object_name"] = "/" + zip_file_name_cos
                msg = "%s - %s: Upload function zip file %s success." % (real_namespace, function, code_url["cos_object_name"])
                Operation(msg).success()
            except Exception as e:
                Operation("%s - %s: This package will be uploaded by TencentCloud Cloud API." % (
                    real_namespace, function,)).information()
                code_url["zip_file"] = os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name)
        else:
            size_infor = self.package_zip_size(file_size)
            if size_infor == -1:
                msg = '%s - %s: Your package %s is too large and needs to be uploaded via COS.' % (
                    real_namespace, function, zip_file_name)
                Operation(msg).warning()
                return
            elif size_infor == 0:
                Operation(
                    "%s - %s: Package %s size is over 8M, it is highly recommended that you upload using COS. " % (
                        real_namespace, function, zip_file_name)).information()
            code_url["zip_file"] = os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name)
        return code_url

    def package_history(self, namespace, function):

        cos_function = CosClient(self.cos_region).get_object_list(
            bucket=self.bucket_name,
            prefix=str(namespace) + "-" + str(function)
        )

        if isinstance(cos_function, dict) and 'Contents' in cos_function:
            rollback_dict = {}
            cos_function_list = cos_function['Contents']
            if cos_function_list:
                msg = "[+] %s %s :Select a number for the historical version deployment." % (namespace, function)
                Operation(msg, fg="cyan").echo()
                function_number = 0
                for eve_function in reversed(cos_function_list):
                    function_number = function_number + 1
                    if function_number > 15:
                        break
                    else:
                        function_name = eve_function["LastModified"].replace(".000Z", "").replace("T", " ")
                        msg = "  [%s] %s" % (function_number, text(function_name))
                        Operation(msg, fg="cyan").echo()
                        rollback_dict[str(function_number)] = eve_function["Key"]

                number = click.prompt(Operation("Please input number(Like: 1)", fg="cyan").style())
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
                    return code_url
            else:
                err_msg = "The historical version is not queried. The deployment history version code only takes effect when you use using-cos."
                raise RollbackException(err_msg)
        else:
            err_msg = "The historical version is not queried. The deployment history version code only takes effect when you use using-cos."
            raise RollbackException(err_msg)

    def package_zip_ignore(self, ignore_source_list, file_path):
        if file_path not in (".", ".."):
            for eve_ignore_file in ignore_source_list:
                if fnmatch.fnmatch(os.path.normpath(file_path), os.path.normpath(eve_ignore_file)):
                    return True
                if os.path.isdir(eve_ignore_file):
                    temp_path = eve_ignore_file if eve_ignore_file.endswith("/") else eve_ignore_file + "/"
                    if file_path.startswith(temp_path):
                        return True
        return False

    def package_zip_core(self, function_path, namespace, function):

        # 找不到函数的对应path，则返回错误
        if not os.path.exists(function_path):
            return (False, "Function file or path not found by CodeUri '{}'".format(function_path))

        # 对用户指定的Deploy进行额外操作
        if self.deploy_namespace and self.deploy_namespace != namespace:
            namespace = self.deploy_namespace

        buff = BytesIO()

        zip_file_name = "%s-%s-latest.zip" % (str(namespace), str(function))
        time_data = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(int(time.time())))
        zip_file_name_cos = "%s-%s-latest-%s.zip" % (str(namespace), str(function), time_data)

        cwd = os.getcwd()
        os.chdir(self.template_file_dir)

        zip_file_path = os.path.join(_BUILD_DIR, zip_file_name)
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)

        try:

            if os.path.isdir(function_path):  # 如果函数目录是dir
                # 进行文件的忽略
                ignore_source_list = []
                ignore_dir_path = os.path.join(function_path, "ignore")
                ignore_file_path = os.path.join(ignore_dir_path, "%s.ignore" % function)
                if os.path.isfile(ignore_file_path):
                    with open(ignore_file_path) as f:
                        ignore_source_list = [str(eve_line).strip() for eve_line in f.readlines()]

                os.chdir(function_path)

                with ZipFile(buff, mode='w', compression=ZIP_DEFLATED) as zip_object:
                    for current_path, sub_folders, files_name in os.walk(_CURRENT_DIR):
                        if not str(current_path).startswith("./.") and not str(current_path).startswith(r".\."):
                            for file in files_name:
                                if not self.package_zip_ignore(ignore_source_list, os.path.join(current_path, file)):
                                    zip_object.write(os.path.join(current_path, file))

                os.chdir(cwd)

            else:  # 如果目录不是Dir: 单个文件、压缩包
                if str(function_path).endswith(".zip"):  # 压缩包
                    with open(function_path, "rb") as f:
                        buff.write(f.read())
                else:  # 单个文件
                    (filepath, filename) = os.path.split(function_path)
                    if filepath:
                        os.chdir(filepath)

                    with ZipFile(buff, mode='w', compression=ZIP_DEFLATED) as zip_object:
                        zip_object.write(filename)
                    os.chdir(cwd)

            buff.seek(0)
            buff.name = zip_file_name

            # 建立临时目录/缓存目录
            if not os.path.exists(_BUILD_DIR):
                os.mkdir(_BUILD_DIR)

            with open(zip_file_path, 'wb') as f:
                f.write(buff.read())
                buff.seek(0)


        except Exception as e:
            return (False, "Package Error: %s" % (str(e)))

        return (True, buff, zip_file_name, zip_file_name_cos)

    def package_zip_size(self, size):
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

    def deploy(self, function_resource, namespace, function, times=0):
        try:
            role = function_resource.get(tsmacro.Properties, {}).get(tsmacro.Role)
            if role:
                rolelist = list_scf_role(self.region)
                if rolelist == None:
                    Operation("%s - %s: Get Role list error" % (namespace, function)).warning()
                    function_resource[tsmacro.Properties][tsmacro.Role] = None
                elif role not in rolelist:
                    Operation("%s - %s: %s not exists in remote scf role list" % (namespace, function, role)).warning()
                    if len(rolelist):
                        Operation("%s - %s: You can choose from %s " % (namespace, function, str(rolelist))).warning()
                    function_resource[tsmacro.Properties][tsmacro.Role] = None

            function_data = self.function_trigger(self.region, namespace, function)
            trigger_release = None
            if function_data:
                runtime_release = function_data[0]
                trigger_release = function_data[1]
                if function_resource['Properties']['Runtime'] != runtime_release:
                    err_msg = "RUNTIME in YAML does not match RUNTIME on the RELEASE (release: %s)" % (runtime_release)
                    Operation(u'%s - %s: %s' % (namespace, function, text(err_msg)), fg="red").warning()
                    return False

            deploy_result = ScfClient(self.region).deploy_func(function_resource, function, namespace, self.forced)

            if deploy_result == 1:
                Operation("%s - %s: Function already exists, update it now" % (namespace, function)).process()
                deploy_result = ScfClient(self.region).update_config(function_resource, function, namespace)
                if deploy_result == True:
                    deploy_result = ScfClient(self.region).update_code(function_resource, function, namespace)
                    deploy_result = 0 if deploy_result == True else deploy_result

            if deploy_result == 0:
                Operation("%s - %s: Deploy function success" % (str(namespace), str(function))).success()
                if not self.skip_event:
                    trigger_result = self.deploy_trigger_core(function_resource, function, namespace, self.region,
                                                              trigger_release)
                return (True, trigger_result)

            elif deploy_result == 2:
                Operation(
                    "%s - %s: You can add -f to update the function when it already exists. Example : scf deploy -f" % (
                        str(namespace), str(function))).warning()
                err_msg = "The function already exists."
                Operation(u'%s - %s: %s' % (str(namespace), str(function), text(err_msg)), fg="red").warning()
                return False

            if deploy_result != None:
                times = times + 1
                err = deploy_result
                s = err.get_message()
                if "which exceeds the frequency limit `10`" in str(s) and times <= 3:
                    time.sleep(random.uniform(0.5, 1.5))
                    deploy_result = self.deploy(function_resource, namespace, function, times)
                    if deploy_result != False and len(deploy_result) == 2:
                        return (True, deploy_result[1])
                    else:
                        return False
                else:
                    if sys.version_info[0] == 2 and isinstance(s, str):
                        s = s.encode("utf8")
                    err_msg = u"Deploy function '{name}' failure, {e}.".format(name=function, e=s)
                    if err.get_request_id():
                        err_msg += (u" RequestId: {}".format(err.get_request_id()))
                    Operation(u'%s - %s: %s' % (str(namespace), str(function), text(err_msg)), fg="red").warning()
                    return False
        except Exception as e:
            Operation(u'%s - %s: %s' % (str(namespace), str(function), str(e)), fg="red").warning()

        return False

    def deploy_trigger_core(self, function_resource, function, namespace, region, trigger_release):
        proper = function_resource.get(tsmacro.Properties, {})
        events = proper.get(tsmacro.Events, {})

        trigger_threads = []
        trigger_queue = Queue(maxsize=20)
        trigger_count = 0
        trigger_result = []
        for trigger in events:
            trigger_count = trigger_count + 1
            trigger_status = True
            msg = "%s - %s: Deploy %s trigger '%s' failure, this trigger has been created." % (
                str(namespace), str(function), events[trigger]['Type'], trigger)
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
                                trigger_result.append((trigger, True))
                            else:
                                if self.update_event:
                                    eve_event["Properties"].pop("Enable", eve_event["Properties"])
                                    err = ScfClient(region).remove_trigger(eve_event, function, namespace)
                                    if not err:
                                        trigger_result.append((trigger, True))
                                        Operation("%s - %s: %s, The trigger is being redeployed." % (
                                            namespace, function, temp_trigger['TriggerName'])).warning()
                                    else:
                                        trigger_result.append((trigger, False))
                                        trigger_status = False
                                        err_msg = "%s - %s: %s, The redeployment trigger failed. Please manually delete the trigger and redeploy." % (
                                            namespace, function, temp_trigger['TriggerName'])
                                        Operation(err_msg).warning()
                                else:
                                    Operation(
                                        '%s - %s: %s, The same name Trigger already exists. If you want to upgrade, you can add the --update-event parameter.' % (
                                            namespace, function, temp_trigger['TriggerName'])).warning()
                                    trigger_status = False
                                    trigger_result.append((trigger, False))
                            break
                except Exception as e:
                    pass

            if trigger_status == True:
                t = threading.Thread(target=self.deploy_do_trigger,
                                     args=(region, events, trigger, function, namespace, trigger_queue))
                trigger_threads.append(t)
                t.start()

        for t in trigger_threads:
            t.join()

        while trigger_count != 0:
            temp_trigger = trigger_queue.get()
            trigger_result.append(temp_trigger)
            time.sleep(0.1)
            if len(trigger_result) == trigger_count:
                break
        return trigger_result

    def deploy_do_trigger(self, region, events, trigger, function, namespace, queue):
        err = ScfClient(region).deploy_trigger(events[trigger], trigger, function, namespace)
        if err is not None:
            message = (trigger, False)
            if sys.version_info[0] == 3:
                s = err.get_message()
            else:
                s = err.get_message().encode("UTF-8")

            if err.get_request_id():
                Operation("%s - %s: Deploy %s %s trigger %s failure. Error: %s. RequestId: %s" % (
                    namespace, function, namespace, function, trigger, s, err.get_request_id())).warning()
            else:
                msg = "%s - %s: Deploy %s %s trigger %s failure. Error: %s." % (
                    namespace, function, namespace, function, trigger, s)
                Operation(msg).warning()
        else:
            message = (trigger, True)
            Operation(
                "%s - %s: Deploy %s %s trigger %s success" % (
                    namespace, function, namespace, function, trigger)).success()
        queue.put(message)

    def function_information(self, region, namespace, function):
        scf_client = ScfClient(region=region)
        result = scf_client.get_function(namespace=namespace, function_name=function)
        return result

    def function_trigger(self, region, namespace, function):
        try:
            result = self.function_information(region, namespace, function)
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

    def function_output(self, function_dict, namespace):
        # print(function_dict)

        error_state = True if "False" in str(function_dict) else False

        package_result = {"success": [], "failed": []}
        function_result = {"success": [], "failed": []}

        for eve_information in function_dict:
            if eve_information['package']:
                package_result["success"].append(eve_information['function'])
            else:
                package_result["failed"].append(eve_information['function'])

            if eve_information['deploy_function']:
                function_result["success"].append(eve_information['function'])
            else:
                function_result["failed"].append(eve_information['function'])

        Operation("Namespace: %s" % (namespace)).process()

        try:
            Operation("Package result:").out_infor()
            Operation("  Success: %d" % (len(package_result["success"]))).out_infor()
            for eve_success in package_result["success"]:
                Operation("    %s" % (eve_success)).out_infor()
            Operation("  Faild: %d" % (len(package_result["failed"]))).out_infor()
            for eve_failed in package_result["failed"]:
                Operation("    %s" % (eve_failed)).out_infor()
        except Exception as e:
            pass

        try:
            Operation("Function result:").out_infor()
            Operation("  Success: %d" % (len(function_result["success"]))).out_infor()
            for eve_success in function_result["success"]:
                Operation("    %s" % (eve_success)).out_infor()
            Operation("  Faild: %d" % (len(function_result["failed"]))).out_infor()
            for eve_failed in function_result["failed"]:
                Operation("    %s" % (eve_failed)).out_infor()
        except Exception as e:
            pass

        try:
            Operation("Trigger result:").out_infor()
            for eve_information in function_dict:
                Operation("  %s: " % (eve_information['function'])).out_infor()
                if eve_information and 'deploy_trigger' in eve_information:
                    if eve_information['deploy_trigger']:
                        for eve_trigger in eve_information['deploy_trigger']:
                            Operation(
                                "    %s: %s" % (eve_trigger[0], "success" if eve_trigger[1] else "failed")).out_infor()
                    else:
                        Operation("    No Trigger deployment results").out_infor()
        except Exception as e:
            pass

        Operation("Deployment is complete and can be triggered by scf remote invoke").information()
        Operation(
            "For example: scf remote invoke -n %s -e ./event.json " % (function_dict[0]["function"])).information()

        if error_state:
            raise DeployException("Not all deployments were successful, please check！")