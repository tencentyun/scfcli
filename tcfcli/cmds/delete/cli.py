import os
import click
from cookiecutter.main import cookiecutter
from cookiecutter import exceptions
from tcfcli.common.operation_msg import Operation
from tcfcli.common.user_exceptions import *
import tcfcli.common.base_infor as infor
from tcfcli.help.message import DeleteHelp as help
from tcfcli.libs.utils.scf_client import ScfClient

REGIONS = infor.REGIONS


class Delete(object):
    @staticmethod
    def do_cli(region, namespace, name):

        if region and region not in REGIONS:
            raise ArgsException("The region must in %s." % (", ".join(REGIONS)))
        else:
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


@click.command(short_help=help.SHORT_HELP)
@click.option('-r', '--region', type=str, help=help.REGION)
@click.option('-ns', '--namespace', default="default", help=help.NAMESPACE)
@click.option('-n', '--name', required=True, help=help.NAME)
@click.option('-f', '--force', is_flag=True, callback=abort_if_false, expose_value=False,
              prompt='Are you sure delete this remote function?', help=help.FORCED)
def delete(region, namespace, name):
    '''
        \b
        Delete a SCF function.
        \b
        Common usage:
        \b
            * Delete a SCF function
              $ scf delete --name functionname --region ap-guangzhou --namespace default
    '''
    Delete.do_cli(region, namespace, name)
