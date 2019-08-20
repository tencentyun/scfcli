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
@click.option('--userid', '-u', help=help.CHANGE_USERID_HELP)
def change(userid):
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
    curruser = uc.section_map[UserConfig.OTHERS]['curr_user']
    Operation('Your current user is %s' % (curruser)).process()
    userlist = uc.get_all_user()
    userlist = sorted(userlist)
    if not userid:
        Operation('%-10s %-15s %-15s %-10s %-10s %-10s' % ('UserId', 'AppId', 'region', 'secret_id', 'secret_key', 'using_cos')).process()
        for user in userlist:
            userinfo = uc.get_user_info(user)
            Operation('%-10s %-15s %-15s %-10s %-10s %-10s' % (user.strip('USER_'), userinfo['appid'], userinfo['region'],
                      "*" * 3 + userinfo['secret_id'][28:32], "*" * 3 + userinfo['secret_key'][28:32], userinfo['using_cos'][:5])).process()

        v = click.prompt(text="Please choice UserId to change",
                         show_default=False)

    v = userid if userid else v
    if ('USER_'+v) in userlist:
        uc.changeuser(('USER_'+v))
        uc.flush()
    else:
        Operation('error No').warning()


