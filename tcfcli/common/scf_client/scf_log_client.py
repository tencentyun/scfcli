# -*- coding: utf-8 -*-

import click
import time
from builtins import str as text
from tcfcli.common.operation_msg import Operation
from tencentcloud.scf.v20180416 import models
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
            Operation(log.StartTime, fg="green").echo()
            if log.RetCode == 0:
                Operation(log.Log).echo()
            else:
                Operation(log.Log, fg="red").echo()

    def fetch_log(self, startime, endtime, count, tail=False):
        for logs in self.__fetch_log(startime, endtime, count, tail):
            if len(logs) == 0 and not tail:
                msg = "There is no data during this time period. You can try to adjust the start-time, end-time, duration, etc. to view a larger range of logs. For example:\n    $ scf logs -s xxxx-xx-xx 00:00:00 -e xxxx-xx-xx 00:00:10\n    $ scf logs -n function -d  10"
                Operation(msg).information()
            for log in logs:
                Operation("Log startTime: %s" % str(log.StartTime)).process()

                if log.RetCode == 0:
                    Operation(u"%s" % (text(log.Log)).replace("\n\n", "\n")).echo()
                else:
                    Operation(u"%s" % (text(log.Log)).replace("\n\n", "\n"), fg="red").echo()

                Operation("\n").echo()

    def __fetch_log(self, startime, endtime, count, tail, order="asc"):
        step = 1000
        req = models.GetFunctionLogsRequest()
        req.FunctionName = self._func
        req.StartTime = startime
        req.EndTime = endtime
        req.Order = order
        req.Offset = 0
        req.Namespace = self._ns
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
