# -*- coding: utf-8 -*-

import json
import sys
import os
import click
import subprocess
from tcfcli.common import tcsam
from tcfcli.common.tcsam.tcsam_macro import TcSamMacro as tsmacro
from tcfcli.common.user_exceptions import InvokeContextException, UserException
from tcfcli.cmds.native.common.runtime import Runtime
from tcfcli.cmds.native.common.debug_context import DebugContext
from tcfcli.common.template import Template
from tcfcli.common.file_util import FileUtil
import tcfcli.common.base_infor as infor
from tcfcli.common.operation_msg import Operation


class StartApiContext(object):
    _thread_err_msg = ""

    def __init__(self,
                 template_file,
                 function=None,
                 debug_port=None,
                 debug_args="",
                 namespace=None,
                 env_file=None,
                 ):

        self._template_file = template_file
        self._function = function
        self._debug_port = debug_port
        self._debug_argv = debug_args
        self._namespace = namespace
        self._runtime = None
        self._env_file = env_file

        self._thread_err_msg = ""

    def _get_namespace(self, resource):
        ns = None
        if self._namespace:
            ns = resource.get(self._namespace, None)
        else:
            nss = list(resource.keys())
            if len(nss) == 1:
                self._namespace = nss[0]
                ns = resource.get(nss[0], None)
        if not ns:
            raise InvokeContextException("You must provide a valid namespace")

        del ns[tsmacro.Type]
        return ns

    def _get_function(self, namespace):
        fun = None
        if self._function:
            fun = namespace.get(self._function, None)
        else:
            funs = list(namespace.keys())
            if len(funs) == 1:
                self._function = funs[0]
                fun = namespace.get(funs[0], None)
        if not fun:
            raise InvokeContextException("You must provide a valid function")

        del fun[tsmacro.Type]
        return fun

    def _check_function_type(self, resource):
        ns = list(resource.keys())[0]
        func = list(resource[ns].keys())[0]
        if tsmacro.Type not in resource[ns][func][tsmacro.Properties]:
            raise InvokeContextException("You must provide Properties Type in yaml file")
        if resource[ns][func][tsmacro.Properties][tsmacro.Type] != 'HTTP':
            raise InvokeContextException("You must provide a HTTP Type Service")
        runtime = resource[ns][func][tsmacro.Properties][tsmacro.Runtime]
        if (runtime[0:].lower()) not in infor.SERVICE_RUNTIME:
            raise InvokeContextException("You must provide a support Runtime,from one of {s_r}".format(s_r=infor.SERVICE_RUNTIME))

    def __enter__(self):
        template_dict = tcsam.tcsam_validate(Template.get_template_data(self._template_file))

        resource = template_dict.get(tsmacro.Resources, {})
        self.resource = resource
        func = self._get_function(self._get_namespace(resource))

        self._check_function_type(resource)

        self._runtime = Runtime(func.get(tsmacro.Properties, {}))
        self._debug_context = DebugContext(self._debug_port, self._debug_argv, self._runtime.runtime)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def start(self):
        try:
            child = subprocess.Popen(args=[self.cmd]+self.argv, env=self.env)
        except OSError:
            Operation("Execution Failed.", fg="red").echo()
            raise UserException("Execution failed,confirm whether the program({}) is installed".format(self._runtime.cmd))

        ret_code = 0
        try:
            ret_code = child.wait()
        except KeyboardInterrupt:
            child.kill()
            Operation("Recv a SIGINT, exit.").echo()

        if ret_code == 233:  # runtime not match
            raise UserException("Execution failed,confirm whether the program({}) is installed".format(self._runtime.runtime))

    @property
    def cmd(self):
        return self._runtime.cmd

    @property
    def argv(self):
        argv = self._debug_context.argv
        code = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(self._template_file)), self._runtime.codeuri))
        return argv+[os.path.join(code, self.get_handler())]

    @property
    def env(self):
        env = {
            'SCF_LOCAL': 'true',
            'SCF_FUNCTION_ENVIRON': json.dumps(self._runtime.env)
        }

        for k, v in self._runtime.env.items():
            env[k] = v

        for k, v in os.environ.items():
            env[k] = v

        env.update(FileUtil.load_json_from_file(self._env_file))

        # convert unicode characters to utf-8 if py2
        if not (sys.version_info > (3, 0)):
            clean_env = {}
            for k in env:
                key = k
                if isinstance(key, unicode):
                    key = key.encode('utf-8')
                if isinstance(env[k], unicode):
                    env[k] = env[k].encode('utf-8')
                clean_env[key] = env[k]
            return clean_env
        return env

    def get_handler(self):
        return self._runtime.handler
