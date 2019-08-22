# -*- coding: utf-8 -*-

import click
import pytz
import datetime
import time
import sys
from dateutil.tz import *
from tcfcli.help.message import StatHelp as help
from tcfcli.common.user_exceptions import InvalidEnvParameters
from tcfcli.libs.utils.monitor_client import MonitorClient
# from tzlocal import get_localzone

@click.command(short_help=help.SHORT_HELP)
@click.option('-p', '--period', type=int, default=60, help=help.PERIOD)
@click.option('-n', '--name', type=str, default=None, help=help.NAME)
@click.option('-ns', '--namespace', type=str, default="default", help=help.NAMESPACE)
@click.option('-r', '--region', type=str, help=help.REGION)
@click.option('--starttime', type=str, help=help.STARTTIME)
@click.option('--endtime', type=str, help=help.ENDTIME)
@click.option('-m', '--metric', type=str, help=help.METRIC)
def stat(period, name, namespace, region, starttime, endtime, metric):
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
        startTime = datetime.datetime.now()
    if not endTime:
        endTime = startTime + datetime.timedelta(hours=1)

    if endTime <= startTime:
        raise InvalidEnvParameters('endtime cannot lt starttime')

    metrics = None
    if not metric:
        metrics = defaultMetrics
    else:
        metrics = metric.split(',')

    strStarTime = datetime.datetime.strftime(startTime, '%Y-%m-%d %H:%M:%S')
    strEndTime  = datetime.datetime.strftime(endTime, '%Y-%m-%d %H:%M:%S')
    
    monitorCli = MonitorClient(region, period)
    metricResp = []
    for k, val in enumerate(metrics):
        resp = monitorCli.get_data(name, namespace, strStarTime, strEndTime, val)
        if resp and resp.DataPoints:
            metricResp.append(resp)

    columnsFmt = []
    padding = []
    for k, name in enumerate(metrics):
        name = name.lower()
        if name == 'mem':
            name = name + '(MB)'
        elif name == 'duration':
            name = name + '(ms)'
        elif name == 'functionerrorpercentage' \
            or name == 'servererrorpercentage':
            name = name + '(%)'

        paddnum = len(name) + 4
        padding.append(paddnum)
        fmt = ('{: ^%d}') % (paddnum)
        columnsFmt.append(fmt.format(name))
    columnsFmt = ['{: ^17}'.format('time')] + columnsFmt

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
            paddingFmt = ('{: ^%d}') % (padding[k])

            if not v:
                values.append(paddingFmt.format('0'))
            else:
                values.append(paddingFmt.format(v))
        print(' '.join(values))
        sys.stdout.flush()
        startTime = startTime + datetime.timedelta(seconds=period)
