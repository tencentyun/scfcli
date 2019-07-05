import click
import json
import time
from tcfcli.common.user_exceptions import InvalidEnvParameters
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.scf.v20180416 import scf_client, models

from . import ScfBaseClient


class ScfLogClient(ScfBaseClient):

    DEFAULT_INTERVAL = 300
    def __init__(self, func, ns="default", region=None, starttime=None, endtime=None, err_only=None):
        super(ScfLogClient, self).__init__(region)
        self._func = func
        self._ns = ns
        self._start = starttime
        self._end = endtime
        self._err_only = err_only        
        if self._start >= self._end:
            raise InvalidEnvParameters("endtime must be greater than starttime")

        


    def fetch_log(self):
        for logs in self.__fetch_log():
            for log in logs:
                click.secho(log.StartTime)
                click.secho(log.Log + "\n*")
                

    def __fetch_log(self):
        req = models.GetFunctionLogsRequest()
        req.FunctionName = self._func
        req.StartTime = self._start
        req.EndTime = self._end
        req.Offset = 0
        req.Limit = 100

        if self._err_only:
            req.Filter = models.Filter()
            req.Filter.RetCode = "not0"
        
        while True:
            rsp = self.wrapped_err_handle(self._client.GetFunctionLogs, req)
            yield rsp.Data
            if rsp.TotalCount < req.Limit:
                break
            req.Offset += req.Limit
            

