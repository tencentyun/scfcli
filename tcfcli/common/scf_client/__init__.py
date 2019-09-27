# -*- coding: utf-8 -*-

import traceback
from tcfcli.cmds.cli import __version__
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.scf.v20180416 import scf_client, models
from tcfcli.common.user_config import UserConfig
from tcfcli.common.user_exceptions import LogsException
from tcfcli.common.operation_msg import Operation


class ScfBaseClient(object):
    CLOUD_API_REQ_TIMEOUT = 5

    def __init__(self, region=None):
        uc = UserConfig()
        self._cred = credential.Credential(secretId=uc.secret_id, secretKey=uc.secret_key)
        if region is None:
            self._region = uc.region
        else:
            self._region = region
        hp = HttpProfile(reqTimeout=ScfBaseClient.CLOUD_API_REQ_TIMEOUT)
        cp = ClientProfile("TC3-HMAC-SHA256", hp)
        self._client = scf_client.ScfClient(self._cred, self._region, cp)
        self._client._sdkVersion = "TCFCLI_" + __version__

    @staticmethod
    def wrapped_err_handle(apifunc, req):
        try:
            return apifunc(req)
        except TencentCloudSDKException as err:
            Operation(err, err_msg=traceback.format_exc(), level="ERROR").no_output()
            requestId = err.get_request_id()
            errmsg = err.get_message()
            if requestId:
                errmsg = errmsg + " RequestId:{}".format(requestId)
            raise LogsException(errmsg)
