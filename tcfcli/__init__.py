# -*- coding: utf-8 -*-

import platform
version = platform.python_version()
if version < '3':
    import sys

    reload(sys)
    sys.setdefaultencoding("utf-8")
