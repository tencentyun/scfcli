import click
import json
import time
import signal
from tcfcli.common.user_exceptions import InvalidEnvParameters
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.scf.v20180416 import scf_client, models

from . import ScfBaseClient


class ScfLogClient(ScfBaseClient):

    DEFAULT_INTERVAL = 300
    def __init__(self, func, ns="default", region=None, err_only=None):
        super(ScfLogClient, self).__init__(region)
        self._func = func
        self._ns = ns
        self._err_only = err_only        



    def fetch_log(self, startime, endtime=None, tail=False):
        for logs in self.__fetch_log(startime, endtime, tail):
            for log in logs:
                click.secho(log.StartTime, fg="green")
                if log.RetCode == 0:
                    click.secho(log.Log)
                else:
                    click.secho(log.Log, fg="red")
                

    def __fetch_log(self, startime, endtime, tail):
        req = models.GetFunctionLogsRequest()
        req.FunctionName = self._func
        req.StartTime = startime
        req.EndTime = endtime
        req.Order = "asc"
        req.Offset = 0
        req.Limit = 1000
        if self._err_only:
            req.Filter = models.Filter()
            req.Filter.RetCode = "not0"
        while True:
            rsp = self.wrapped_err_handle(self._client.GetFunctionLogs, req)
            yield rsp.Data
            count = len(rsp.Data)
            if count < req.Limit and not tail:
                break
            req.Offset += count
            if tail:
                time.sleep(2)
            else:
                time.sleep(0.5)
            

