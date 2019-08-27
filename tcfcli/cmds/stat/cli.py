# -*- coding: utf-8 -*-

import click
import pytz
import datetime
import time
import sys
from dateutil.tz import *
import tcfcli.common.base_infor as infor
from tcfcli.common.user_exceptions import *
from tcfcli.libs.utils.scf_client import ScfClient
from tcfcli.help.message import StatHelp as help
from tcfcli.common.operation_msg import Operation
from tcfcli.common.user_exceptions import InvalidEnvParameters
from tcfcli.libs.utils.monitor_client import MonitorClient

metricTables = {
    'Duration': 'Duration(ms)',
    'Invocation': 'Invocation',
    'Error': 'Error',
    'ConcurrentExecutions': 'Concurrency',
    'ConfigMem': 'ConfigMem(MB)',
    'FunctionErrorPercentage': 'FuncErrRate(%)',
    'Http2xx': 'Http2xx',
    'Http432': 'Http432',
    'Http433': 'Http433',
    'Http434': 'Http434',
    'Http4xx': 'Http4xx',
    'Mem': ' Mem(MB)',
    'MemDuration': 'MemDuration(MB/ms)',
    'OutFlow': 'OutFlow',
    'ServerErrorPercentage': 'SvrErrRage(%)',
    'Syserr': 'Syserr',
    'Throttle': 'Throttle'
}

@click.command(short_help=help.SHORT_HELP)
@click.option('-p', '--period', type=int, default=60, help=help.PERIOD)
@click.option('-n', '--name', type=str, default=None, help=help.NAME)
@click.option('-r', '--region', type=str, help=help.REGION)
@click.option('--starttime', type=str, help=help.STARTTIME)
@click.option('--endtime', type=str, help=help.ENDTIME)
@click.option('-m', '--metric', type=str, help=help.METRIC)
def stat(period, name, region, starttime, endtime, metric):
    if name is None:
        raise InvalidEnvParameters("function name is unspecif")

    startTime = None
    endTime = None
    defaultMetrics = [
        'Invocation',
        'Duration',
        'Mem',
        'Error',
        'FunctionErrorPercentage',
    ]

    if not (period == 60 or period == 300):
        raise InvalidEnvParameters('period %s invalid. value is 60 or 300' % period)

    if region and region not in infor.REGIONS:
        raise ArgsException("The region must in %s." % (", ".join(infor.REGIONS)))

    namespaces = ScfClient(region).list_ns()
    if not namespaces:
        Operation("Region {r} not exist namespace".format(r=region)).warning()
        return

    flag = True
    for key, namespace in enumerate(namespaces):
        if flag == False:
            break

        functions = ScfClient(region).list_function(namespace['Name'])
        if functions:
            for k, func in enumerate(functions):
                if name == func.FunctionName:
                    flag = False
                    break

    if flag:
        raise InvalidEnvParameters('function %s not exist' % name)

    if starttime:
        try:
            startTime = datetime.datetime.strptime(starttime,'%Y-%m-%d %H:%M:%S')
        except Exception as e:
            raise InvalidEnvParameters(e)

    if endtime:
        if startTime == None:
            raise InvalidEnvParameters('starttime value unspecif')
        try:
            endTime = datetime.datetime.strptime(endtime,'%Y-%m-%d %H:%M:%S')
        except Exception as e:
            raise InvalidEnvParameters(e)

    if not startTime:
        startTime = datetime.datetime.now() + datetime.timedelta(hours=-1)
    if not endTime:
        endTime = datetime.datetime.now()

    if endTime <= startTime:
        raise InvalidEnvParameters('endtime cannot lt starttime')

    nowUnixTime = int(time.mktime(startTime.timetuple()))
    secDiff = nowUnixTime % period
    startTime = startTime + datetime.timedelta(seconds=-secDiff)

    metrics = []
    if not metric:
        metrics = defaultMetrics
    else:
        tmpArr = metric.split(',')
        for k, m in enumerate(tmpArr):
            try:
                if metricTables[m]:
                    metrics.append(m)
            except Exception as e:
                Operation("metric name '{name}' invalid.".format(name=m)).warning()
    if not len(metrics):
        return

    strStarTime = datetime.datetime.strftime(startTime, '%Y-%m-%d %H:%M:%S')
    strEndTime  = datetime.datetime.strftime(endTime, '%Y-%m-%d %H:%M:%S')

    metricResp = []
    columnsFmt = []
    padding = []
    monitorCli = MonitorClient(region, period)
    for k, val in enumerate(metrics):
        resp = monitorCli.get_data(name, strStarTime, strEndTime, val)
        if resp and resp.DataPoints:
            metricResp.append(resp)

        paddnum = len(metricTables[val]) + 4
        padding.append(paddnum)
        fmt = ('{:>%d}') % (paddnum)
        columnsFmt.append(fmt.format(metricTables[val]))

        # reduce server concurrency
        time.sleep(0.1) 

    columnsFmt = ['{: ^17}'.format('Time')] + columnsFmt

    print(' '.join(columnsFmt))
    while (startTime <= endTime):
        strTime = datetime.datetime.strftime(startTime, '%y%m%d %H:%M:%S')
        timestamp = int(time.mktime(startTime.timetuple()))

        values = ['{: ^17}'.format(strTime)]
        for k, metric in enumerate(metricResp):
            length = len(metric.DataPoints[0].Timestamps)
            v = None
            paddingRight = ''
            for i in range(length):
                if timestamp == metric.DataPoints[0].Timestamps[i]:
                    v = str(metric.DataPoints[0].Values[i])
                    break
            paddingFmt = ('{:>%d}') % (padding[k])

            if not v:
                values.append(paddingFmt.format('0'))
            else:
                values.append(paddingFmt.format(v))
        print(' '.join(values))
        sys.stdout.flush()
        startTime = startTime + datetime.timedelta(seconds=period)
