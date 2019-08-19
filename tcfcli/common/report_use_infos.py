# -*- coding: utf-8 -*-

# -*- coding:utf-8 -*-
import platform
import ssl
import socket
import json
import time
from tcfcli.common.user_config import UserConfig


def report_use_infos():
    try:
        uc = UserConfig()
        data = {}
        data['appid'] = uc.appid
        data['region'] = uc.region

        version = platform.python_version()
        if version >= '3':
            from urllib.request import Request, urlopen
        else:
            from urllib2 import Request, urlopen

        try:
            socket.setdefaulttimeout(1)
            ssl._create_default_https_context = ssl._create_unverified_context

            url = 'https://service-qgphxt7y-1253970226.gz.apigw.tencentcs.com/release/scf_operation_report'
            postdata = json.dumps(data)

            if version >= '3':
                req = Request(url, data=postdata.encode("utf-8"))
            else:
                req = Request(url, data=postdata)
            res = urlopen(req)

        except Exception:
            pass
    except Exception as e:
        pass
