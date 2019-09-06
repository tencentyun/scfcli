# -*- coding: utf-8 -*-

import click
import platform
import tcfcli.common.base_infor as infor
from tcfcli.help.message import ConfigureHelp as help
from tcfcli.common.user_config import UserConfig
from tcfcli.common.operation_msg import Operation

version = platform.python_version()
if version >= '3':
    from functools import reduce


def report_info():
    pass


REGIONS = infor.REGIONS


@click.command(short_help=help.ADD_SHORT_HELP)
@click.option('--secret-id', '-si', help=help.SET_SECRET_ID)
@click.option('--secret-key', '-sk', help=help.SET_SECRET_KEY)
@click.option('--region', '-r', help=help.SET_REGION)
@click.option('--appid', '-a', help=help.SET_APPID)
@click.option('--using-cos', '-uc', help=help.SET_USING_COS)
def add(**kwargs):
    '''
        \b
        Add a user.
        \b
        Common usage:
            \b
            * Add a user.
              $ scf configure add
    '''

    def set_true(k):
        kwargs[k] = True

    uc = UserConfig()

    using_cos_true = "False (By default, it isn't deployed by COS.)"
    using_cos_false = "True (By default, it is deployed by COS.)"

    if "region" in kwargs and kwargs["region"]:
        if kwargs["region"] not in REGIONS:
            Operation("The region must in %s." % (", ".join(REGIONS))).warning()
            kwargs["region"] = uc.section_map[UserConfig.USER_QCLOUD_CONFIG]['region']
            return
    if "using_cos" in kwargs and kwargs["using_cos"]:
        kwargs["using_cos"] = using_cos_true if kwargs["using_cos"] not in ["y", "Y"] else using_cos_false

    values = [v for k, v in kwargs.items()]
    if not reduce(lambda x, y: (bool(x) or bool(y)), values):
        list(map(set_true, kwargs))
        attrs = uc.get_attrs(kwargs)
        config = {}
        skip_attr = {'using_cos'}
        for attr in sorted(attrs):
            if attr not in skip_attr:
                while True:
                    v = click.prompt(
                        text="TencentCloud {}".format(attr),
                        default=None,
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
                         default="y" if str(attrs["using_cos"]).startswith("True") else "n",
                         show_default=False)

        if v:
            config["using_cos"] = using_cos_true if v not in ["y", "Y"] else using_cos_false
        else:
            config["using_cos"] = attrs["using_cos"]

        kwargs = config

    user = uc.add_user(data=kwargs)
    uc.flush()
    Operation('Add User %s success!' % user).success()
    Operation(user).process()
    Operation('%-10s %-15s %-15s %-15s %-15s %-10s' % ('UserId', 'AppId', 'region', 'secret_id', 'secret_key', 'using_cos')).process()
    userinfo = uc.get_user_info(user)
    secret_id = ("*" * 3 + userinfo['secret_id'][32:]) if userinfo['secret_id'].upper() != 'NONE' else 'None'
    secret_key = ("*" * 3 + userinfo['secret_key'][28:]) if userinfo['secret_key'].upper() != 'NONE' else 'None'
    Operation('%-10s %-15s %-15s %-15s %-15s %-10s' % (user.strip('USER_'), userinfo['appid'], userinfo['region'],
                                                       secret_id, secret_key, userinfo['using_cos'][:5])).process()
    Operation('You can use `scf configure change -u %s` to switch user.' % (user.strip('USER_'))).process()
