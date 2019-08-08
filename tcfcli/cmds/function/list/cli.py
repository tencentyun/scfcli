# -*- coding: utf-8 -*-

from tcfcli.common.operation_msg import Operation
from tcfcli.libs.utils.scf_client import ScfClient
from tcfcli.common.user_exceptions import *
from tcfcli.help.message import FunctionHelp as help
import tcfcli.common.base_infor as infor
from tcfcli.common.user_config import UserConfig

REGIONS = infor.REGIONS


class List(object):
    @staticmethod
    def do_cli(region, namespace):
        List.show(region, namespace)

    @staticmethod
    def show(region, namespace):
        if region and region not in REGIONS:
            raise ArgsException("region {r} not exists ,please select from{R}".format(r=region, R=REGIONS))
        if not region:
            region = UserConfig().region

        rep = ScfClient(region).get_ns(namespace)
        if not rep:
            raise NamespaceException("Region {r} not exist namespace {n}".format(r=region, n=namespace))

        functions = ScfClient(region).list_function(namespace)
        if not functions:
            Operation("Region {r} namespace {n} not exist function".format(r=region, n=namespace)).warning()
            return

        Operation("Region:%s" % (region)).process()
        Operation("Namespace:%s " % (namespace)).process()
        click.secho("%-20s %-15s %-20s %-20s %-60s" % ("Runtime", "Status", "AddTime", "ModTime", "FunctionName"))
        for function in functions:
            click.secho("%-20s %-24s %-20s %-20s %-60s" % (function.Runtime, List.status(function.Status),
                                                           function.AddTime, function.ModTime,
                                                           function.FunctionName))
        click.secho("\n")

    @staticmethod
    def status(status_name):
        if status_name == "Active":
            return click.style(status_name, fg="green")
        elif "Failed" in status_name:
            return click.style(status_name, fg="red")
        else:
            return click.style(status_name, fg="blue")


@click.command(name='list', short_help=help.LIST_SHORT_HELP)
@click.option('--region', '-r', help=help.REGION)
@click.option('-ns', '--namespace', default="default", help=help.NAMESPACE)
def list(region, namespace):
    """
        \b
        Show the SCF function list.
        \b
        Common usage:
        \b
            * All function in ap-guangzhou
              $ scf function list --region ap-guangzhou
    """
    List.do_cli(region, namespace)
