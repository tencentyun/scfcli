# -*- coding: utf-8 -*-

from tcfcli.help.message import EventdataHelp as help
from tcfcli.common.operation_msg import Operation
from tcfcli.libs.utils.scf_client import ScfClient
from tcfcli.common.user_exceptions import *
from tcfcli.common.user_config import UserConfig
import tcfcli.common.base_infor as infor
import os
import json

REGIONS = infor.REGIONS


class Update(object):
    @staticmethod
    def get_event_from_file(path):
        try:
            with click.open_file(path, 'r', encoding="utf-8") as f:
                event = f.read()
                json.loads(event)
        except Exception as e:
            Operation(str(e) + '\nPlease check your json file {%s} format.' % path).warning()
            return None

        filefullname = os.path.split(path)[1]
        filename = os.path.splitext(filefullname)[0]
        return {filename: event}

    @staticmethod
    def update_event_data(region, namespace, name, eventdatalist, forced):
        region = region if region else UserConfig().region

        if region not in REGIONS:
            raise ArgsException("region {r} not exists ,please select from{R}".format(r=region, R=REGIONS))

        if not ScfClient(region).get_ns(namespace):
            raise NamespaceException("Region {r} not exist namespace {n}".format(r=region, n=namespace))

        if not ScfClient(region).get_function(function_name=name, namespace=namespace):
            raise FunctionNotFound("Region {r} namespace {n} not exists function {f}".format(r=region, n=namespace, f=name))

        Operation("Region:%s" % (region)).process()
        Operation("Namespace:%s " % (namespace)).process()
        Operation("Function:%s " % (name)).process()

        flag = False
        for eventdata in eventdatalist:
            if Update.do_deploy_testmodel(functionName=name, namespace=namespace, region=region, forced=forced,
                                          event=list(eventdata.values())[0], event_name=list(eventdata.keys())[0]):
                flag = True
        if flag:
            Operation("If you want to cover remote eventdata.You can use command with option -f").exception()

    @staticmethod
    def do_deploy_testmodel(functionName, namespace, region, forced, event, event_name):
            # 获取失败抛出异常会直接创建新模版
            # 获取成功代表已有模版，根据force是否覆盖
        try:
            ScfClient(region).get_func_testmodel(functionName=functionName, testModelName=event_name,
                                                 namespace=namespace)
            if not forced:
                Operation("Eventdata {%s} exist in remote" % event_name).exception()
                return True
            else:
                Operation("Eventdata {%s} exist in remote,updating event..." % event_name).process()
                ScfClient(region).update_func_testmodel(functionName=functionName, testModelValue=event,
                                                        testModelName=event_name, namespace=namespace)
                Operation("Eventdata {%s} update success!" % event_name).success()
        except:
            Operation("Updateing eventdata {%s}..." % event_name).process()
            ScfClient(region).create_func_testmodel(functionName=functionName, testModelValue=event,
                                                    testModelName=event_name, namespace=namespace)
            Operation("Eventdata {%s} update success!" % event_name).success()

    @staticmethod
    def do_cli(region, namespace, name, dir, forced):
        eventdatalist = []
        if not os.path.exists(dir):
            raise EventFileNotFoundException("Event Dir Not Exists")

        elif os.path.isfile(dir):
            if not dir.endswith('.json'):
                raise EventFileNameFormatException('Please check your json file name endwith `.json`.')
            eventdata = Update.get_event_from_file(dir)
            if eventdata:
                eventdatalist.append(eventdata)

        elif os.path.isdir(dir):
            for path in os.listdir(dir):
                filepath = os.path.join(dir, path)
                if os.path.isfile(filepath) and filepath.endswith('.json'):
                    eventdata = Update.get_event_from_file(filepath)
                    if eventdata:
                        eventdatalist.append(eventdata)

        if len(eventdatalist):
            Update.update_event_data(region=region, namespace=namespace, name=name,
                                     eventdatalist=eventdatalist, forced=forced)
        else:
            Operation("Eventdata file not found").exception()


@click.command(name='update', short_help=help.UPDATE_SHORT_HELP)
@click.option('-r', '--region', help=help.REGION)
@click.option('-ns', '--namespace', default="default", help=help.NAMESPACE)
@click.option('-n', '--name', required=True, help=help.FUNCTION_NAME_HELP)
@click.option('-d', '--dir', type=str, default='.', help=help.DIR)
@click.option('-f', '--forced', is_flag=True, default=False, help=help.FORCED_UPDATE)
@click.option('--no-color', '-nc', is_flag=True, default=False, help=help.NOCOLOR)
def update(region, namespace, name, dir, forced, no_color):
    """
        \b
        Update Events to Function1.
        \b
        Common usage:
        \b
            * Update Events to Function1
              $ scf eventdata update --name Function1
    """

    Update.do_cli(region, namespace, name, dir, forced)
