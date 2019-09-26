# -*- coding: utf-8 -*-

from tcfcli.common.operation_msg import Operation
from tcfcli.libs.utils.scf_client import ScfClient
from tcfcli.common.user_exceptions import *
from tcfcli.help.message import RemoteHelp as help
import tcfcli.common.base_infor as infor
from tcfcli.common.user_config import UserConfig
import json


REGIONS = infor.REGIONS
INVOCATION_TYPE = infor.INVOCATION_TYPE
LOG_TYPE = infor.LOG_TYPE


class Invoke(object):
    @staticmethod
    def do_cli(name, region, namespace, eventdata, invocationtype, logtype):
        if region and region not in REGIONS:
            raise ArgsException("region {r} not exists ,please select from{R}".format(r=region, R=REGIONS))
        if not region:
            region = UserConfig().region

        rep = ScfClient(region).get_ns(namespace)
        if not rep:
            raise NamespaceException("Region {r} not exist namespace {n}".format(r=region, n=namespace))

        functions = ScfClient(region).get_function(name, namespace)
        if not functions:
            Operation("Region {r} namespace {n} not exist function {fn}".format(r=region, n=namespace, fn=name)).warning()
            return

        rep, invokeres = ScfClient(region).invoke_func(name, namespace, eventdata, invocationtype, logtype)

        if not rep:
            Operation("Invoke failed").warning()
            Operation(invokeres).exception()
            return
        else:
            invokeres=json.loads(invokeres)
            Operation('Invoke success\n\n'
                      'Response:%s\n\n'
                      'Output:\n%s\n\n'
                      'Summary:\n'
                      'FunctionRequestId:%s\n'
                      'Run Duration:%sms\n'
                      'Bill Duration:%sms\n'
                      'Usage memory:%sB\n\n' %
                      (invokeres['Result']['RetMsg'],
                       invokeres['Result']['Log'],
                       invokeres['Result']['FunctionRequestId'],
                       invokeres['Result']['Duration'],
                       invokeres['Result']['BillDuration'],
                       invokeres['Result']['MemUsage'],
                       )).success()


@click.command(name='invoke', short_help=help.SHORT_HELP)
@click.option('-n', '--name', help=help.INVOKE_NAME)
@click.option('-r', '--region', help=help.REGION)
@click.option('-ns', '--namespace', default="default", help=help.NAMESPACE)
@click.option('-e', '--eventdata', help=help.EVENTDATA)
@click.option('-it', '--invocationtype', default='RequestResponse', help=help.INVOCATIONTYPE)
@click.option('-l', '--type', default='None', help=help.LOGTYPE)
@click.option('--no-color', '-nc', is_flag=True, default=False, help=help.NOCOLOR)
def invoke(name, region, namespace, eventdata, invocationtype, type, no_color):
    """
        \b
        Invoke the SCF remote function.
        \b
        Common usage:
        \b
            * Invoke the function test in ap-guangzhou and in namespace default
              $ scf remote invoke --name test --region ap-guangzhou --namespace default
    """
    if invocationtype.lower() not in INVOCATION_TYPE:
        Operation("InvocationType must in {it}".format(it=INVOCATION_TYPE)).warning()
        return
    if type.lower() not in LOG_TYPE:
        Operation("logtype must in {l}".format(l=LOG_TYPE)).warning()
        return

    if eventdata:
        with open(eventdata, 'r') as f:
            eventdata = f.read()
    else:
        eventdata = json.dumps({"key1": "value1", "key2": "value2"})

    Invoke.do_cli(name, region, namespace, eventdata, invocationtype, type)
