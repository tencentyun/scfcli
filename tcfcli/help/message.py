# -*- coding: utf-8 -*-

'''
    Powered by Dfounderliu
    Email: dfounderliu@tencent.com
    Date: 2019 / 7 / 27
    Help Message

'''

import click
import tcfcli.common.base_infor as infor
from tcfcli.common.operation_msg import Operation

REGIONS = infor.SHOW_REGIONS
REGIONS_STR = Operation("%s" % (", ".join(REGIONS)), fg='green').style()

RUNTIME = infor.EVENT_RUNTIME
RUNTIME_STR = Operation("%s" % (", ".join(RUNTIME)), fg='green').style()

HTTP_RUNTIME = infor.HTTP_RUNTIME
HTTP_RUNTIME_STR = Operation("%s" % (", ".join(HTTP_RUNTIME)), fg='green').style()


class CommonHelp():
    # Common Help Message

    NAME = "Function name."
    NAMESPACE = "Namespace name."
    HELP_MESSAGE = "Show the help and exit."

    EVENTS_CMQ = "CMQ event."
    EVENTS_CMQ_NOTIFICATION = "Generates an CMQ Topic notification event."

    EVENTS_CKAFKA = "Ckafka event."
    EVENTS_CKAFKA_CONSUME = "Generates an ckafka consuming event."

    EVENTS_APIGATEWAY = "API Gateway event."
    EVENTS_APIGATEWAY_PROXY = "Generates an API Gateway proxy event."

    EVENTS_TIMER = "Timer event."
    EVENTS_TIMER_TIMEUP = "Generates an Timer event."

    EVENTS_COS = "COS Event."
    EVENTS_COS_PUT = "Generates an COS Put event."
    EVENTS_COS_POST = "Generates an COS Post event."
    EVENTS_COS_DELETE = "Generates an COS Delete event."

    INVOKE_ENV_VARS = 'JSON file contains function environment variables.'
    INVOKE_DEBUG_PORT = 'The port exposed for debugging. If specified, local container will start with debug mode.'
    INVOKE_DEBUGGER_PATH = 'The debugger path in host. If specified, the debugger will mounted into the function container.'
    INVOKE_DEBUG_ARGS = 'Additional args to be passed the debugger.'
    INVOKE_DOCKER_VOLUME_BASEDIR = 'The basedir where SCF template locate in.'
    INVOKE_DOCKER_NETWORK = 'Specifies the name or id of an existing docker network which containers should connect to, along with the default bridge network.'
    INVOKE_LOG_FILE = 'Path of logfile where send runtime logs to file.'
    INVOKE_SKIP_PULL_IMAGE = 'Specify whether CLI skip pulling or update docker images.'
    INVOKE_REGION = "The function region. Including %s." % REGIONS_STR

    NOCOLOR = "Suppress colored output"


class DeployHelp():
    # Deploy Help Message

    SHORT_HELP = "Deploy a SCF function."

    NAME = CommonHelp.NAME
    NAMESPACE = CommonHelp.NAMESPACE
    NOCOLOR = CommonHelp.NOCOLOR

    COS_BUCKET = "COS Bucket name."
    TEMPLATE_FILE = "SCF function template file."
    REGION = "The function will be deployed in this region. Including %s." % REGIONS_STR
    FORCED = "The function will be forced to update when it already exists. The default is False."
    SKIP_EVENT = "Triggers will continue with the previous setup and won't cover them this time."
    WITHOUT_COS = "Deploy SCF function without COS. If you set cos-bucket in configure."
    HISTORY = "The deployment history version code is only valid when using using-cos."
    EVENT = "The function event file name. Please set json file name,such as `event.json`"
    EVENT_NAME = "The function event name. Such as `event`"
    UPDATE_EVENT = "Event that has been modified will be overwritten by the upgrade. This parameter defaults to False."


