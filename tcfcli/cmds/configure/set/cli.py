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


@click.command(short_help=help.SET_SHORT_HELP)
@click.option('--secret-id', help=help.SET_SECRET_ID)
@click.option('--secret-key', help=help.SET_SECRET_KEY)
@click.option('--region', help=help.SET_REGION)
@click.option('--appid', help=help.SET_APPID)
@click.option('--using-cos', help=help.SET_USING_COS)
@click.option('--python2-path', help=help.SET_PATHON_PATH)
@click.option('--python3-path', help=help.SET_PATHON_PATH)
@click.option('--no-color', '-nc', is_flag=True, default=False, help=help.NOCOLOR)
@click.option('--allow-report', '-ar', is_flag=True, default=False, help=help.ALLOW_REPORT)
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
        skip_attr = {'using-cos', 'python2-path', 'python3-path', 'no-color', 'allow-report'}
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

        #
        v1 = click.prompt(text="Show the command information without color. (y/n)",
                          default="y" if str(attrs["using-cos"]).startswith("True") else "n",
                          show_default=False)
        if v1:
            config["no-color"] = "False" if v1 not in ["y", "Y"] else "True"
        else:
            config["no-color"] = attrs["no-color"]

        v2 = click.prompt(text="Deploy SCF function by COS, it will be faster. (y/n)",
                          default="y" if str(attrs["using-cos"]).startswith("True") else "n",
                          show_default=False)
        if v2:
            config["using_cos"] = using_cos_true if v2 not in ["y", "Y"] else using_cos_false
        else:
            config["using_cos"] = attrs["using-cos"]

        v3 = click.prompt(text="Allow report information to help us optimize scfcli. (y/n)",
                          default="y",
                          show_default=False)
        if v3:
            config["allow_report"] = "False" if v3 not in ["y", "Y"] else "True"
        else:
            config["allow_report"] = attrs["allow_report"]

        kwargs = config

    uc.set_attrs(kwargs)
    uc.flush()

