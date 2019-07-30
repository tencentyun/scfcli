import os
import click
from cookiecutter.main import cookiecutter
from cookiecutter import exceptions
from tcfcli.libs.utils.scf_client import ScfClient
from tcfcli.help.message import ListHelp as help
import tcfcli.common.base_infor as infor

REGIONS = infor.REGIONS


class List(object):
    @staticmethod
    def do_cli(region, namespace):
        if region != 'all' and region not in REGIONS:
            click.secho("! The region must in all, %s." % (", ".join(REGIONS)), fg="red")

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
            click.secho("region {r} not exists ,please select from{R}".format(r=region, R=REGIONS), fg="red")
            return
        rep = ScfClient(region).get_ns(namespace)
        if not rep:
            click.secho("namespace {ns} not exists".format(ns=namespace), fg="red")
            return

        functions = ScfClient(region).list_function(namespace)
        if not functions:
            # click.secho("Region:%s \nNamespace:%s " % (region, namespace), fg="green")
            # click.secho("no function exists\n", fg="red")
            return

        click.secho("Region:%s \nNamespace:%s " % (region, namespace), fg="green")
        click.secho("%-15s %-15s %-20s %-20s %-60s" % ("Runtime", "Status", "AddTime", "ModTime", "FunctionName"))
        for function in functions:
            click.secho("%-15s %-15s %-20s %-20s %-60s" % (function['Runtime'], function['Status'], function['AddTime'],
                                                           function['ModTime'], function['FunctionName']))
        click.secho("\n")


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