class InitHelp():
    # Init Help Message

    SHORT_HELP = "Initialize a SCF function with the template."

    NAME = CommonHelp.NAME
    NAMESPACE = CommonHelp.NAMESPACE
    TYPE = "Function Type (Event,HTTP). The default is Event."
    LOCATION = "Template location (git, mercurial, http(s), zip, path)."
    # RUNTIME = "Runtime of this funtion. Event type include %s, HTTP type include %s." % (RUNTIME_STR, HTTP_RUNTIME_STR)
    RUNTIME = "Runtime of this funtion.Include %s." % (RUNTIME_STR)
    OUTPUT_DIR = "The path where will output the initialized app into."
    NO_INPUT = "Disable prompting and accept default values defined template config."

    NOCOLOR = "Suppress colored output"


class ConfigureHelp():
    # Configure Help Message

    SHORT_HELP = "Configure your account parameters."

    SECRET_ID = "TencentCloudAPI  SecretId."
    SECRET_KEY = "TencentCloudAPI  SecretKey."
    REGION = "TencentCloudAPI  Region."
    APPID = "TencentCloudAPI  APPID."
    USING_COS = "Deploy function by COS. The default is False.(y/n)"
    PATHON_PATH = "Cli native invoke first use this path."

    SET_SHORT_HELP = "Set your account parameters."
    SET_SECRET_ID = SECRET_ID
    SET_SECRET_KEY = SECRET_KEY
    SET_REGION = REGION
    SET_APPID = APPID
    SET_USING_COS = USING_COS
    SET_PATHON_PATH = PATHON_PATH

    GET_SHORT_HELP = "Get your account parameters."
    GET_SECRET_ID = SECRET_ID
    GET_SECRET_KEY = SECRET_KEY
    GET_REGION = REGION
    GET_APPID = APPID
    GET_USING_COS = USING_COS
    GET_PATHON_PATH = PATHON_PATH

    ADD_SHORT_HELP = "Add a user"

    CHANGE_SHORT_HELP ="Configure change your user."
    CHANGE_USERID_HELP = 'UserId to change to.'

    NOCOLOR = "Suppress colored output. (y/n)"
    ALLOW_REPORT = "Cli will report some infos about command usage amount.You can turn off at any time. (y/n)"


class NativeHelp():
    # Native Help Message

    SHORT_HELP = "Run your SCF function natively for quick development."

    INVOKE_SHORT_HELP = "Execute the SCF function in a environment natively."
    INVOKE_EVENT = 'The source of the file for the simulated test event, the file content must be in JSON format.'
    INVOKE_NO_ENENT = "Without the source of the file for the simulated test. The default is False."
    INVOKE_ENV_VARS = "The environment variable configuration when the function is running, you need to specify the environment variable configuration file, the content must be in JSON format."
    INVOKE_TEMPLATE = "The path or file name of the configuration file. The default is template.yaml."
    INVKOE_DEBUG_PORT = 'The port exposed when the function is running. After the port is specified, the local runtime will start in debug mode and expose the specified port.'
    INVOKE_DEBUG_ARGS = 'The debugger startup parameters in this machine. After the parameter is specified, the specified parameters will be passed when the debugger starts.'
    START_API_SHORT_HElP = "Execute your scf in a environment natively."
    START_API_DEBUG_PORT = 'The port exposed when the function is running. After the port is specified, the local runtime will start in debug mode and expose the specified port.'
    START_API_DEBUG_ARGS = 'The debugger startup parameters in this machine. After the parameter is specified, the specified parameters will be passed when the debugger starts.'
    INVOKE_QUIET = 'Only display what function return.'

    NOCOLOR = "Suppress colored output"


class ValidateHelp():
    # Validate Help Message

    SHORT_HELP = "Validate a SCF template."

    TEMPLATE_FILE = "The SCF template file for Deploy."

    NOCOLOR = "Suppress colored output"


