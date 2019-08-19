# -*- coding: utf-8 -*-

from tcfcli.common import statistics, daily_task
import sys


statistics.StatisticsConfigure().get_args(sys.argv)
daily_task.daily_task()

