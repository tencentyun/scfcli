# -*- coding: utf-8 -*-

import click
import platform
import tcfcli.common.base_infor as infor
from tcfcli.help.message import ConfigureHelp as help
from tcfcli.common.user_config import UserConfig
from tcfcli.common.operation_msg import Operation
from tcfcli.common.scf_client.scf_report_client import ScfReportClient

version = platform.python_version()
if version >= '3':
    from functools import reduce


def report_info():
    pass


REGIONS = infor.REGIONS


@click.command(short_help=help.GET_SHORT_HELP)
@click.option('--secret-id', is_flag=True, help=help.GET_SECRET_ID)
@click.option('--secret-key', is_flag=True, help=help.GET_SECRET_KEY)
@click.option('--region', is_flag=True, help=help.GET_REGION)
@click.option('--appid', is_flag=True, help=help.GET_APPID)
@click.option('--using-cos', is_flag=True, help=help.GET_USING_COS)
@click.option('--python2-path', help=help.GET_PATHON_PATH)
@click.option('--python3-path', help=help.GET_PATHON_PATH)
def get(**kwargs):
    '''
        \b
        Get your account parameters.
        \b
        Common usage:
            \b
            * Get the configured information
              $ scf configure get
        '''
    uc = UserConfig()

    def set_true(k):
        kwargs[k] = True

    bools = [v for k, v in kwargs.items()]
    if not reduce(lambda x, y: bool(x or y), bools):
        list(map(set_true, kwargs))
    attrs = uc.get_attrs(kwargs)
    msg = "{} config:".format(UserConfig.API)
    for attr in sorted(attrs):
        attr_value = attrs[attr]
        if attr == "secret-id":
            attr_value = "*" * 32 + attr_value[32:]
        elif attr == "secret-key":
            attr_value = "*" * 28 + attr_value[28:]
        msg += click.style("\n[-] ", fg="cyan") + click.style("{} = {}".format(attr, attr_value), fg="cyan")
    Operation(msg.strip()).process()


@click.command(short_help=help.SET_SHORT_HELP)
@click.option('--secret-id', help=help.SET_SECRET_ID)
@click.option('--secret-key', help=help.SET_SECRET_KEY)
@click.option('--region', help=help.SET_REGION)
@click.option('--appid', help=help.SET_APPID)
@click.option('--using-cos', help=help.SET_USING_COS)
@click.option('--python2-path', help=help.SET_PATHON_PATH)
@click.option('--python3-path', help=help.SET_PATHON_PATH)
def set(**kwargs):
    '''
        \b
        Configure your account parameters.
        \b
        Common usage:
            \b
            * Configure your account parameters
              $ scf configure set
            \b
            * Modify a configuration item
              $ scf configure set --region ap-shanghai
    '''

    def set_true(k):
        kwargs[k] = True

    uc = UserConfig()

    using_cos_true = "False (By default, it isn't deployed by COS.)"
    using_cos_false = "True (By default, it is deployed by COS.)"

    if "region" in kwargs and kwargs["region"]:
        if kwargs["region"] not in REGIONS:
            Operation("The region must in %s." % (", ".join(REGIONS))).warning()
            kwargs["region"] = uc.region
            return

    if "using_cos" in kwargs and kwargs["using_cos"]:
        kwargs["using_cos"] = using_cos_true if kwargs["using_cos"] not in ["y", "Y"] else using_cos_false

    values = [v for k, v in kwargs.items()]
    if not reduce(lambda x, y: (bool(x) or bool(y)), values):
        list(map(set_true, kwargs))
        attrs = uc.get_attrs(kwargs)
        config = {}
        skip_attr = {'using-cos', 'python2-path', 'python3-path'}
        for attr in sorted(attrs):
            if attr not in skip_attr:
                while True:
                    attr_value = attrs[attr]
                    if attr == "secret-id":
                        attr_value = "*" * 32 + attr_value[32:]
                    elif attr == "secret-key":
                        attr_value = "*" * 28 + attr_value[28:]

                    v = click.prompt(
                        text="TencentCloud {}({})".format(attr, attr_value),
                        default=attrs[attr],
                        show_default=False)
                    config[attr] = v

                    if attr != "region":
                        break
                    else:
                        if v in REGIONS:
                            break
                        else:
                            Operation("The region must in %s." % (", ".join(REGIONS))).warning()

        v = click.prompt(text="Deploy SCF function by COS, it will be faster. (y/n)",
                         default="y" if str(attrs["using-cos"]).startswith("True") else "n",
                         show_default=False)

        if v:
            config["using_cos"] = using_cos_true if v not in ["y", "Y"] else using_cos_false
        else:
            config["using_cos"] = attrs["using-cos"]

        kwargs = config

    uc.set_attrs(kwargs)
    uc.flush()

    if not reduce(lambda x, y: (bool(x) or bool(y)), values):
        v = click.prompt(text="Allow report information to help us optimize scfcli. (y/n)",
                         default="y",
                         show_default=False)
        if v in ["y", "Y"]:
            client = ScfReportClient()
            client.report()


@click.group(name='configure', short_help=help.SHORT_HELP)
def configure():
    """
        \b
        You need to perform initial configuration and configure the account information in the configuration file of scf cli for subsequent use.
        \b
        Common usage:
            \b
            * Configure your account parameters
              $ scf configure set
            \b
            * Modify a configuration item
              $ scf configure set --region ap-shanghai
            \b
            * Get the configured information
              $ scf configure get
    """


configure.add_command(get)
configure.add_command(set)
