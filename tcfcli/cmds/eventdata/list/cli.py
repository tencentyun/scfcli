# -*- coding: utf-8 -*-

import click
from tcfcli.help.message import EventdataHelp as help
from tcfcli.common.operation_msg import Operation
from tcfcli.libs.utils.scf_client import ScfClient
from tcfcli.common.user_exceptions import *
from tcfcli.common.user_config import UserConfig
import tcfcli.common.base_infor as infor

REGIONS = infor.REGIONS


class List(object):
    @staticmethod
    def do_cli(region, namespace, name):
        List.show(region, namespace, name)

    @staticmethod
    def show(region, namespace, name):
        if region and region not in REGIONS:
            raise ArgsException("region {r} not exists ,please select from{R}".format(r=region, R=REGIONS))
        if not region:
            region = UserConfig().region

        rep = ScfClient(region).get_ns(namespace)
        if not rep:
            raise NamespaceException("Region {r} not exist namespace {n}".format(r=region, n=namespace))

        functions = ScfClient(region).get_function(function_name=name, namespace=namespace)
        if not functions:
            raise FunctionNotFound("Region {r} namespace {n} not exist function {f}".format(r=region, n=namespace, f=name))
            return

        Operation("Region:%s" % (region)).process()
        Operation("Namespace:%s " % (namespace)).process()
        Operation("Function:%s " % (name)).process()
        testmodels = ScfClient(region).list_func_testmodel(functionName=name, namespace=namespace)
        if not testmodels:
            raise NamespaceException("This function not exist event".format(f=name))

        Operation("%-20s %-20s %-20s" % ("TestmodelsName", "AddTime", "ModTime")).echo()
        for testmodel in testmodels:
            res = ScfClient(region).get_func_testmodel(functionName=name, namespace=namespace, testModelName=testmodel)
            Operation("%-20s %-20s %-20s" % (testmodel, res['CreatedTime'], res['ModifiedTime'])).echo()
        Operation("\n").echo()


@click.command(name='list', short_help=help.LIST_SHORT_HELP)
@click.option('-r', '--region', help=help.REGION)
@click.option('-ns', '--namespace', default="default", help=help.NAMESPACE)
@click.option('-n', '--name', required=True, help=help.FUNCTION_NAME_HELP)
@click.option('--no-color', '-nc', is_flag=True, default=False, help=help.NOCOLOR)
def list(region, namespace, name, no_color):
    """
        \b
        Show the SCF function event list.
        \b
        Common usage:
        \b
            * All function Events of Function1
              $ scf eventdata list --name Function1
    """

    List.do_cli(region, namespace, name)


