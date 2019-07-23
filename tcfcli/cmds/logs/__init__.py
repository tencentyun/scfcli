import click
import time
from datetime import datetime
from datetime import timedelta
from tcfcli.cmds.native.common.invoke_context import InvokeContext
from tcfcli.cmds.local.common.options import invoke_common_options
from tcfcli.common.user_exceptions import InvalidEnvParameters
from tcfcli.common.scf_client.scf_log_client import ScfLogClient

TM_FORMAT = '%Y-%m-%d %H:%M:%S'
@click.command()
@click.option('-n', '--name', help="Function name")
@click.option('-ns', '--namespace',  default="default", help="Namespace name")
@click.option('--region', default=None, help="The region of the service (e.g. ap-guangzhou)")
@click.option('-c', '--count', type=int,
    help="The count of logs,the maximum value is 10000 and the minimum value is 1")
@click.option('-s', '--start-time', type=str, default=None, help="Fetch logs starting at this time, conflict with --tail")
@click.option('-e', '--end-time', type=str, default=None, help="Fetch logs up to this time, conflict with --tail")
@click.option('-d', '--duration', type=int, default=None, help="The duration between starttime and current time(unit:second)")
@click.option('-f', '--failed',  is_flag=True, default=False, help="Fetch the failed log")
@click.option('-t', '--tail', is_flag=True ,default=False, help="Tail the log output")
def logs(name, namespace, region, count, start_time, end_time, duration, failed, tail):
    """
    \b
    Fetch logs of scf from service.
    Common usage:
        \b
        Fetch logs using the function's name
        \b
        $ scf logs -n(--name) function
        \b
        Specify a namespace, the default value is 'default'
        \b
        $ scf logs -n function -ns(--namespace) nodefault
        \b
        Specific time range using the -s (--starttime) and -e (--endtime) options
        \b
        $ scf logs -n function -s xxxx-xx-xx 00:00:00 -e xxxx-xx-xx 00:00:10
        \b
        Specify a duration between starttime and current time(unit:second)
        \b
        $ scf logs -n function -d(--duration)  10
        \b
        Fetch logs that was exceptional 
        \b
        $ scf logs -n function  -f(--failed)
        \b
        Specify region of service
        \b
        $ scf logs -n function --region ap-guangzhou
    """
    if name is None:
        raise InvalidEnvParameters("Function name is unspecified")

    if duration and (start_time or end_time):
        raise InvalidEnvParameters("Duration is conflict with (start_time, end_time)")

    if tail:
        start = datetime.now()
        end = start + timedelta(days=1)
        if count:
            end = start
            start = end - timedelta(days=1)
    else:    
        start, end = _align_time(start_time, end_time, duration)
    client = ScfLogClient(name, namespace, region,  failed)
    if tail and count:
        client.fetch_log_tail_c(start.strftime(TM_FORMAT), 
            end.strftime(TM_FORMAT), count, tail)
        return
    if not count:
        count = 10000  #cloudapi limit
    client.fetch_log(start.strftime(TM_FORMAT), end.strftime(TM_FORMAT), count, tail)




def _align_time(_start, _end, _offset):
    start = end = None
    if _start:
        start = datetime.strptime(_start, TM_FORMAT)

    if _end:
        end = datetime.strptime(_end, TM_FORMAT)
    
    
    if _offset:
        end = datetime.now()
        start = end - timedelta(seconds=_offset)
    elif start and end:
        pass
    elif (not start) and (not end):
        end = datetime.now()
        start = end - timedelta(seconds=60)  
    elif not start:
        raise InvalidEnvParameters("start-time name is unspecified")
    else:
        raise InvalidEnvParameters("end-time name is unspecified")

    if start >= end:
        raise InvalidEnvParameters("endtime must be greater than starttime")
    return start, end
