import click
import json
import time
import signal
from tcfcli.common.operation_msg import Operation
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

        # fetch in desc, print in asc

    def fetch_log_tail_c(self, startime, endtime, count, tail):
        log_stack = []
        for logs in self.__fetch_log(startime, endtime, count, tail, order="desc"):
            for log in logs:
                log_stack.append(log)
        for i in range(len(log_stack) - 1, -1, -1):
            log = log_stack[i]
            click.secho(log.StartTime, fg="green")
            if log.RetCode == 0:
                click.secho(log.Log)
            else:
                click.secho(log.Log, fg="red")

    def fetch_log(self, startime, endtime, count, tail=False):
        for logs in self.__fetch_log(startime, endtime, count, tail):
            for log in logs:
                Operation("Log startTime: " % str(log.StartTime)).process()
                if log.RetCode == 0:
                    click.secho(str(log.Log).replace("\n\n", "\n"))
                else:
                    click.secho(str(log.Log).replace("\n\n", "\n"), fg="red")
                click.secho("\n\n")

    def __fetch_log(self, startime, endtime, count, tail, order="asc"):
        step = 1000
        req = models.GetFunctionLogsRequest()
        req.FunctionName = self._func
        req.StartTime = startime
        req.EndTime = endtime
        req.Order = order
        req.Offset = 0
        if self._err_only:
            req.Filter = models.Filter()
            req.Filter.RetCode = "not0"
        while count > 0:
            req.Limit = step if step < count else count
            rsp = self.wrapped_err_handle(self._client.GetFunctionLogs, req)
            yield rsp.Data
            c = len(rsp.Data)
            count -= c
            if c < req.Limit and not tail:
                break
            req.Offset += c
            if tail:
                time.sleep(2)
            else:
                time.sleep(0.5)
