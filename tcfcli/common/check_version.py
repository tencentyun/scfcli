# -*- coding: utf-8 -*-

from tcfcli.cmds.cli import __version__
import re
import ssl
import click
import socket
import platform
import time
from tcfcli.common.user_config import UserConfig


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
                url = "https://github.com/tencentyun/scfcli/blob/master/tcfcli/cmds/cli/__init__.py"
                temp_data = urllib.request.urlopen(url) if version >= '3' else urllib2.urlopen(url)
                temp_data = temp_data.read().decode("utf-8")
                regex_str = '<span class="pl-pds">&#39;</span>(.*?)<span class="pl-pds">&#39;</span></span>'
                r_version = re.findall(regex_str, temp_data)[0]
                version_list = __version__.split(".")
                r_version_list = r_version.split(".")
                for i in range(0, len(version_list)):
                    if r_version_list[i] > version_list[i]:
                        uc.set_attrs({'version_time': this_time})
                        uc.flush()
                        click.secho(click.style("""    ----------------------------------------------------
    |                  Upgrade reminder                |
    | Latest version：%s   ,  Your version:   %s |
    | If you want to upgrade, you can use the command: |
    |""" % (r_version, __version__), fg="green") +
                                    click.style("                 pip install -U scf               ", fg="yellow") +
                                    click.style('''|
    ----------------------------------------------------''', fg="green"))
                        break
        except Exception as e:
            pass
    except Exception as e:
        pass
