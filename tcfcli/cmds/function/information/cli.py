# -*- coding: utf-8 -*-

import json
from tcfcli.common.operation_msg import Operation
from tcfcli.libs.utils.scf_client import ScfClient
from tcfcli.common.user_exceptions import *
from tcfcli.help.message import FunctionHelp as help
from tcfcli.common.user_config import UserConfig

@click.command(name='info', short_help=help.INFO_SHORT_HELP)
@click.option('-r', '--region', help=help.REGION)
@click.option('-ns', '--namespace', default="default", help=help.NAMESPACE)
@click.option('-n', '--name',  help=help.INFO_NAME)
@click.option('--no-color', '-nc', is_flag=True, default=False, help=help.NOCOLOR)
def info(region, namespace, name, no_color):
    """
        \b
        Show the function information.
        \b
        Common usage:
        \b
            * Get the function information
              $ scf function infor --region ap-guangzhou --namespace default --name hello_world
    """
    Information(region=region, namespace=namespace, name=name).get_information()

class Information(object):
    def __init__(self, region, namespace, name):
        self.user_config = UserConfig()
        self.region = region if region else self.user_config.region
        self.namespace = namespace
        self.name = name

    def recursion_dict(self, information, num):
        for eveKey, eveValue in information.items():
            try:
                eveValue = json.loads(eveValue)
            except:
                pass
            finally:
                if isinstance(eveValue, dict):
                    Operation(" " * num + "%s:" % (str(eveKey))).out_infor()
                    self.recursion_dict(eveValue, num + 2)
                else:
                    Operation(" " * num + "%s: %s" % (str(eveKey), str(eveValue))).out_infor()

    def format_information(self, result):
        if result:
            information = json.loads(result)
            Operation("[+] %s - %s - %s:" % (self.region, information["Namespace"], self.name), fg="cyan").echo()
            Operation("Name: %s" % self.name).out_infor()
            Operation("Version: %s" % information["FunctionVersion"]).out_infor()
            Operation("Status: %s" % information["Status"]).out_infor()
            Operation("FunctionId: %s" % information["FunctionId"]).out_infor()
            Operation("Region: %s" % self.region).out_infor()
            Operation("Namespace: %s" % information["Namespace"]).out_infor()
            Operation("Runtime: %s" % information["Runtime"]).out_infor()

            release_serviceid_list = []
            if information["Triggers"]:
                Operation("     Trigger Information: ", fg="cyan").echo()
                for eve_trigger in information["Triggers"]:
                    trigger_type = eve_trigger['Type']

                    # release apigateway service_id list
                    try:
                        if trigger_type == 'apigw':
                            release_serviceid_list.append(
                                json.loads(eve_trigger['TriggerDesc'])["service"]["serviceId"])
                    except Exception as e:
                        pass

                    msg = u"      > %s - %s:" % (text(trigger_type).upper(), text(eve_trigger["TriggerName"]))
                    Operation(msg, fg="cyan").echo()
                    self.recursion_dict(eve_trigger, 6)


    def information_client(self, namespace, name):
        scf_client = ScfClient(region=self.region)
        result = scf_client.get_function(namespace=namespace, function_name=name)
        return result

    def get_information(self):

        if self.name:
            try:
                function_info = self.information_client(self.namespace, self.name)
                if function_info:
                    self.format_information(function_info)
                else:
                    Operation("Data not available, please check Region/Namespace/FunctionName.").exception()
            except:
                Operation("Could not find function resource: %s - %s - %s" % (
                self.region, self.namespace, self.name)).warning()
                Operation("You can view the list of functions by: scf function list,  and select the correct function resource for information query").warning()
                raise Information("No Function Resource Exception")
        else:
            Operation("Function Name to be queried must be specified").warning()
            Operation("You can view the list of functions by: scf function list,  and select the correct function resource for information query").warning()
            raise InformationException("No Function Resource Exception")