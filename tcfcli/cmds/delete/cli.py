import os
import click
from cookiecutter.main import cookiecutter
from cookiecutter import exceptions
from tcfcli.libs.utils.scf_client import ScfClient
REGIONS = ['ap-guangzhou', 'ap-shanghai', 'ap-beijing', 'ap-hongkong',
            'ap-chengdu', 'ap-singapore', 'ap-guangzhou-open', 'ap-mumbai']


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


@click.command()
@click.option('--region', type=click.Choice(REGIONS), help="region name")
@click.option('-ns', '--namespace', default="default", help="Namespace name")
@click.option('-n', '--name', required=True, help="Function name")
@click.option('-f', '--force', is_flag=True, callback=abort_if_false, expose_value=False,
              prompt='Are you sure delete this remote function?', help="Force delete function without ask")
def delete(region, namespace, name):
    Delete.do_cli(region, namespace, name)
