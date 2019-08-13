# -*- coding: utf-8 -*-

from tcfcli.cmds.cli import __version__

from . import ScfBaseClient


class ScfReportClient(ScfBaseClient):
    CLOUD_API_REQ_TIMEOUT = 3

    def __init__(self):
        super(ScfReportClient, self).__init__("ap-guangzhou")    

    def report(self):
        try:
            params = {'Downloads': 1, 'Source': 'cli', 'SourceVersion': __version__}
            self._client.call("ReportCliInfos", params)
        except Exception as err:
            pass
