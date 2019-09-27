# -*- coding: utf-8 -*-

import io
import json
import traceback
from tcfcli.common.operation_msg import Operation
from tcfcli.common.user_exceptions import InvalidEnvVarsException


class FileUtil(object):

    @staticmethod
    def load_json_from_file(p):
        if p is None:
            return {}
        try:
            with io.open(p, mode='r', encoding='utf-8') as fp:
                return json.load(fp)
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            raise InvalidEnvVarsException('read environment from file {} failed: {}'.format(p, str(e)))