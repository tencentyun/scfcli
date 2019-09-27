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


@click.command(short_help=help.SET_SHORT_HELP)
@click.option('--secret-id', '-si', help=help.SET_SECRET_ID)
@click.option('--secret-key', '-sk', help=help.SET_SECRET_KEY)
@click.option('--region', '-r', help=help.SET_REGION)
@click.option('--appid', '-a', help=help.SET_APPID)
@click.option('--using-cos', '-uc', help=help.SET_USING_COS)
@click.option('--python2-path', '-p2p', help=help.SET_PATHON_PATH)
@click.option('--python3-path', '-p3p', help=help.SET_PATHON_PATH)
@click.option('--no-color', '-nc', help=help.NOCOLOR)
@click.option('--allow-report', '-ar', help=help.ALLOW_REPORT)
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

    using_cos_true = "True (By default, it is deployed by COS.)"
    using_cos_false = "False (By default, it isn't deployed by COS.)"

    if "region" in kwargs and kwargs["region"]:
        if kwargs["region"] not in REGIONS:
            Operation("The region must in %s." % (", ".join(REGIONS))).warning()
            kwargs["region"] = uc.region
            return

    if "using_cos" in kwargs and kwargs["using_cos"]:
        kwargs["using_cos"] = using_cos_false if kwargs["using_cos"] not in ["y", "Y"] else using_cos_true

    if "allow_report" in kwargs and kwargs["allow_report"]:
        kwargs["allow_report"] = 'False' if kwargs["allow_report"] not in ["y", "Y"] else 'True'
        if kwargs["allow_report"] == "True":
            Operation('当前已开启数据收集，详情请参考 https://cloud.tencent.com/document/product/583/37766').out_infor()

    if "no_color" in kwargs and kwargs["no_color"]:
        kwargs["no_color"] = 'False' if kwargs["no_color"] not in ["y", "Y"] else 'True'

    values = [v for k, v in kwargs.items()]
    config = {}
    if not reduce(lambda x, y: (bool(x) or bool(y)), values):
        list(map(set_true, kwargs))
        attrs = uc.get_attrs(kwargs)
        skip_attr = {'using_cos', 'python2_path', 'python3_path', 'no_color', 'allow_report'}
        for attr in sorted(attrs):
            if attr not in skip_attr:
                while True:
                    attr_value = attrs[attr]
                    if attr == "secret_id":
                        attr_value = "*" * 32 + attr_value[32:]
                    elif attr == "secret_key":
                        attr_value = "*" * 28 + attr_value[28:]

                    v = click.prompt(
                        text="TencentCloud {}({})".format(attr.replace('_', '-'), attr_value),
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
        v1 = click.prompt(text= ("Show the command information without color(cur:%s). (y/n)") % attrs["no_color"][:5],
                          default="y" if str(attrs["no_color"]).upper().startswith("TRUE") else "n",
                          show_default=False)
        if v1:
            config["no_color"] = "False" if v1 not in ["y", "Y"] else "True"
        else:
            config["no_color"] = attrs["no_color"]

        v2 = click.prompt(text=("Deploy SCF function by COS, it will be faster(cur:%s).  (y/n)") % attrs["using_cos"][:5],
                          default="y" if str(attrs["using_cos"]).upper().startswith("TRUE") else "n",
                          show_default=False)
        if v2:
            config["using_cos"] = using_cos_false if v2 not in ["y", "Y"] else using_cos_true
        else:
            config["using_cos"] = attrs["using_cos"]

        #v3 = click.prompt(text=("Allow report information to help us optimize scfcli(cur:%s). (y/n)") % attrs["allow_report"][:5],
        #                  default="y" if str(attrs["allow_report"]).upper().startswith("TRUE") else "n",
        #                  show_default=False)
        #if v3:
        #    config["allow_report"] = "False" if v3 not in ["y", "Y"] else "True"
        #else:
        #    config["allow_report"] = attrs["allow_report"]

        # if uc.section_map[UserConfig.OTHERS]['allow_report'].upper() == 'TRUE':
        #     Operation('当前已开启数据收集，详情请参考 https://cloud.tencent.com/document/product/583/37766').out_infor()


        kwargs = config

    uc.set_attrs(kwargs)
    uc.flush()




