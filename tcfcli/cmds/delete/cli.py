import os
import click
from cookiecutter.main import cookiecutter
from cookiecutter import exceptions
from tcfcli.help.message import DeleteHelp as help
from tcfcli.libs.utils.scf_client import ScfClient


class Delete(object):
    @staticmethod
    def do_cli(region, namespace, name):
        rep = ScfClient(region).get_ns(namespace)
        if not rep:
            click.secho("namespace {ns} not exists".format(ns=namespace), fg="red")
            return

        rep = ScfClient(region).get_function(function_name=name, namespace=namespace)
        if not rep:
            click.secho("function {function} not exists".format(function=name), fg="red")
            return

        rep = ScfClient(region).delete_function(function_name=name, namespace=namespace)
        if not rep:
            click.secho("function {function} delete failed".format(function=name), fg="red")
            return

        click.secho("function {function} delete success".format(function=name), fg="green")


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
