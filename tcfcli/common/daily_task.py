# -*- coding: utf-8 -*-

from tcfcli.cmds.cli import __version__
import ssl
import click
import socket
import platform
import time
import json
from tcfcli.common.statistics import StatisticsConfigure
from tcfcli.common.operation_msg import Operation
from tcfcli.common.user_config import UserConfig


def output_msg(local_version, release_version, message):
    upgrade_command_msg_start = Operation("""    |                 """, fg="green").style()
    upgrade_command_msg_middl = Operation("""pip install -U scf""", fg="yellow").style()
    upgrade_command_msg_end = Operation("""               |""", fg="green").style()
    Operation("""    ----------------------------------------------------""", fg="green").echo()
    Operation("""    |                  Upgrade reminder                |""", fg="green").echo()
    Operation("""    | Latest version：%7s  , Your version: %7s |""" % (release_version, local_version),
              fg="green").echo()
    Operation("""    | If you want to upgrade, you can use the command: |""", fg="green").echo()
    Operation(upgrade_command_msg_start + upgrade_command_msg_middl + upgrade_command_msg_end).echo()
    Operation("""    ----------------------------------------------------""", fg="green").echo()
    if message:
        for eve_msg in message:
            Operation(eve_msg).information()


def daily_task():
    try:
        version = platform.python_version()

        if version >= '3':
            import urllib.request as openurl
        else:
            import urllib2 as openurl

        socket.setdefaulttimeout(1.2)
        ssl._create_default_https_context = ssl._create_unverified_context

        try:

            uc = UserConfig()

            now_time = time.strftime("%Y-%m-%d")  # day
            version_time = uc.version_time
            allow_report = uc.section_map[UserConfig.OTHERS]['allow_report']
            #print allow_report
            if now_time != version_time:
                url = "https://service-qgphxt7y-1253970226.gz.apigw.tencentcs.com/release/client_daily_task"
                post_data = None
                if allow_report.upper() == 'TRUE':
                    statistics = StatisticsConfigure()
                    statistics.read_data()
                    post_data = statistics.get_data()
                    statistics.delete_data()
                # print post_data
                if not post_data:
                    post_data = {}
                post_data["appid"] = uc.appid
                post_data["version"] = __version__
                post_data = json.dumps(post_data) if post_data else "{}"
                request = openurl.Request(data=post_data.encode("utf-8") if version >= '3' else post_data,
                                          url=url) if version >= '3' else openurl.Request(url, data=post_data)
                # print openurl.urlopen(request).read()
                response = json.loads(openurl.urlopen(request).read().decode("utf-8"))
                if not isinstance(response, dict):
                    response = json.loads(response.encode('utf-8'))
                release_version = response["version"]
                message = response["message"]
                release_version_list = release_version.split(".")
                local_version_list = __version__.split(".")
                for i in range(0, len(release_version_list)):
                    if int(release_version_list[i]) > int(local_version_list[i]):
                        output_msg(__version__, release_version, message)
                        break
                uc.set_attrs({'version_time': now_time})
                uc.flush()
        except Exception as e:
            # print e
            pass

    except Exception as e:
        pass


def get_version():
    version = platform.python_version()

    if version >= '3':
        import urllib.request as openurl
    else:
        import urllib2 as openurl

    socket.setdefaulttimeout(1.2)
    ssl._create_default_https_context = ssl._create_unverified_context

    url = "https://service-qgphxt7y-1253970226.gz.apigw.tencentcs.com/release/client_daily_task"
    post_data = "{}"
    request = openurl.Request(data=post_data.encode("utf-8") if version >= '3' else post_data,
                              url=url) if version >= '3' else openurl.Request(url, data=post_data)
    response = json.loads(json.loads(openurl.urlopen(request).read().decode("utf-8")))
    release_version = response["version"]
    message = response["message"]
    release_version_list = release_version.split(".")
    local_version_list = __version__.split(".")
    for i in range(0, len(release_version_list)):
        if int(release_version_list[i]) > int(local_version_list[i]):
            return {"version": release_version, "message": message}

    return {}
