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


@click.command(short_help=help.ADD_SHORT_HELP)
@click.option('--secret-id', help=help.SET_SECRET_ID)
@click.option('--secret-key', help=help.SET_SECRET_KEY)
@click.option('--region', help=help.SET_REGION)
@click.option('--appid', help=help.SET_APPID)
@click.option('--using-cos', help=help.SET_USING_COS)
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
    # if ('USER_'+ str(kwargs['appid'])) in userlist:
    #     Operation("The appid %s exists in config file." % (str(kwargs['appid']))).warning()
    #     return
    if "using_cos" in kwargs and kwargs["using_cos"]:
        kwargs["using_cos"] = using_cos_true if kwargs["using_cos"] not in ["y", "Y"] else using_cos_false

    values = [v for k, v in kwargs.items()]
    if not reduce(lambda x, y: (bool(x) or bool(y)), values):
        list(map(set_true, kwargs))
        attrs = uc.get_attrs(kwargs)
        config = {}
        skip_attr = {'using-cos'}
        for attr in sorted(attrs):
            if attr not in skip_attr:
                while True:
                    v = click.prompt(
                        text="TencentCloud {}".format(attr),
                        default=attrs[attr],
                        show_default=False)
                    # if attr == 'appid':
                    #     # if ('USER_' + str(v)) in userlist:
                    #     #     Operation("The appid %s exists in config file." % (str(kwargs['appid']))).warning()
                    #     #     return
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
            config["using-cos"] = using_cos_true if v not in ["y", "Y"] else using_cos_false
        else:
            config["using-cos"] = attrs["using-cos"]

        kwargs = config

    uc.add_user(data=kwargs)
    uc.flush()
