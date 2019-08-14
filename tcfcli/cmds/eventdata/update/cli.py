# -*- coding: utf-8 -*-

import click
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
        if not path.endswith('.json'):
            Operation(' Please check your json file name must endwith `.json`.')
            return None
        try:
            with click.open_file(path, 'r', encoding="utf-8") as f:
                event = f.read()
                json.loads(event)
        except Exception as e:
            Operation(str(e) + ' Please check your json file format.')
            return None

        filefullname = os.path.split(path)[1]
        filename = os.path.splitext(filefullname)[0]
        return {filename: event}

    @staticmethod
    def do_cli(region, namespace, name, dir):
        eventdatalist = []
        if not os.path.exists(dir):
            raise EventFileNotFoundException("Event Dir Not Exists")
        elif os.path.isfile(dir):
            eventdata = Update.get_event_from_file(dir)
            if not eventdata:
                Operation("The file must be a json file,your file is %s." % dir).warning()
                return
            eventdatalist.append(eventdata)

        elif os.path.isdir(dir):
            for path in os.listdir(dir):
                if os.path.isdir(path):
                    continue
                elif os.path.isfile(path):
                    eventdata = Update.get_event_from_file(path)
                    if not eventdata:
                        continue
                    eventdatalist.append(eventdata)
        Update.update_event_data(region=region, namespace=namespace, name=name,
                                 eventdatalist=eventdatalist)

    @staticmethod
    def update_event_data(region, namespace, name, eventdatalist):
        if region and region not in REGIONS:
            raise ArgsException("region {r} not exists ,please select from{R}".format(r=region, R=REGIONS))
        if not region:
            region = UserConfig().region

        rep = ScfClient(region).get_ns(namespace)
        if not rep:
            raise NamespaceException("Region {r} not exist namespace {n}".format(r=region, n=namespace))

        functions = ScfClient(region).get_function(function_name=name, namespace=namespace)
        if not functions:
            raise FunctionNotFound("Region {r} namespace {n} not exist function {f}".format(r=region, n=namespace, f=name))
            return

        Operation("Region:%s" % (region)).process()
        Operation("Namespace:%s " % (namespace)).process()
        Operation("Function:%s " % (name)).process()
        print (eventdatalist)
        for eventdata in eventdatalist:
            #eventdata = json.dumps(eventdata)
            Update.do_deploy_testmodel(functionName=name, event=list(eventdata.values())[0],
            event_name=list(eventdata.keys())[0], namespace=namespace, region=region)

    @staticmethod
    def do_deploy_testmodel(functionName, event, event_name, namespace, region):
            # 获取失败会直接创建新模版
            # 获取成功代表已有模版，直接覆盖
        try:
            ScfClient(region).get_func_testmodel(functionName=functionName, testModelName=event_name,
                                                    namespace=namespace)
        except:
            ScfClient(region).create_func_testmodel(functionName=functionName, testModelValue=event,
                                                    testModelName=event_name, namespace=namespace)
            Operation("Updateing event {%s}..." % event_name).process()
            return
        Operation("This event {%s} exist in remote，Covering event..." % event_name).process()
        # v = click.prompt(text="Do you want to cover remote event? (y/n)",
        #                  default="n", show_default=False)
        # if v and v in ['y', 'Y']:

        ScfClient(region).update_func_testmodel(functionName=functionName, testModelValue=event,
                                                testModelName=event_name, namespace=namespace)


@click.command(name='update', short_help=help.LIST_SHORT_HELP)
@click.option('--region', '-r', help=help.REGION)
@click.option('-ns', '--namespace', default="default", help=help.NAMESPACE)
@click.option('-n', '--name', required=True, help=help.FUNCTION_NAME_HELP)
@click.option('--dir', '-d', type=str, default='.', help=help.DIR)
def update(region, namespace, name, dir):
    """
        \b
        Update Events to Function1.
        \b
        Common usage:
        \b
            * Update Events to Function1
              $ scf eventdata update --name Function1
    """
    Update.do_cli(region, namespace, name, dir)
