# -*- coding: utf-8 -*-

import json
import sys
import traceback
from tcfcli.cmds.cli import __version__
from tcfcli.common.user_exceptions import *
from tcfcli.common.operation_msg import Operation
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.scf.v20180416 import scf_client, models
from tcfcli.common.scf_client import scf_service_models
from tcfcli.common.user_config import UserConfig
from tcfcli.common.tcsam.tcsam_macro import TcSamMacro as tsmacro
from tcfcli.common.tcsam.tcsam_macro import TriggerMacro as trmacro
import base64


class FunctionStatus(object):
    FUNC_STATUS_FAILED       = -1
    #
    # function status
    FUNC_STATUS_ACTIVE       = 0
    FUNC_STATUS_UPDATING     = 1
    FUNC_STATUS_UPDATEFAILED = 2
    FUNC_STATUS_CREATING     = 3
    FUNC_STATUS_CREATEFAILED = 4

class ResourceStatus(object):
    #
    # resource status
    RESOURCE_STATUS_FUNC_NOT_EXISTS = 1
    RESOURCE_STATUS_FUNC_EXISTS = 2

class ScfClient(object):
    CLOUD_API_REQ_TIMEOUT = 120

    def __init__(self, region=None):
        uc = UserConfig()
        self._cred = credential.Credential(secretId=uc.secret_id, secretKey=uc.secret_key)
        if region is None:
            self._region = uc.region
        else:
            self._region = region
        hp = HttpProfile(reqTimeout=ScfClient.CLOUD_API_REQ_TIMEOUT)
        cp = ClientProfile("TC3-HMAC-SHA256", hp)
        self._client = scf_client.ScfClient(self._cred, self._region, cp)
        self._client._sdkVersion = "TCFCLI"
        self._client_ext = ScfClientExt(self._cred, self._region, cp)
        self._client_ext._sdkVersion = "TCFCLI_" + __version__

    def get_function(self, function_name=None, namespace='default'):
        try:
            req = models.GetFunctionRequest()
            req.FunctionName = function_name
            req.Namespace = namespace
            resp = self._client.GetFunction(req)
            return resp.to_json_string()
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            if sys.version_info[0] == 3:
                s = err.get_message()
            else:
                s = err.get_message().encode("UTF-8")
        return None

    def delete_function(self, function_name=None, namespace='default'):
        try:
            req = models.DeleteFunctionRequest()
            req.FunctionName = function_name
            req.Namespace = namespace
            resp = self._client.DeleteFunction(req)
            return resp.to_json_string()
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            if sys.version_info[0] == 3:
                s = err.get_message()
            else:
                s = err.get_message().encode("UTF-8")
        return None

    def list_function(self, offset=0, limit=20, namespace='default'):
        try:
            req = models.ListFunctionsRequest()
            req.Offset = offset
            req.Limit = limit
            req.Namespace = namespace
            req.Type = 'Event'
            return self._client.ListFunctions(req)
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            if sys.version_info[0] == 3:
                s = err.get_message()
            else:
                s = err.get_message().encode("UTF-8")
            Operation("list functions failure. Error: {e}.".format(e=s)).warning()
        return None

    def update_func_code(self, func, func_name, func_ns):
        req = models.UpdateFunctionCodeRequest()
        req.Namespace = func_ns
        req.FunctionName = func_name
        proper = func.get(tsmacro.Properties, {})
        req.Handler = proper.get(tsmacro.Handler)
        req.ZipFile = self._model_zip_file(proper.get(tsmacro.LocalZipFile))
        req.CosBucketName = proper.get(tsmacro.CosBucketName)
        req.CosObjectName = proper.get(tsmacro.CosObjectName)
        resp = self._client.UpdateFunctionCode(req)
        return resp.to_json_string()

    def update_func_config(self, func, func_name, func_ns):
        req = models.UpdateFunctionConfigurationRequest()
        req.Namespace = func_ns
        req.FunctionName = func_name
        proper = func.get(tsmacro.Properties, {})
        req.Description = proper.get(tsmacro.Desc)
        req.MemorySize = proper.get(tsmacro.MemSize)
        req.Timeout = proper.get(tsmacro.Timeout)
        req.Role = proper.get(tsmacro.Role)
        req.Environment = self._model_envs(proper.get(tsmacro.Envi, {}))
        req.VpcConfig = self._model_vpc(proper.get(tsmacro.VpcConfig))
        resp = self._client.UpdateFunctionConfiguration(req)
        return resp.to_json_string()

    def update_service_code(self, func, func_name, func_ns):
        req = scf_service_models.UpdateFunctionCodeRequest()
        req.Namespace = func_ns
        req.FunctionName = func_name
        proper = func.get(tsmacro.Properties, {})
        req.Handler = proper.get(tsmacro.Handler)
        req.CosBucketName = proper.get(tsmacro.CosBucketName)
        req.CosObjectName = proper.get(tsmacro.CosObjectName)
        resp = self._client.UpdateFunctionCode(req)
        return resp.to_json_string()

    def update_service_config(self, func, func_name, func_ns):
        req = scf_service_models.UpdateFunctionConfigurationRequest()
        req.Namespace = func_ns
        req.FunctionName = func_name
        proper = func.get(tsmacro.Properties, {})
        req.Description = proper.get(tsmacro.Desc)
        req.Environment = self._model_envs(proper.get(tsmacro.Envi, {}))
        req.VpcConfig = self._model_vpc(proper.get(tsmacro.VpcConfig))
        resp = self._client.UpdateFunctionConfiguration(req)
        return resp.to_json_string()

    def create_func(self, func, func_name, func_ns):
        req = models.CreateFunctionRequest()
        req.Namespace = func_ns
        req.FunctionName = func_name
        proper = func.get(tsmacro.Properties, {})
        req.Handler = proper.get(tsmacro.Handler)
        req.Description = proper.get(tsmacro.Desc)
        req.MemorySize = proper.get(tsmacro.MemSize)
        req.Timeout = proper.get(tsmacro.Timeout)
        req.Runtime = proper.get(tsmacro.Runtime)
        req.Role = proper.get(tsmacro.Role)
        if req.Runtime:
            req.Runtime = req.Runtime[0].upper() + req.Runtime[1:].lower()
        req.Environment = self._model_envs(proper.get(tsmacro.Envi, {}))
        req.VpcConfig = self._model_vpc(proper.get(tsmacro.VpcConfig))
        req.Code = self._model_code(proper.get(tsmacro.LocalZipFile),
                                    proper.get(tsmacro.CosBucketName),
                                    proper.get(tsmacro.CosObjectName))
        resp = self._client.CreateFunction(req)
        return resp.to_json_string()

    def create_service(self, func, func_name, func_ns):
        req = scf_service_models.CreateFunctionRequest()
        req.Namespace = func_ns
        req.FunctionName = func_name
        proper = func.get(tsmacro.Properties, {})
        req.Handler = proper.get(tsmacro.Handler)
        req.Description = proper.get(tsmacro.Desc)
        req.MemorySize = proper.get(tsmacro.MemSize)
        req.Runtime = proper.get(tsmacro.Runtime)
        req.Type = proper.get(tsmacro.Type)
        if req.Runtime:
            req.Runtime = req.Runtime[0].upper() + req.Runtime[1:].lower()
        req.Environment = self._model_envs(proper.get(tsmacro.Envi, {}))
        req.VpcConfig = self._model_vpc(proper.get(tsmacro.VpcConfig))
        req.Code = self._model_code(proper.get(tsmacro.LocalZipFile),
                                    proper.get(tsmacro.CosBucketName),
                                    proper.get(tsmacro.CosObjectName))
        resp = self._client.CreateFunction(req)
        return resp.to_json_string()

    def deploy_func(self, func, func_name, func_ns):
        '''

        :param func:
        :param func_name:
        :param func_ns:
        :param forced:
        :return: 0 : success
                 1 : error in-use
                 2 : only in-use
                 e : error
        '''
        try:
            # SERVICE_RUNTIME_SUPPORT_LIST = ["Nodejs8.9-service"]
            # if 'Type' in func['Properties'] and func['Properties']['Type'] == 'HTTP' and \
            # func['Properties']['Runtime'] in SERVICE_RUNTIME_SUPPORT_LIST:
            # self.create_service(func, func_name, func_ns)
            # else:
            self.create_func(func, func_name, func_ns)
            return True, None
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            # if err.code in ["ResourceInUse.Function", "ResourceInUse.FunctionName"]:
                # return False, RESOURCE_STATUS_FUNC_NOT_EXISTS
            return False, err

    def update_config(self, func, func_name, func_ns):
        try:
            self.update_func_config(func, func_name, func_ns)
            return True
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            return err

    def update_code(self, func, func_name, func_ns):
        try:
            self.update_func_code(func, func_name, func_ns)
            return True
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            return err

    def create_trigger(self, trigger, name, func_name, func_ns):
        req = models.CreateTriggerRequest()
        req.Namespace = func_ns
        req.FunctionName = func_name
        req.TriggerName = name
        trigger_type = trigger.get(tsmacro.Type, "")
        req.Type = trigger_type.lower()
        proper = trigger.get(tsmacro.Properties, {})
        if trmacro.Message in proper:
            req.CustomArgument = proper[trmacro.Message]
        if trigger_type == tsmacro.TrCOS and trmacro.Bucket in proper:
            req.TriggerName = proper[trmacro.Bucket]
        if trigger_type in [tsmacro.TrCMQ] and trmacro.Name in proper:
            req.TriggerName = proper[trmacro.Name]
        if trigger_type in [tsmacro.TrCKafka] and trmacro.Name in proper:
            req.TriggerName = proper[trmacro.Name] + "-" + proper.get(trmacro.Topic)
        self._fill_trigger_req_desc(req, trigger_type, proper)
        enable = proper.get(trmacro.Enable)
        if isinstance(enable, bool):
            enable = ["CLOSE", "OPEN"][int(enable)]
        req.Enable = enable
        self._client.CreateTrigger(req)

    def delete_trigger(self, trigger, func_name, func_ns):
        req = models.DeleteTriggerRequest()
        req.Namespace = func_ns
        req.FunctionName = func_name
        req.TriggerName = trigger["TriggerName"]
        req.Type = str(trigger["Type"]).lower()
        req.Qualifier = "$LATEST"
        req.TriggerDesc = json.dumps(trigger["TriggerDesc"])
        self._client.DeleteTrigger(req)

    def get_ns(self, namespace):
        try:
            resp = self._client_ext.ListAllNamespaces()
            namespaces = resp.get("Namespaces", [])
            for ns_dict in namespaces:
                if namespace == ns_dict.get("Name"):
                    return namespace
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            if sys.version_info[0] == 3:
                s = err.get_message()
            else:
                s = err.get_message().encode("UTF-8")
            Operation("get namespace '{name}' failure. Error: {e}.".format(
                name=namespace, e=s)).warning()
        return None

    def create_ns(self, namespace):
        try:
            self._client_ext.CreateNamespace(namespace)
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            return err
        return

    def list_ns(self):
        try:
            resp = self._client_ext.ListAllNamespaces()
            namespaces = resp.get("Namespaces", [])
            return namespaces
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            if sys.version_info[0] == 3:
                s = err.get_message()
            else:
                s = err.get_message().encode("UTF-8")
            Operation("list namespace failure. Error: {e}.".format(e=s)).warning()
        return None

    def create_func_testmodel(self, functionName, testModelValue, testModelName, namespace):
        try:
            self._client_ext.CreateFunctionTestModel(functionName=functionName, testModelValue=testModelValue,
                                                     testModelName=testModelName, namespace=namespace)
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            return err
        return

    def update_func_testmodel(self, functionName, testModelValue, testModelName, namespace):
        try:
            self._client_ext.UpdateFunctionTestModel(functionName=functionName, testModelValue=testModelValue,
                                                     testModelName=testModelName, namespace=namespace)
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            return err
        return

    def list_func_testmodel(self, functionName, namespace):
        try:
            resp = self._client_ext.ListFunctionTestModels(functionName=functionName, namespace=namespace)
            testmodels = resp.get("TestModels", [])
            return testmodels
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            if sys.version_info[0] == 3:
                s = err.get_message()
            else:
                s = err.get_message().encode("UTF-8")
            Operation("list testmodels failure. Error: {e}.".format(e=s)).warning()
        return None

    def get_func_testmodel(self, functionName, testModelName, namespace):
        try:
            resp = self._client_ext.GetFunctionTestModel(functionName=functionName, testModelName=testModelName,
                                                         namespace=namespace)
            return resp
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            if sys.version_info[0] == 3:
                s = err.get_message()
            else:
                s = err.get_message().encode("UTF-8")
            Operation("list testmodels failure. Error: {e}.".format(e=s)).warning()
        return None

    def invoke_func(self, functionName, namespace, eventdata, invocationType, logtype):
        try:
            req = models.InvokeRequest()
            req.FunctionName = functionName
            req.Namespace = namespace
            req.ClientContext = eventdata
            req.InvocationType = invocationType
            req.LogType = logtype
            resp = self._client.Invoke(req)
            return True, resp.to_json_string()
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            if sys.version_info[0] == 3:
                s = err.get_message()
            else:
                s = err.get_message().encode("UTF-8")
        return False, s

    @staticmethod
    def _fill_trigger_req_desc(req, t, proper):
        if t == tsmacro.TrTimer:
            desc = proper.get(trmacro.CronExp)
        elif t == tsmacro.TrApiGw:
            ir_flag = proper.get(trmacro.IntegratedResp, False)
            isIntegratedResponse = "TRUE" if ir_flag else "FALSE"
            service_name = {"serviceName": "SCF_API_SERVICE"}
            service_id = {"serviceId": proper.get('ServiceId', None)}
            service_temp = service_id if service_id["serviceId"] else service_name
            desc = {
                "api": {
                    "authRequired": "FALSE",
                    "requestConfig": {
                        "method": proper.get(trmacro.HttpMethod, None)
                    },
                    "isIntegratedResponse": isIntegratedResponse
                },
                "service": service_temp,
                "release": {
                    "environmentName": proper.get(trmacro.StageName, None)
                }
            }
            desc = json.dumps(desc, separators=(',', ':'))
        elif t == tsmacro.TrCMQ:
            # desc = proper.get(trmacro.Name, name)
            desc = None

        elif t == tsmacro.TrCOS:
            desc = {"event": proper.get(tsmacro.Events), "filter": proper.get(trmacro.Filter)}
            desc = json.dumps(desc, separators=(',', ':'))
        elif t == tsmacro.TrCKafka:
            desc = {"maxMsgNum": str(proper.get(trmacro.MaxMsgNum)), "offset": proper.get(trmacro.Offset)}
            desc = json.dumps(desc, separators=(',', ':'))
        else:
            raise Exception("Invalid trigger type:{}".format(str(t)))
        req.TriggerDesc = desc

    def deploy_trigger(self, trigger, name, func_name, func_ns):
        try:
            self.create_trigger(trigger, name, func_name, func_ns)
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            return err

    def remove_trigger(self, trigger, func_name, func_ns):
        try:
            self.delete_trigger(trigger, func_name, func_ns)
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            return err

    def deploy(self, func, func_name, func_ns, forced):
        err = self.deploy_func(func, func_name, func_ns, forced)
        if err:
            return err

    @staticmethod
    def _model_envs(environment):
        envs_array = []
        vari = environment.get(tsmacro.Vari, {})
        for k in vari:
            var = models.Variable()
            var.Key = k
            var.Value = vari[k]
            envs_array.append(var)
        envi = models.Environment()
        envi.Variables = envs_array
        return envi

    @staticmethod
    def _model_vpc(vpc_config):
        if vpc_config:
            vpc = models.VpcConfig()
            vpc.VpcId = vpc_config.get("VpcId", None)
            vpc.SubnetId = vpc_config.get("SubnetId", None)
            return vpc
        return None

    @staticmethod
    def _model_code(zip_file, cos_buk_name, cos_obj_name):
        code = models.Code()
        code.CosBucketName = cos_buk_name
        code.CosObjectName = cos_obj_name
        if zip_file:
            with open(zip_file, 'rb') as f:
                code.ZipFile = base64.b64encode(f.read()).decode('utf-8')
        return code

    @staticmethod
    def _model_zip_file(zip_file):
        if zip_file:
            with open(zip_file, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        return None


class ScfClientExt(scf_client.ScfClient):
    def ListAllNamespaces(self):
        try:
            maxResponseCount = 1000
            totalCount = 0
            request = {
                'Offset': 0,
                'Limit': 100,
            }

            body = self.call("ListNamespaces", request)
            response = json.loads(body)
            if "Error" in response["Response"]:
                code = response["Response"]["Error"]["Code"]
                message = response["Response"]["Error"]["Message"]
                reqid = response["Response"]["RequestId"]
                raise TencentCloudSDKException(code, message, reqid)
            totalCount = response["Response"]['TotalCount']
            request['Offset'] += len(response["Response"]['Namespaces'])
            totalCount -= request['Offset']

            while totalCount > 0 and maxResponseCount > 0:

                body = self.call("ListNamespaces", request)
                result = json.loads(body)
                if "Error" in result["Response"]:
                    code = result["Response"]["Error"]["Code"]
                    message = result["Response"]["Error"]["Message"]
                    reqid = result["Response"]["RequestId"]
                    raise TencentCloudSDKException(code, message, reqid)

                response['Response']['Namespaces'] += result['Response']['Namespaces']
                listLength = len(result["Response"]['Namespaces'])
                request['Offset'] += listLength
                totalCount -= listLength
                maxResponseCount -= listLength
            
            return response['Response']

        except Exception as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            raise TCSDKException(str(e))

    def ListNamespaces(self):
        try:
            request = {
                'Offset': 0,
                'Limit': 20,
            }
            body = self.call("ListNamespaces", request)
            response = json.loads(body)
            if "Error" not in response["Response"]:
                return response["Response"]
            else:
                code = response["Response"]["Error"]["Code"]
                message = response["Response"]["Error"]["Message"]
                reqid = response["Response"]["RequestId"]
                raise TencentCloudSDKException(code, message, reqid)
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            raise TCSDKException(str(e))
            # if isinstance(e, TencentCloudSDKException):
            #     raise
            # else:
            #     raise TencentCloudSDKException(e.message, e.message)

    def CreateNamespace(self, namespace):
        try:
            request = {
                'Namespace': namespace,
                'Description': namespace,
                'Type': 'default'
            }
            body = self.call("CreateNamespace", request)
            response = json.loads(body)
            if "Error" not in response["Response"]:
                return response["Response"]
            else:
                code = response["Response"]["Error"]["Code"]
                message = response["Response"]["Error"]["Message"]
                reqid = response["Response"]["RequestId"]
                raise TencentCloudSDKException(code, message, reqid)
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            raise TCSDKException(str(e))
            # if isinstance(e, TencentCloudSDKException):
            #     raise
            # else:
            #     raise TencentCloudSDKException(e.message, e.message)

    def CreateFunctionTestModel(self, functionName, testModelValue, testModelName, namespace):
        try:
            request = {
                'FunctionName': functionName,
                'TestModelValue': testModelValue,
                'TestModelName': testModelName,
                'Namespace': namespace,
            }
            body = self.call("CreateFunctionTestModel", request)
            response = json.loads(body)
            if "Error" not in response["Response"]:
                return response["Response"]
            else:
                code = response["Response"]["Error"]["Code"]
                message = response["Response"]["Error"]["Message"]
                reqid = response["Response"]["RequestId"]
                raise TencentCloudSDKException(code, message, reqid)
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            raise TCSDKException(str(e))

    def UpdateFunctionTestModel(self, functionName, testModelValue, testModelName, namespace):
        try:
            request = {
                'FunctionName': functionName,
                'TestModelValue': testModelValue,
                'TestModelName': testModelName,
                'Namespace': namespace,
            }
            body = self.call("UpdateFunctionTestModel", request)
            response = json.loads(body)
            if "Error" not in response["Response"]:
                return response["Response"]
            else:
                code = response["Response"]["Error"]["Code"]
                message = response["Response"]["Error"]["Message"]
                reqid = response["Response"]["RequestId"]
                raise TencentCloudSDKException(code, message, reqid)
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            raise TCSDKException(str(e))

    def ListFunctionTestModels(self, functionName, namespace):
        try:
            request = {
                'FunctionName': functionName,
                'Namespace': namespace,
            }
            body = self.call("ListFunctionTestModels", request)
            response = json.loads(body)
            if "Error" not in response["Response"]:
                return response["Response"]
            else:
                code = response["Response"]["Error"]["Code"]
                message = response["Response"]["Error"]["Message"]
                reqid = response["Response"]["RequestId"]
                raise TencentCloudSDKException(code, message, reqid)
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            raise TCSDKException(str(e))

    def GetFunctionTestModel(self, functionName, testModelName, namespace):
        try:
            request = {
                'FunctionName': functionName,
                'TestModelName': testModelName,
                'Namespace': namespace,
            }
            body = self.call("GetFunctionTestModel", request)
            response = json.loads(body)
            if "Error" not in response["Response"]:
                return response["Response"]
            else:
                code = response["Response"]["Error"]["Code"]
                message = response["Response"]["Error"]["Message"]
                reqid = response["Response"]["RequestId"]
                raise TencentCloudSDKException(code, message, reqid)
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            raise TCSDKException(str(e))


"""
    def ListFunctions(self, namespace):
        try:
            request = {
                'Offset': 0,
                'Limit': 20,
                'Namespace': namespace
            }
            body = self.call("ListFunctions", request)
            response = json.loads(body)
            if "Error" not in response["Response"]:
                return response["Response"]
            else:
                code = response["Response"]["Error"]["Code"]
                message = response["Response"]["Error"]["Message"]
                reqid = response["Response"]["RequestId"]
                raise TencentCloudSDKException(code, message, reqid)
        except Exception as e:
            raise TCSDKException(e)
            # if isinstance(e, TencentCloudSDKException):
            #     raise
            # else:
            #     raise TencentCloudSDKException(e.message, e.message)
"""
