import click
import json
import time
import signal
from tcfcli.cmds.cli import __version__
from tcfcli.common.user_exceptions import InvalidEnvParameters
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.scf.v20180416 import scf_client, models

from . import ScfBaseClient


class ScfReportClient(ScfBaseClient):

    CLOUD_API_REQ_TIMEOUT = 3
    def __init__(self):
        super(ScfReportClient, self).__init__("ap-guangzhou")    


    def report(self):
        try:
            params = {'Downloads': 1, 'Source': 'cli', 'SourceVersion': __version__}
            click.secho(self._client.call("ReportCliInfos", params))
        except Exception as err:
            pass
