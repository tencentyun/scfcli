# -*- coding: utf-8 -*-

from tcfcli.common.user_config import UserConfig
from tcfcli.common.operation_msg import Operation
from tcfcli.common.user_exceptions import *
import tcfcli.common.base_infor as infor
from tcfcli.help.message import FunctionHelp as help
from tcfcli.libs.utils.scf_client import ScfClient

REGIONS = infor.REGIONS


class Delete(object):
    @staticmethod
    def do_cli(region, namespace, name):

        rep = ScfClient(region).get_ns(namespace)
        if not rep:
            raise DeleteException("Namespace {ns} not exists".format(ns=namespace))
            # return

        rep = ScfClient(region).get_function(function_name=name, namespace=namespace)
        if not rep:
            raise DeleteException("Function {function} not exists".format(function=name))
            # return

        rep = ScfClient(region).delete_function(function_name=name, namespace=namespace)
        if not rep:
            raise DeleteException("Function {function} delete failed".format(function=name))
            # return

        Operation("Function {function} delete success".format(function=name)).success()


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@click.command(name='delete', short_help=help.DELETE_SHORT_HELP)
@click.option('-r', '--region', type=str, help=help.REGION)
@click.option('-ns', '--namespace', default="default", help=help.NAMESPACE)
@click.option('-n', '--name', help=help.DELETE_NAME)
@click.option('-f', '--force', is_flag=True, help=help.FORCED)
@click.option('--no-color', '-nc', is_flag=True, default=False, help=help.NOCOLOR)

def delete(region, namespace, name, force,no_color):
    '''
        \b
        Delete a SCF function.
        \b
        Common usage:
        \b
            * Delete a SCF function
              $ scf function delete --name functionname --region ap-guangzhou --namespace default
    '''

    if name:

        if not region:
            region = UserConfig().region

        if region and region not in REGIONS:
            raise ArgsException("The region must in %s." % (", ".join(REGIONS)))

        Operation("Function Information:").process()
        Operation("  Region: %s" % (region)).process()
        Operation("  Namespace: %s" % (namespace)).process()
        Operation("  Function Name: %s" % (name)).process()

        if force:
            Delete.do_cli(region, namespace, name)
        else:
            Operation("This function's trigger will be deleted too").warning()
            result = click.prompt(
                Operation('[!] Are you sure delete this remote function? (y/n)', fg="magenta").style())
            if result in ["y", "Y"]:
                Delete.do_cli(region, namespace, name)
            else:
                Operation("Delete operation has been canceled").warning()
    else:
        raise ArgsException("You must give a name, like: scf delete --name YourFunctionName! ")
