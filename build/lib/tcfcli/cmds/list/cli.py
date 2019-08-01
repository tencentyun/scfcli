# -*- coding: utf-8 -*-

from tcfcli.common.operation_msg import Operation
from tcfcli.libs.utils.scf_client import ScfClient
from tcfcli.common.user_exceptions import *
from tcfcli.help.message import ListHelp as help
import tcfcli.common.base_infor as infor

REGIONS = infor.REGIONS


class List(object):
    @staticmethod
    def do_cli(region, namespace):
        if region != 'all' and region not in REGIONS:
            raise ArgsException("! The region must in all, %s." % (", ".join(REGIONS)))

        if region == 'all' and namespace == 'all':
            for region in REGIONS:
                namespaces = ScfClient(region).list_ns()
                for namespace in namespaces:
                    List.show(region, namespace['Name'])

        elif region == 'all' and namespace != 'all':
            for region in REGIONS:
                List.show(region, namespace)

        elif region != 'all' and namespace == 'all':
            namespaces = ScfClient(region).list_ns()
            for namespace in namespaces:
                List.show(region, namespace['Name'])

        elif region != 'all' and namespace != 'all':
            List.show(region, namespace)

    @staticmethod
    def show(region, namespace):
        if region and region not in REGIONS:
            raise ArgsException("region {r} not exists ,please select from{R}".format(r=region, R=REGIONS))
            # return
        rep = ScfClient(region).get_ns(namespace)
        if not rep:
            raise NamespaceException("namespace {ns} not exists".format(ns=namespace))
            # return

        functions = ScfClient(region).list_function(namespace)
        if not functions:
            # click.secho("Region:%s \nNamespace:%s " % (region, namespace), fg="green")
            # click.secho("no function exists\n", fg="red")
            return

        Operation("Region:%s" % (region)).process()
        Operation("Namespace:%s " % (namespace)).process()
        click.secho("%-20s %-15s %-20s %-20s %-60s" % ("Runtime", "Status", "AddTime", "ModTime", "FunctionName"))
        for function in functions:
            click.secho("%-20s %-24s %-20s %-20s %-60s" % (function['Runtime'], List.status(function['Status']),
                                                           function['AddTime'], function['ModTime'],
                                                           function['FunctionName']))
        click.secho("\n")

    @staticmethod
    def status(status_name):
        if status_name == "Active":
            return click.style(status_name, fg="green")
        elif "Failed" in status_name:
            return click.style(status_name, fg="red")
        else:
            return click.style(status_name, fg="blue")


@click.command(short_help=help.SHORT_HELP)
@click.option('--region', default="all", help=help.REGION)
@click.option('-ns', '--namespace', default="all", help=help.NAMESPACE)
def list(region, namespace):
    """
        \b
        Show the SCF function list.
        \b
        Common usage:
        \b
            * All function in ap-guangzhou
              $ scf list --region ap-guangzhou
    """
    List.do_cli(region, namespace)
