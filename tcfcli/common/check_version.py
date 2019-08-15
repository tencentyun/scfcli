# -*- coding: utf-8 -*-

from tcfcli.cmds.cli import __version__
import re
import ssl
import click
import socket
import platform
import time
from tcfcli.common.user_config import UserConfig


upgrade_msg = '''



'''

def check_version():
    try:
        version = platform.python_version()

        if version >= '3':
            import urllib.request
        else:
            import urllib2

        socket.setdefaulttimeout(1)
        ssl._create_default_https_context = ssl._create_unverified_context

        try:

            uc = UserConfig()

            # this_time = time.strftime("%W") # week
            this_time = time.strftime("%Y-%m-%d")  # day
            that_time = uc.version_time

            if this_time != that_time:
                url = "https://service-qgphxt7y-1253970226.gz.apigw.tencentcs.com/test/check_version"
                temp_data = urllib.request.urlopen(url) if version >= '3' else urllib2.urlopen(url)
                r_version = temp_data.read().decode("utf-8")[1:-1]
                print(r_version)
                r_version_list = r_version.split(".")
                version_list = __version__.split(".")
                for i in range(0, len(version_list)):
                    if int(r_version_list[i]) > int(version_list[i]):
                        click.secho(click.style("""    ----------------------------------------------------
    |                  Upgrade reminder                |
    | Latest version：%7s  , Your version: %7s |
    | If you want to upgrade, you can use the command: |
    |""" % (r_version, __version__), fg="green") +
                                    click.style("                 pip install -U scf               ", fg="yellow") +
                                    click.style('''|
    ----------------------------------------------------''', fg="green"))
                        break
                uc.set_attrs({'version_time': this_time})
                uc.flush()
        except Exception as e:
            pass
    except Exception as e:
        pass
