# -*- coding: utf-8 -*-

from tcfcli.common.operation_msg import Operation
from tcfcli.libs.utils.scf_client import ScfClient
from tcfcli.common.user_exceptions import *
from tcfcli.help.message import RemoteHelp as help
import tcfcli.common.base_infor as infor
from tcfcli.common.user_config import UserConfig
import json
import chardet

REGIONS = infor.REGIONS
INVOCATION_TYPE = infor.INVOCATION_TYPE


class Invoke(object):
    @staticmethod
    def do_cli(name, region, namespace, eventdata, logtype, invocationtype):
        if region and region not in REGIONS:
            raise ArgsException("region {r} not exists ,please select from{R}".format(r=region, R=REGIONS))
        if not region:
            region = UserConfig().region

        rep = ScfClient(region).get_ns(namespace)
        if not rep:
            raise NamespaceException("Region {r} not exist namespace {n}".format(r=region, n=namespace))

        functions = ScfClient(region).get_function(name, namespace)

        if not functions:
            Operation("Could not found this funtion").warning()
            Operation("You could get function name by: scf function list").warning()
            Operation("This command requires the --name option / -n shortcut. Usage: The function name").warning()
            return

        rep, invokeres = ScfClient(region).invoke_func(name, namespace, eventdata, invocationtype, logtype)

        if not rep:
            Operation("Invoke failed").warning()
            Operation(invokeres).exception()
            return
        else:
            invokeres = json.loads(invokeres)
            # print(invokeres)
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

            if len(invokeres['Result']['Log']) > 4000:
                Operation('You could get more logs by: `scf logs -r %s -ns %s -n %s`' % (
                    region, namespace, name)).information()


@click.command(name='invoke', short_help=help.SHORT_HELP)
@click.option('-n', '--name', help=help.INVOKE_NAME)
@click.option('-r', '--region', help=help.REGION)
@click.option('-ns', '--namespace', default="default", help=help.NAMESPACE)
@click.option('-e', '--eventdata', help=help.EVENTDATA)
@click.option('-t', '--type', default='sync', help=help.INVOCATIONTYPE)
@click.option('--no-color', '-nc', is_flag=True, default=False, help=help.NOCOLOR)
def invoke(name, region, namespace, eventdata, type, no_color):
    """
        \b
        Invoke the SCF remote function.
        \b
        Common usage:
        \b
            * Invoke the function test in ap-guangzhou and in namespace default
              $ scf remote invoke --name test --region ap-guangzhou --namespace default

    """

    type_dict = {
        "sync": "RequestResponse",
        "async": "Event"
    }


    logtype = "tail"

    if type.lower() not in type_dict:
        Operation("Log type must in {l}".format(l=INVOCATION_TYPE)).warning()
        return

    if type.lower == "async":
        Operation('invoke start ,you can get the invoke logs by excute `scf logs -r %s -ns %s -n %s`' % (
            region, namespace, name)).information()

    if eventdata:
        try:
            eventdata = get_data(eventdata)
        except Exception as e:
            raise EventFileException("Read file error: %s" % (str(e)))
    else:
        eventdata = json.dumps({"key1": "value1", "key2": "value2"})

    Invoke.do_cli(name, region, namespace, eventdata, logtype, type_dict[type.lower()])


def get_data(path):
    with open(path, 'rb') as file:  # 先用二进制打开
        data = file.read()  # 读取文件内容
    try:
        return_data = data.decode("utf-8")
    except Exception as e:
        try:
            return_data = data.decode("gbk")
        except Exception as e:
            try:
                return_data = data.decode("ascii")
            except:
                return_data = data.decode(chardet.detect(data).get('encoding'))

    return return_data
