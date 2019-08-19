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
@click.option('--no-color', '-nc', is_flag=True, default=False, help=help.NOCOLOR)
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

    Operation(uc._get_curr_user_section()).process()
    bools = [v for k, v in kwargs.items()]
    if not reduce(lambda x, y: bool(x or y), bools):
        list(map(set_true, kwargs))
    attrs = uc.get_attrs(kwargs)
    msg = "Config" #"{} config:".format(UserConfig.API)
    for attr in sorted(attrs):
        attr_value = attrs[attr]
        if attr == "secret-id":
            attr_value = "*" * 32 + attr_value[32:]
        elif attr == "secret-key":
            attr_value = "*" * 28 + attr_value[28:]
        msg += Operation("\n[-] ", fg="cyan").style() + Operation("{} = {}".format(attr, attr_value), fg="cyan").style()
    Operation(msg.strip()).process()