class LogsHelp():
    # Logs Help Message

    SHORT_HELP = "Fetch logs of SCF function from service."

    NAME = CommonHelp.NAME
    NAMESPACE = CommonHelp.NAMESPACE

    REGION = "Specify the area where the function is located (e.g. ap-guangzhou)."
    COUNT = "The count of logs,the maximum value is 10000 and the minimum value is 1."
    START_TIME = "Get the log after the specified start time."
    END_TIMEE = "Get the log before the specified start time."
    DURATION = "The duration between starttime and current time (unit:second)."
    FAILED = "Get the log of the failed call."
    TAIL = "Get the latest real-time logs."

    NOCOLOR = "Suppress colored output"


class LocalHelp():
    # Local Help Message

    SHORT_HELP = "Run SCF function locally (Docker is required)."

    INVOKE_SHORT_HELP = "Execute SCF function in a docker environment locally."
    INVOKE_EVENT = 'The source of the file for the simulated test event, the file content must be in JSON format.'
    INVOKE_NO_ENENT = "Without the source of the file for the simulated test. The default is False."
    INVOKE_QUIET = 'Only display what function return.'

    NOCOLOR = "Suppress colored output"



class FunctionHelp():
    # Function Help Message

    SHORT_HELP = "Manage SCF remote function resource."
    LIST_SHORT_HELP = "Show the SCF function list."
    DELETE_SHORT_HELP = "Delete a SCF function."
    INFO_SHORT_HELP = "Show the function information."

    DELETE_NAME = CommonHelp.NAME
    NAMESPACE = CommonHelp.NAMESPACE
    INFO_NAME = CommonHelp.NAMESPACE
    FORCED = "Force delete function without ask."
    REGION = "Region name. Including %s." % REGIONS_STR

    NOCOLOR = "Suppress colored output"
    LIMIT = "Number of response records. the value maximum 1000"
    OFFSET = "Skip the number of records"


class EventdataHelp():
    # Function Help Message
    DIR = "The local eventdata dir."
    SHORT_HELP = "Manage SCF remote event resource."
    LIST_SHORT_HELP = "Show the SCF event list."
    GET_SHORT_HELP = "Get SCF event from remote."
    UPDATE_SHORT_HELP = "Update local event to remote."
    FUNCTION_NAME_HELP = 'The SCF remote fucntion name.'
    FUNCTION_TESTMODEL_NAME_HELP = 'The SCF remote fucntion event name.'
    FUNCTION_TESTMODEL_OUTPUTDIR = 'The remote function event get to which dir.'
    FORCED_GET = "The local eventdata will be forced to get when it already exists. The default is False."
    FORCED_UPDATE = "The remote eventdata will be forced to update when it already exists. The default is False."
    NAMESPACE = CommonHelp.NAMESPACE
    REGION = "Region name. Including %s." % REGIONS_STR
    NOCOLOR = "Suppress colored output"


class StatHelp():
    SHORT_HELP = "Show the SCF function monitor info."
    NAME = CommonHelp.NAME
    PERIOD = "Specify monitor period (unit s). the value must is 60s or 300s. default 60s"
    STARTTIME = "Start time format YYYY-MM-DD H:M:S"
    ENDTIME = "End time format YYYY-MM-DD H:M:S"
    REGION = LogsHelp.REGION
    METRIC = "Specify show metric. multiple separated by commas case sensitive\n\tmore goto 'https://cloud.tencent.com/document/api/248/37207#2.2-.E6.8C.87.E6.A0.87.E5.90.8D.E7.A7.B0'"


class RemoteHelp():
    # RemoteHelp Help Message

    SHORT_HELP = "Manage SCF remote function invoke."
    INVOKE_NAME = CommonHelp.NAME
    NAMESPACE = CommonHelp.NAMESPACE
    REGION = "Region name. Including %s." % REGIONS_STR
    EVENTDATA = "Local eventdata file"
    NOCOLOR = "Suppress colored output"
    INVOCATIONTYPE ="The type of invoke remote function.Include %s." % infor.INVOCATION_TYPE