# -*- coding: utf-8 -*-

from tcfcli.common.operation_msg import Operation
from tcfcli.libs.utils.scf_client import ScfClient
from tcfcli.common.user_exceptions import *
from tcfcli.help.message import FunctionHelp as help
import tcfcli.common.base_infor as infor
from tcfcli.common.user_config import UserConfig

REGIONS = infor.REGIONS
MAX_RESPONSE_ROWS = 1000

class List(object):
    @staticmethod
    def do_cli(region, offset, limit, namespace):
        List.show(region, offset, limit, namespace)

    @staticmethod
    def show(region, offset, limit, namespace):
        status = False
        if region and region not in REGIONS:
            raise ArgsException("region {r} not exists ,please select from{R}".format(r=region, R=REGIONS))
        if not region:
            region = UserConfig().region
            status = True

        rep = ScfClient(region).get_ns(namespace)
        if not rep:
            raise NamespaceException("Region {r} not exist namespace {n}".format(r=region, n=namespace))

        result = ScfClient(region).list_function(offset, limit, namespace)
        if not result:
            Operation("Region {r} namespace {n} not exist function".format(r=region, n=namespace)).warning()
            return

        Operation("Region:%s" % (region)).process()
        Operation("Namespace:%s " % (namespace)).process()
        Operation("Function Total:%s, response %d-%d record." % (result.TotalCount, offset + 1, offset + limit)).process()
        Operation("%-15s %-18s %-25s %-20s %-5s" % ("Runtime", "Status", "AddTime", "ModTime", "FunctionName")).echo()
        for function in result.Functions:
            Operation("%-15s %-22s %-25s %-25s %-5s" % (function.Runtime, List.status(function.Status),
                                                           function.AddTime, function.ModTime,
                                                           function.FunctionName)).echo()
        if status:
            msg = "If you want to get a list of more functions, you can specify the region and namespace. Like: scf function list --region ap-shanghai --namespace default"
            Operation(msg).information()

    @staticmethod
    def status(status_name):
        if status_name == "Active":
            return Operation(status_name, fg="green").style()
        elif "Failed" in status_name:
            return Operation(status_name, fg="red").style()
        else:
            return Operation(status_name, fg="blue").style()


@click.command(name='list', short_help=help.LIST_SHORT_HELP)
@click.option('-r', '--region', help=help.REGION)
@click.option('-ns', '--namespace', default="default", help=help.NAMESPACE)
@click.option('-l', '--limit', default=20, help=help.LIMIT)
@click.option('-o', '--offset', default=0, help=help.OFFSET)
@click.option('--no-color', '-nc', is_flag=True, default=False, help=help.NOCOLOR)
def list(region, namespace, limit, offset, no_color):
    """
        \b
        Show the SCF function list.
        \b
        Common usage:
        \b
            * All function in ap-guangzhou and in namespace default
              $ scf function list --region ap-guangzhou --namespace default
    """
    if limit > MAX_RESPONSE_ROWS:
        limit = MAX_RESPONSE_ROWS
    List.do_cli(region, offset, limit, namespace)
