# -*- coding: utf-8 -*-

from tcfcli.common import statistics, daily_task
from tcfcli.common.operation_msg import Operation
from tcfcli.common.daily_task import get_version
from tcfcli.cmds.cli import __version__, __internal_version__

import sys

statistics.StatisticsConfigure().get_args(sys.argv)

if "-v" in sys.argv or "--version" in sys.argv:
    Operation("Version: %s" % (__version__)).success()
    try:
        version_information = get_version()
        Operation("Latest Version: %s" % version_information["version"]).information()
        if version_information["message"]:
            for eve_msg in version_information["message"]:
                Operation(eve_msg).information()
        Operation("If you want to upgrade: pip install -U scf").information()
    except:
        pass
    if "-test" in sys.argv:
        Operation("Test Version: %s" % (__internal_version__), tofile=False).success()
    sys.exit(0)
else:
    daily_task.daily_task()



