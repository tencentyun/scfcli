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


class Get(object):
    @staticmethod
    def do_cli(region, namespace, name, event, output_dir):
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

        testmodelvaluelist = {}
        if event:
            testmodelvalue = ScfClient(region).get_func_testmodel(functionName=name, namespace=namespace, testModelName=event)
            if not testmodelvalue:
                raise NamespaceException("This function {f} not exist event {e} ".format(f=name, e=event))
            testmodelvaluelist[event] = testmodelvalue
        else:
            for testmodel in ScfClient(region).list_func_testmodel(functionName=name, namespace=namespace):
                testmodelvalue = ScfClient(region).get_func_testmodel(functionName=name, namespace=namespace,
                                                                      testModelName=testmodel)
                testmodelvaluelist[testmodel] = testmodelvalue

        for testmodel in testmodelvaluelist:
            testmodelfilename = testmodel+'.json'
            testmodelfilepath = os.path.join(output_dir, testmodelfilename)
             #(testmodelvaluelist[testmodel]['TestModelValue'])
            with open(testmodelfilepath, 'w') as f:
                f.write(testmodelvaluelist[testmodel]['TestModelValue'])
                Operation('Downloading event-data: {%s} ...' % (testmodel)).process()
            #     json.dump(testmodelvaluelist[testmodel], f)


@click.command(name='get', short_help=help.GET_SHORT_HELP)
@click.option('-r', '--region', help=help.REGION)
@click.option('-ns', '--namespace', default="default", help=help.NAMESPACE)
@click.option('-n', '--name', required=True, help=help.FUNCTION_NAME_HELP)
@click.option('-e', '--event', help=help.FUNCTION_TESTMODEL_NAME_HELP)
@click.option('-d', '--output-dir', default='.', help=help.FUNCTION_TESTMODEL_NAME_HELP)
def get(region, namespace, name, event, output_dir):
    '''
    \b
    Get a SCF function event.
    \b
    Common usage:
        \b
        * Get a function event
          $ scf event get --name test  --event event
    '''
    Get.do_cli(region, namespace, name, event, output_dir)


