# -*- coding: utf-8 -*-

import os
import sys
import random
import time
import re
import json
import chardet
import operator
from io import BytesIO
import shutil
import hashlib
import threading
import fnmatch
import platform
import traceback
import multiprocessing
import tcfcli.common.base_infor as infor
from multiprocessing import Process, queues
from queue import Queue
from zipfile import ZipFile, ZIP_DEFLATED
from tcfcli.help.message import DeployHelp as help
from tcfcli.common.template import Template
from tcfcli.common.user_exceptions import *
from tcfcli.libs.utils.scf_client import ScfClient, FunctionStatus, ResourceStatus
from tcfcli.common import tcsam
from tcfcli.common.user_config import UserConfig
from tcfcli.common.tcsam.tcsam_macro import TcSamMacro as tsmacro
from tcfcli.libs.utils.cos_client import CosClient
from tcfcli.common.operation_msg import Operation
from tcfcli.common.cam_role import list_scf_role
from tcfcli.cmds.function.information.cli import Information
from tcfcli.common.gitignore import IgnoreList, MATCH_IGNORE

_CURRENT_DIR = '.'
_BUILD_DIR = os.path.join(os.getcwd(), '.scf_build')
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

    # 删除缓存目录（临时文件存放）
    try:
        shutil.rmtree(_BUILD_DIR)
    except Exception as e:
        Operation(e, err_msg=traceback.format_exc()).no_output()

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
            cos_client = CosClient(self.region)
            Operation("Checking %s COS-Bucket: %s." % (self.region, self.cos_bucket)).process()
            default_bucket = self.cos_bucket + "-" + self.user_config.appid
            if cos_client.get_bucket(default_bucket) == 0:
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
                    Operation("Creating %s Cos Bucket: %s faild." % (self.region, default_bucket)).exception()
                    try:
                        if "<?xml" in str(create_status):
                            error_code = re.findall("<Code>(.*?)</Code>", str(create_status))[0]
                            error_message = re.findall("<Message>(.*?)</Message>", str(create_status))[0]
                            err_msg = "COS client error code: %s, message: %s" % (error_code, error_message)
                        else:
                            err_msg = str(create_status)
                    except Exception as e:
                        err_msg = "Failed to create COS-Bucket. Please check if you have related operation permissions."
                        Operation(e, err_msg=traceback.format_exc()).no_output()
                    raise COSBucketException(err_msg)
        else:
            Operation(
                "If you want to increase the upload speed, you can use --using-cos, the open command：scf configure set --using-cos Y").information()

        error_state = False

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
                    Operation(u' %s' % text(err_msg), fg="red").exception()
                    return False

            li = queues.Queue(1000, ctx=multiprocessing) if platform.python_version() >= '3' else queues.Queue(1000)

            workflow_process = None
            temp_function_list = []
            for function in list(self.resource[namespace]):  # 遍历函数

                # 去除掉函数类型行
                if function == tsmacro.Type:
                    continue

                # 如果用户指定Function，则只提取用户已有的Function
                if self.function is not None and function != self.function:
                    continue

                temp_function_list.append(function)

            # function_count = 0
            # function_list = []
            # function_team = []
            # for eve_function in temp_function_list:
            #     function_team.append(eve_function)
            #     function_count = function_count + 1
            #     if len(function_team) == 10 or function_count == len(temp_function_list):
            #         function_list.append(function_team)
            #         function_team = []
            #
            #
            # function_count = len(function_list)
            # max_thread = int(50 / function_count)
            # max_thread = 2 if max_thread < 2 else max_thread
            # #
            #
            # final_function_list = []
            # for function_team in function_list:
            #     for function in function_team:
            #         # 前置判断完成，进行workflow： package -> deploy function -> deploy trigger
            #         # 此处采用多进程实现
            #         # self.workflow(namespace, function, message)
            #
            #         if self.history:
            #             self.workflow(namespace, real_namespace, function, li, 10)
            #         else:
            #             workflow_process = Process(
            #                 target=self.workflow,
            #                 args=(namespace, real_namespace, function, li, max_thread)
            #             )
            #             workflow_process.start()
            #
            #     if workflow_process:
            #         workflow_process.join()
            #
            #     result_list = []
            #     while len(function_team) != 0:
            #         temp_li = li.get()
            #         result_list.append(temp_li)
            #         final_function_list.append(temp_li)
            #         time.sleep(0.1)
            #         if len(result_list) == len(function_team):
            #             break

            function_count = 0
            result_list = []
            function_total = len(temp_function_list)
            max_thread = int(50 / (function_total if function_total <= 10 else 10))
            max_thread = 2 if max_thread < 2 else max_thread
            max_funtion = 10
            for eve_function in temp_function_list:

                function_count = function_count + 1
                if function_count >= max_funtion or function_count == function_total:
                    if workflow_process:
                        workflow_process.join()
                    while True:
                        try:
                            temp_li = li.get(timeout=0.5)
                            result_list.append(temp_li)
                            max_funtion = max_funtion + 1
                        except:
                            break

                if self.history:
                    self.workflow(namespace, real_namespace, eve_function, li, 10)
                else:
                    workflow_process = Process(
                        target=self.workflow,
                        args=(namespace, real_namespace, eve_function, li, max_thread)
                    )
                    workflow_process.start()

            while function_total != 0:
                temp_li = li.get()
                result_list.append(temp_li)
                if len(result_list) == function_total:
                    break

            self.function_output(result_list, real_namespace)

            if not error_state:
                error_state = True if "False" in str(result_list) else False

        if error_state:
            raise DeployException("Not all deployments were successful, please check！")

        # 删除缓存目录（临时文件存放）
        try:
            shutil.rmtree(_BUILD_DIR)
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc()).no_output()

    def workflow(self, namespace, real_namespace, function, li, max_thread):

        function_message = {
            "function": function,
            "package": None,
            "deploy_function": None,
            "deploy_trigger": None,
        }

        function_resource = self.package(namespace, real_namespace, function, max_thread)
        if (not function_resource) or (function not in function_resource[real_namespace]):
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

    def package(self, namespace, real_namespace, function, max_thread):
        function_resource = {
            real_namespace: {
                "Type": "TencentCloud::Serverless::Namespace",
                function: self.resource[namespace][function]
            }
        }

        if self.history:
            code_url = self.package_history(namespace, function)
        else:
            code_url = self.package_core(namespace, real_namespace, function, max_thread)

        if code_url:
            try:
                if "cos_bucket_name" in code_url:  # 使用了cos_bucket或者是using_cos
                    bucket_name = code_url["cos_bucket_name"]
                    object_name = code_url["cos_object_name"]
                    function_resource[real_namespace][function][tsmacro.Properties]["CosBucketName"] = bucket_name
                    function_resource[real_namespace][function][tsmacro.Properties]["CosObjectName"] = object_name
                elif "zip_file" in code_url:  # 未使用using_cos或者使用without-cos,
                    function_resource[real_namespace][function][tsmacro.Properties]["LocalZipFile"] = code_url[
                        "zip_file"]
                else:
                    Operation("%s - %s: Package Failed" % (real_namespace, function)).exception()
                    del self.resource[namespace][function]
            except Exception as e:
                Operation("%s - %s: %s" % (real_namespace, function, str(e)), err_msg=traceback.format_exc()).warning()
                del self.resource[namespace][function]
        else:
            return None

        return function_resource

    def package_core(self, namespace, real_namespace, function, max_thread):

        template_path, template_name = os.path.split(self.template_file)
        code_uri = self.resource[namespace][function][tsmacro.Properties].get(tsmacro.CodeUri, "")

        if isinstance(code_uri, dict):
            return {
                "cos_bucket_name": code_uri["Bucket"],
                "cos_object_name": code_uri["Key"]
            }

        function_path = os.path.join(template_path, code_uri)
        zip_result = self.package_zip_core(function_path, real_namespace, function)
        if zip_result[0] == True:
            zip_file, zip_file_name, zip_file_name_cos = zip_result[1:]
        else:
            if len(zip_result) == 2:
                Operation("%s - %s: %s" % (real_namespace, function, zip_result[1])).exception()
            return

        code_url = dict()
        file_size = os.path.getsize(os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name))
        max_thread_file = int(file_size / 1000 / 40)
        max_thread = 1 if max_thread_file < 1 else (max_thread if max_thread_file > max_thread else max_thread_file)
        Operation("%s - %s: Package name: %s, package size: %s kb" % (
            real_namespace, function, zip_file_name, 0.01 if file_size / 1000 == 0 else file_size / 1000)).process()
        using_cos = True if self.user_config.using_cos.upper().startswith("TRUE") else False

        if self.without_cos:
            size_infor = self.package_zip_size(file_size)
            if size_infor == -1:
                msg = '%s - %s: Your package %s is too large and needs to be uploaded via COS.' % (
                    real_namespace, function, zip_file_name)
                Operation(msg).exception()
                return
            elif size_infor == 0:
                Operation(
                    "%s - %s: Package %s size is over 8M, it is highly recommended that you upload using COS. " % (
                        real_namespace, function, zip_file_name)).information()
            code_url["zip_file"] = os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name)
        elif self.cos_bucket:
            upload_result = CosClient(self.cos_region).upload_file2cos2(bucket=self.cos_bucket, file=os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name),
                                                                        key=zip_file_name_cos, max_thread=max_thread)
            if upload_result == True:
                code_url["cos_bucket_name"] = self.cos_bucket
                code_url["cos_object_name"] = "/" + zip_file_name_cos
                msg = "%s - %s: Upload function zip file %s to cos success." % (
                    real_namespace, function, code_url["cos_object_name"],)
                Operation(msg).success()
            else:
                msg = "%s - %s: Upload function zip file to cos %s failed: %s" % (
                    real_namespace, function, self.cos_bucket, upload_result)
                Operation(msg).exception()
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
                    Operation(e, err_msg=traceback.format_exc()).no_output()
                if is_have == 0:
                    upload_result = cos_client.upload_file2cos2(
                        bucket=self.bucket_name,
                        file=os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name),
                        key=zip_file_name_cos,
                        max_thread=max_thread,
                    )
                    if upload_result != True:
                        if "your policy or acl has reached the limit" in upload_result:
                            msg = "%s - %s: Your policy or acl has reached the limit, Please clean up COS-Bucket: %s" % (
                                real_namespace, function, self.bucket_name)
                        else:
                            msg = "%s - %s: Upload function zip file %s failed: %s" % (
                                real_namespace, function, zip_file_name_cos, upload_result)
                        Operation(msg).exception()
                        return

                code_url["cos_bucket_name"] = self.bucket_name
                code_url["cos_object_name"] = "/" + zip_file_name_cos
                msg = "%s - %s: Upload function zip file %s success." % (
                    real_namespace, function, code_url["cos_object_name"])
                Operation(msg).success()
            except Exception as e:
                Operation("%s - %s: This package will be uploaded by TencentCloud Cloud API." % (
                    real_namespace, function,), err_msg=traceback.format_exc()).information()
                code_url["zip_file"] = os.path.join(os.getcwd(), _BUILD_DIR, zip_file_name)
        else:
            size_infor = self.package_zip_size(file_size)
            if size_infor == -1:
                msg = '%s - %s: Your package %s is too large and needs to be uploaded via COS.' % (
                    real_namespace, function, zip_file_name)
                Operation(msg).exception()
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
        ignore = IgnoreList()
        ignore.parse(ignore_source_list)
        return ignore.match(file_path) == MATCH_IGNORE

        # if file_path not in (".", ".."):
        #     for eve_ignore_file in ignore_source_list:
        #         if fnmatch.fnmatch(os.path.normpath(file_path), os.path.normpath(eve_ignore_file)):
        #             return True
        #         if os.path.isdir(eve_ignore_file):
        #             temp_path = eve_ignore_file if eve_ignore_file.endswith("/") else eve_ignore_file + "/"
        #             if file_path.startswith(temp_path):
        #                 return True
        # return False

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
                    with open(ignore_file_path, "rb") as f:
                        temp_data = f.readlines()
                    ignore_source_list = []
                    for eve_line in temp_data:
                        try:
                            read_data = eve_line.decode("utf-8")
                        except Exception as e:
                            try:
                                read_data = eve_line.decode("gbk")
                            except Exception as e:
                                try:
                                    read_data = eve_line.decode("ascii")
                                except:
                                    read_data = eve_line.decode(chardet.detect(eve_line).get('encoding'))
                        ignore_source_list.append(str(read_data).strip())
                    Operation("%s - %s : Ignore file found: \n    %s" % (
                        namespace, function, "\n    ".join(ignore_source_list))).information()

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
            Operation(e, err_msg=traceback.format_exc(), level="ERROR")
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


    def check_func_status(self, function, namespace, timeout=30):
        '''
        :param timeout: check function status timeout
        :return 0 status normal
               1 status can't update 
               2 function not found
        '''
        
        status = ''
        while (True):
            if timeout == 0:
                break
            funcJsonStr = ScfClient(self.region).get_function(function, namespace)
            if funcJsonStr == None:
                return FunctionStatus.FUNC_STATUS_FAILED

            funcObject = json.loads(funcJsonStr)
            status = funcObject.get('Status', '')
            Operation(
                    "%s - %s: Check function status %s" % (str(namespace), str(function), status)).process()
            if (status.upper() == 'ACTIVE'):
                break
            elif (status.upper() == 'CREATEFAILED'):
                return FunctionStatus.FUNC_STATUS_FAILED
            elif (status.upper() == 'UPDATEFAILED'):
                return FunctionStatus.FUNC_STATUS_FAILED
            time.sleep(1)
            timeout = timeout - 1

        if status.upper() != 'ACTIVE':
            return FunctionStatus.FUNC_STATUS_FAILED
        else:
            return FunctionStatus.FUNC_STATUS_ACTIVE

    def deploy(self, function_resource, namespace, function, times=0):
        try:
            role = function_resource.get(tsmacro.Properties, {}).get(tsmacro.Role)
            if role:
                rolelist = list_scf_role(self.region)
                if rolelist == None:
                    Operation("%s - %s: Get Role list error" % (namespace, function)).exception()
                    return False
                elif role not in rolelist:
                    Operation(
                        "%s - %s: %s not exists in remote scf role list" % (namespace, function, role)).exception()
                    if len(rolelist):
                        Operation("%s - %s: You can choose from %s " % (namespace, function, str(rolelist))).exception()
                    return False

            function_data = self.function_trigger(self.region, namespace, function)
            trigger_release = None
            if function_data:
                runtime_release = function_data[0]
                trigger_release = function_data[1]
                if function_resource['Properties']['Runtime'] != runtime_release:
                    err_msg = "RUNTIME in YAML does not match RUNTIME on the RELEASE (release: %s)" % (runtime_release)
                    Operation(u'%s - %s: %s' % (namespace, function, text(err_msg)), fg="red").exception()
                    return False

            deploy_result, err = ScfClient(self.region).deploy_func(function_resource, function, namespace)
            func_status = ResourceStatus.RESOURCE_STATUS_FUNC_NOT_EXISTS
            if deploy_result == False:
                if err.code in ["ResourceInUse.Function", "ResourceInUse.FunctionName"]:
                    func_status = ResourceStatus.RESOURCE_STATUS_FUNC_EXISTS
                else:
                    return False
            else:
                func_status = FunctionStatus.FUNC_STATUS_ACTIVE

            if func_status == ResourceStatus.RESOURCE_STATUS_FUNC_EXISTS and self.forced == False:
                Operation(
                    "%s - %s: You can add -f to update the function when it already exists. Example : scf deploy -f" % (
                        str(namespace), str(function))).warning()
                err_msg = "The function already exists."
                Operation(u'%s - %s: %s' % (str(namespace), str(function), text(err_msg)), fg="red").exception()
                return False

            if func_status == FunctionStatus.FUNC_STATUS_ACTIVE:
                func_status = self.check_func_status(function, namespace, 90)
                if func_status == FunctionStatus.FUNC_STATUS_FAILED:
                    err_msg = 'The function status not allowed update config'
                    Operation(u'%s - %s: %s' % (str(namespace), str(function), text(err_msg)), fg="red").exception()
                    return False

            Operation("%s - %s: Function update it now" % (namespace, function)).process()
            deploy_result = ScfClient(self.region).update_config(function_resource, function, namespace)
            if deploy_result == True:
                func_status = self.check_func_status(function, namespace, 90)
                if func_status == FunctionStatus.FUNC_STATUS_FAILED:
                    err_msg = 'The function status not allowed update code'
                    Operation(u'%s - %s: %s' % (str(namespace), str(function), text(err_msg)), fg="red").exception()
                    return False
                deploy_result = ScfClient(self.region).update_code(function_resource, function, namespace)


            if deploy_result == True:
                Operation("%s - %s: Deploy function success" % (str(namespace), str(function))).success()
                if not self.skip_event:
                    func_status = self.check_func_status(function, namespace, 90)
                    if func_status == FunctionStatus.FUNC_STATUS_FAILED:
                        err_msg = 'The function status not allowed update trigger'
                        Operation(u'%s - %s: %s' % (str(namespace), str(function), text(err_msg)), fg="red").exception()
                        return False
                    trigger_result = self.deploy_trigger_core(function_resource, function, namespace, self.region,
                                                              trigger_release)
                else:
                    trigger_result = None
                return (True, trigger_result)


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
                    Operation(u'%s - %s: %s' % (str(namespace), str(function), text(err_msg)), fg="red").exception()
                    return False
        except Exception as e:
            Operation(u'%s - %s: %s' % (str(namespace), str(function), str(e)), fg="red",
                      err_msg=traceback.format_exc()).exception()

        return False

    def deploy_trigger_core(self, function_resource, function, namespace, region, trigger_release):
        try:
            proper = function_resource.get(tsmacro.Properties, {})
            events = proper.get(tsmacro.Events, {})

            trigger_threads = []
            trigger_queue = Queue(maxsize=2000)
            trigger_count = 0
            trigger_result = []
            for trigger in events:
                trigger_count = trigger_count + 1
                trigger_status = True
                msg = "%s - %s: Trigger: %s - %s has been created." % (
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
                                    if "Enable" not in temp_trigger['Properties']:
                                        temp_trigger['Properties']["Enable"] = True
                                    change_infor = True
                            elif event_type == "apigw":
                                if tproperty['ServiceId'] == eproperty['ServiceId'] and tproperty['StageName'] == \
                                        eproperty['StageName'] and tproperty['HttpMethod'] == eproperty['HttpMethod']:
                                    eve_event_infor.pop("TriggerName")
                                    if 'IntegratedResponse' not in temp_trigger['Properties']:
                                        temp_trigger['Properties']['isIntegratedResponse'] = 'FALSE'
                                    else:
                                        temp_ir = "TRUE" if temp_trigger['Properties'][
                                            'IntegratedResponse'] else "FALSE"
                                        temp_trigger['Properties']['isIntegratedResponse'] = temp_ir
                                        temp_trigger['Properties'].pop("IntegratedResponse")
                                    if "Enable" not in temp_trigger['Properties']:
                                        temp_trigger['Properties']["Enable"] = True
                                    change_infor = True
                            elif event_type == "ckafka":
                                if tproperty['Name'] + "-" + eproperty['Topic'] == tproperty['Name'] + "-" + eproperty[
                                    'Topic']:
                                    if "Enable" not in temp_trigger['Properties']:
                                        temp_trigger['Properties']["Enable"] = True
                                    eve_event_infor.pop("TriggerName")
                                    change_infor = True
                            elif event_type == "cmq":
                                if tproperty['Name'] == eproperty['Name']:
                                    if "Enable" not in temp_trigger['Properties']:
                                        temp_trigger['Properties']["Enable"] = True
                                    eve_event_infor.pop("TriggerName")
                                    change_infor = True
                            elif event_type == "cos":
                                if tproperty['Bucket'] == eproperty['Bucket'] and tproperty['Events'] == eproperty[
                                    'Events'] and tproperty['Filter'] == eproperty['Filter']:
                                    if "Enable" not in temp_trigger['Properties']:
                                        temp_trigger['Properties']["Enable"] = True
                                    eve_event_infor.pop("TriggerName")
                                    change_infor = True
                            if change_infor:

                                different = False
                                keys_temp_trigger = temp_trigger.keys()
                                keys_eve_event_infor = eve_event_infor.keys()
                                sorted(keys_temp_trigger)
                                sorted(keys_eve_event_infor)
                                if keys_temp_trigger != keys_temp_trigger:
                                    different = True
                                if not different:
                                    for eve in keys_temp_trigger:
                                        if temp_trigger[eve] != eve_event_infor[eve]:
                                            different = True
                                            break

                                if not different:
                                    trigger_status = False
                                    Operation(msg).warning()
                                    trigger_result.append((trigger, True))
                                else:
                                    if self.update_event:
                                        eve_event["Properties"].pop("Enable", eve_event["Properties"])
                                        err = ScfClient(region).remove_trigger(eve_event, function, namespace)
                                        if not err:
                                            Operation("%s - %s: %s, The trigger is being redeployed." % (
                                                namespace, function, temp_trigger['TriggerName'])).warning()
                                        else:
                                            trigger_result.append((trigger, False))
                                            trigger_status = False
                                            err_msg = "%s - %s: %s, The redeployment trigger failed. Please manually delete the trigger and redeploy." % (
                                                namespace, function, temp_trigger['TriggerName'])
                                            Operation(err_msg).exception()
                                    else:
                                        Operation(
                                            '%s - %s: %s, The same name Trigger already exists. If you want to upgrade, you can add the --update-event parameter.' % (
                                                namespace, function, temp_trigger['TriggerName'])).warning()
                                        trigger_status = False
                                        trigger_result.append((trigger, False))
                                break
                    except Exception as e:
                        Operation(e, err_msg=traceback.format_exc()).no_output()
                        pass

                if trigger_status == True:
                    t = threading.Thread(target=self.deploy_do_trigger,
                                         args=(region, events, trigger, function, namespace, trigger_queue))
                    trigger_threads.append(t)
                    t.start()

            for t in trigger_threads:
                t.join()
            while trigger_count != 0:
                try:
                    temp_trigger = trigger_queue.get(False)
                    trigger_result.append(temp_trigger)
                except Exception as e:
                    Operation(e, err_msg=traceback.format_exc()).no_output()
                time.sleep(0.1)
                # print(len(trigger_result), trigger_count)
                if len(trigger_result) == trigger_count:
                    break
            return trigger_result
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            return False

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
                    namespace, function, namespace, function, trigger, s, err.get_request_id())).exception()
            else:
                msg = "%s - %s: Deploy %s %s trigger %s failure. Error: %s." % (
                    namespace, function, namespace, function, trigger, s)
                Operation(msg).exception()
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
                                    'CronExpression': trigger_desc['cron'][2:-2] if str(
                                        trigger_desc['cron']).startswith("0 ") else trigger_desc['cron'],
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
                                    'isIntegratedResponse': trigger_desc["api"]["isIntegratedResponse"],
                                    'Enable': True if eve_trigger['Enable'] == 1 else False,
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
                                    'Enable': True if eve_trigger['Enable'] == 1 else False,
                                },
                                "TriggerDesc": trigger_desc
                            })

                    except Exception as e:
                        Operation(e, err_msg=traceback.format_exc()).no_output()
                return (function_runtime, trigger)
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc()).no_output()

        return None

    def function_output(self, function_dict, namespace):
        # print(function_dict)

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
            Operation(e, err_msg=traceback.format_exc()).no_output()

        try:
            Operation("Function result:").out_infor()
            Operation("  Success: %d" % (len(function_result["success"]))).out_infor()
            for eve_success in function_result["success"]:
                Operation("    %s" % (eve_success)).out_infor()
            Operation("  Faild: %d" % (len(function_result["failed"]))).out_infor()
            for eve_failed in function_result["failed"]:
                Operation("    %s" % (eve_failed)).out_infor()
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc()).no_output()

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
            Operation(e, err_msg=traceback.format_exc()).no_output()

        try:
            if len(function_dict) > 0:
                Operation("Deployment is complete and can be triggered by scf remote invoke").information()
                Operation("For example: scf remote invoke -r %s -ns %s -n %s" % (
                    self.region, namespace, function_dict[0]["function"])).information()

                if len(function_dict) == 1 and function_dict[0]['deploy_function']:
                    Information(region=self.region, namespace=namespace,
                                name=function_dict[0]["function"]).get_information()
                else:
                    Operation("If you want to query function information, you can use: scf function info").information()
                    Operation("For example: scf function info -r %s -ns %s -n %s" % (
                        self.region, namespace, function_dict[0]["function"])).information()
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc()).no_output()
