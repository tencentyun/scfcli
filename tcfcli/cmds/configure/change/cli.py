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


@click.command(short_help=help.CHANGE_SHORT_HELP)
def change(**kwargs):
    '''
        \b
        Change your user.
        \b
        Common usage:
            \b
            * Configure change your user
              $ scf configure change
    '''

    uc = UserConfig()
    userlist = uc.get_all_user()
    userlist = sorted(userlist)

    Operation('%-10s %-15s' % ('UserId', 'AppId')).process()
    for user in userlist:
        Operation('%-10s %-15s' % (user.strip('USER_'), uc.get_user_appid(user))).process()

    v = click.prompt(text="Please choice UserId to change",
                     show_default=False)

    if ('USER_'+v) in userlist:
        uc.changeuser(('USER_'+v))
        uc.flush()
    else:
        Operation('error No').warning()


