import click
import platform
from tcfcli.common.user_config import UserConfig
from tcfcli.common.scf_client.scf_report_client import ScfReportClient
version = platform.python_version()
if version >= '3':
    from functools import reduce

def report_info():
    pass


@click.command()
@click.option('--secret-id', is_flag=True, help="TencentCloudAPI  SecretId")
@click.option('--secret-key', is_flag=True, help="TencentCloudAPI  SecretKey")
@click.option('--region', is_flag=True,  help="TencentCloudAPI  Region")
@click.option('--appid', is_flag=True, help="TencentCloudAPI  Appid")
def get(**kwargs):
    uc = UserConfig()
    def set_true(k):
        kwargs[k] = True
    bools = [v for k, v in kwargs.items()]
    if not reduce(lambda x, y: bool(x or y), bools):
        list(map(set_true, kwargs))
    attrs = uc.get_attrs(kwargs)
    msg = "{} config:\n".format(UserConfig.API)
    for attr in sorted(attrs):
        attr_value = attrs[attr]
        if attr == "secret-id":
            attr_value = "*"*32 + attr_value[32:]
        elif attr == "secret-key":
            attr_value = "*"*28 + attr_value[28:]
        msg += "{} = {}\n".format(attr, attr_value)
    click.secho(msg.strip())


@click.command()
@click.option('--secret-id', help="TencentCloudAPI  SecretId")
@click.option('--secret-key', help="TencentCloudAPI  SecretKey")
@click.option('--region', help="TencentCloudAPI  Region")
@click.option('--appid', help="TencentCloudAPI  Region")
def set(**kwargs):
    def set_true(k):
        kwargs[k] = True
    uc = UserConfig()
    values = [v for k, v in kwargs.items()]
    if not reduce(lambda x, y: (bool(x) or bool(y)), values):
        list(map(set_true, kwargs))
        attrs = uc.get_attrs(kwargs)
        config = {}
        for attr in sorted(attrs):
            attr_value = attrs[attr]
            if attr == "secret-id":
                attr_value = "*"*32 + attr_value[32:]
            elif attr == "secret-key":
                attr_value = "*"*28 + attr_value[28:]
            v = click.prompt(
                text="TencentCloud {}({})".format(attr, attr_value),
                default=attrs[attr],
                show_default=False)
            config[attr] = v
        kwargs = config
    uc.set_attrs(kwargs)
    uc.flush()
    if not reduce(lambda x, y: (bool(x) or bool(y)), values):
        v = click.prompt(text="Allow report information to help us optimize scfcli(Y/n)",
            default="y",
            show_default=False)
        if v in ["y", "Y"]:
            client = ScfReportClient()
            client.report()


@click.group(name='configure')
def configure():
    """
    Configure your account parameters
    \b
    e.g. scf configure set --region ap-beijing
    \b
    e.g. scf configure get --region
    \b
    Type the cmd 'scf configure set' without option into the interactive mode
    \b
    Type the cmd 'scf configure set' without option return all configurations
    """


configure.add_command(get)
configure.add_command(set)
