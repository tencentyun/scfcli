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

    userlist = uc.get_all_user()
    userlist = sorted(userlist)

    # 如果没有传入编号，则进入交互
    if not userid:
        curruser = uc.section_map[UserConfig.OTHERS]['curr_user']
        Operation('Your current user is %s' % curruser).process()
        Operation('%-10s %-15s %-15s %-15s %-15s %-10s' % ('UserId', 'AppId', 'region', 'secret_id', 'secret_key', 'using_cos')).process()
        for user in userlist:
            userinfo = uc.get_user_info(user)
            secret_id = ("*" * 3 + userinfo['secret_id'][32:]) if userinfo['secret_id'] != 'None' else 'None'
            secret_key = ("*" * 3 + userinfo['secret_key'][28:]) if userinfo['secret_key'] != 'None' else 'None'
            Operation('%-10s %-15s %-15s %-15s %-15s %-10s' % (user.strip('USER_'), userinfo['appid'], userinfo['region'],
                      secret_id, secret_key, userinfo['using_cos'][:5])).process()

        v = click.prompt(text="Please choice UserId to change", show_default=False)

    v = userid if userid else v
    if ('USER_'+v) in userlist:
        uc.changeuser(('USER_'+v))
        uc.flush()
        Operation('Your current user has switched to %s' % ('USER_'+v)).success()
    else:
        Operation('error UserId').warning()


