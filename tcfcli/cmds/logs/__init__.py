import click
import time
from datetime import datetime
from datetime import timedelta
from tcfcli.cmds.native.common.invoke_context import InvokeContext
from tcfcli.cmds.local.common.options import invoke_common_options
from tcfcli.common.user_exceptions import InvalidEnvParameters
from tcfcli.common.scf_client.scf_log_client import ScfLogClient

@click.command()
@click.option('-n', '--name', help="Function name")
@click.option('-ns', '--namespace',  default="default", help="Namespace name")
@click.option('--region', default=None, help="The region of the service (e.g. ap-guangzhou)")
@click.option('-s', '--start-time', type=str, default=None, help="Fetch logs starting at this time")
@click.option('-e', '--end-time', type=str, default=None, help="Fetch logs up to this time, conflict with --tail")
@click.option('-o', '--offset', type=int, default=1, help="Time offset in minute based on the (start-time|end-time|current)")
@click.option('-f', '--failed',  is_flag=True, default=False, help="Fetch the failed log")
@click.option('-t', '--tail', is_flag=True ,default=False, help="Tail the log output")
def logs(name, namespace, region, start_time, end_time, offset, failed, tail):
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
        Specify a (forward|backward) time offset based on the (start-time|end-time|current) time
        \b
        $ scf logs -n function -o(--offset)  10
        \b
        Fetch logs that was exceptional 
        \b
        $ scf logs -n function  -f(--failed)
        \b
        Specify region of service
        \b
        $ scf logs -n function --region ap-guangzhou
    """

    start, end = _align_time(start_time, end_time, offset, tail)
    client = ScfLogClient(name, namespace, region,  failed)
    client.fetch_log(start, end, tail)




def _align_time(_start, _end, _offset, tail):
    tm_format = '%Y-%m-%d %H:%M:%S'
    start = end = None
    if tail and _end:
        raise InvalidEnvParameters("Endtime is conflict with tail")

    if _start:
        start = datetime.strptime(_start, tm_format)

    if _end:
        end = datetime.strptime(_end, tm_format)
    
    
    # specify starttime and endtime
    if start and end:
        pass
    elif start:  # the combination of starttime and interval
        end = start + timedelta(minutes=_offset)
    elif end:   # the combination of endtime and interval
        start = end - timedelta(minutes=_offset)
    else:
        if tail:
            start = datetime.now()
            end = start + timedelta(days=1)
        else:
            end = datetime.now()
            start = end - timedelta(minutes=_offset)
    if start >= end:
        raise InvalidEnvParameters("endtime must be greater than starttime")
    return start.strftime(tm_format), end.strftime(tm_format)
