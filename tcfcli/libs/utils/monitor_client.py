# -*- coding: utf-8 -*-

import sys
from tcfcli.common.operation_msg import Operation
from tcfcli.common.user_config import UserConfig
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.monitor.v20180724 import monitor_client, models
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tcfcli.libs.utils.scf_client import ScfClient


class MonitorClient(object):
    CLOUD_API_REQ_TIMEOUT = 30
    ProductNS = 'QCE/SCF_V2'

    def __init__(self, region=None, period=60):
        uc = UserConfig()
        self._cred = credential.Credential(secretId=uc.secret_id, secretKey=uc.secret_key)
        if region is None:
            self._region = uc.region
        else:
            self._region = region
            
        self.period = period
        hp = HttpProfile(reqTimeout=MonitorClient.CLOUD_API_REQ_TIMEOUT)
        cp = ClientProfile("TC3-HMAC-SHA256", hp)
        self._client = monitor_client.MonitorClient(self._cred, self._region, cp)
        self._client._sdkVersion = "TCFCLI"

    def get_data(self, func_name, start_time, end_time, metric):
        try:
            req = models.GetMonitorDataRequest()
            req.Period = self.period
            req.MetricName = metric
            req.Namespace = MonitorClient.ProductNS
            req.StartTime = start_time
            req.EndTime = end_time
            req.Instances = []
            
            version = models.Dimension()
            version.Name = "version"
            version.Value = "$latest"

            funcname = models.Dimension()
            funcname.Name = 'functionName'
            funcname.Value = func_name

            params = models.Instance()
            params.Dimensions = []
            params.Dimensions.append(version)
            params.Dimensions.append(funcname)
            req.Instances.append(params)
            
            return self._client.GetMonitorData(req)
        except TencentCloudSDKException as err:
            if sys.version_info[0] == 3:
                s = err.get_message()
            else:
                s = err.get_message().encode("UTF-8")
            Operation("get data '{name}' failure. Error: {code} {e}.".format(
                name=func_name, code=err.get_code(), e=s)).warning()
        return None
