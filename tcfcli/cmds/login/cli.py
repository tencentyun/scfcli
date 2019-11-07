# -*- coding: utf-8 -*-
import webbrowser
import click
import time
import sys
from threading import Thread, Event
from tcfcli.common.operation_msg import Operation
from tcfcli.common.user_config import UserConfig
from tcfcli.common.http_server import HttpServer, HttpResponse
from tcfcli.help.message import LoginHelp as help

appId = '100005789219'
redirectUrl = 'http://scfdev.tencentserverless.com/login'
authUrl = 'https://cloud.tencent.com/open/authorize?scope=login&app_id=%s&redirect_url=%s' % (appId, redirectUrl)
event = Event()
config = {}

class HttpService(Thread):
    def __init__(self, addr = '0.0.0.0', port = 19527):
        Thread.__init__(self)
        self.httpd = HttpServer(addr, port) 
        self.httpd.addRoute('get', '/authorization/token', handlerToken)

    def run(self):
        self.httpd.start()

    def stop(self):
        self.httpd.stop()

def handlerToken(request):
    if request.query is None:
        return True, HttpResponse('invalid param', 412)

    if 'token' not in request.query:
        return True, HttpResponse('token invalid param', 412)
    if 'secretId' not in request.query:
        return True, HttpResponse('secretId invalid param', 412)
    if 'secretKey' not in request.query:
        return True, HttpResponse('secretKey invalid param', 412)

    config['secret_id'] = request.query['secretId']
    config['secret_key'] = request.query['secretKey']
    config['token'] = request.query['token']

    event.set()
    return True, HttpResponse('success')

@click.command(short_help=help.SHORT_HELP)
@click.option('-r', '--region', help=help.REGION)
def login(region):
    uc = UserConfig()
    if uc.appid and uc.appid != 'None': 
        Operation("Current user already is login status").information()
        return
    else:
        pass

    success = webbrowser.open_new_tab(authUrl)
    if not success:
        Operation("Open browser access authorize page faild.").exception()
        sys.exit(1)
    Operation("Please login in the open browser").process()

    httpd = HttpService()
    httpd.daemon = True
    httpd.start()

    while True:
        if event.isSet() is True:
            break
        time.sleep(1)
    event.wait()
    httpd.stop()
    event.clear()
    Operation("Login success. please set the region").process()
    if region == None:
        region = click.prompt(text= ("TencentCloud region(default: ap-guangzhou)"), default='ap-guangzhou',
                        show_default=False)
    config['region'] = region

    uc.set_attrs(config)
    uc.flush()




