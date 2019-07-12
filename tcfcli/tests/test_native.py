import unittest
import os
import shutil

from datetime import datetime
from test_common import *
from click.testing import CliRunner
from tcfcli.cmds.configure import cli as configure_cli
from tcfcli.cmds.init import cli as init_cli
from tcfcli.cmds.native import cli as native_cli

class TestNative(unittest.TestCase):
    def setUp(self):
        super(TestNative, self).setUp()
        runner = CliRunner()
        result = runner.invoke(configure_cli.set, ['--appid', AppID])
        self.assertEqual(0, result.exit_code)
        result = runner.invoke(configure_cli.set, ['--region', Region])
        self.assertEqual(0, result.exit_code)
        result = runner.invoke(configure_cli.set, ['--secret-id', SecretId])
        self.assertEqual(0, result.exit_code)
        result = runner.invoke(configure_cli.set, ['--secret-key', SecretKey])
        self.assertEqual(0, result.exit_code)

    def tearDown(self):
        super(TestNative, self).tearDown()

    def test_native_python27(self):
        name = "landun-devops-python27-" + get_datetime()
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'python2.7', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(native_cli.invoke, ["-t", "./%s/template.yaml" % name, "--no-event"])
        self.assertEqual(0, result.exit_code)

        if os.path.exists(path):
            shutil.rmtree(path)

    def test_native_python27_quiet(self):
        name = "landun-devops-python27-" + get_datetime()
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'python2.7', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        # test option: -q, --quiet 
        result = runner.invoke(native_cli.invoke, ["-t", "./%s/template.yaml" % name, "--no-event", "-q"])
        self.assertEqual(0, result.exit_code)

        if os.path.exists(path):
            shutil.rmtree(path)

    def test_native_python36(self):
        name = "landun-devops-python36-" + get_datetime()
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'python3.6', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(native_cli.invoke, ["-t", "./%s/template.yaml" % name, "--no-event"])
        self.assertEqual(0, result.exit_code)

        if os.path.exists(path):
            shutil.rmtree(path)

    def test_deploy_python36_quiet(self):
        name = "landun-devops-python36-" + get_datetime()
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'python3.6', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        # test option: -q, --quiet 
        result = runner.invoke(native_cli.invoke, ["-t", "./%s/template.yaml" % name, "--no-event", "-q"])
        self.assertEqual(0, result.exit_code)

        if os.path.exists(path):
            shutil.rmtree(path)


    def test_deploy_nodejs610(self):
        name = "landun-devops-nodejs610-" + get_datetime()
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'nodejs6.10', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(native_cli.invoke, ["-t", "./%s/template.yaml" % name, "--no-event"])
        self.assertEqual(0, result.exit_code)

        if os.path.exists(path):
            shutil.rmtree(path)

    def test_deploy_nodejs610_quiet(self):
        name = "landun-devops-nodejs610-" + get_datetime()
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'nodejs6.10', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(native_cli.invoke, ["-t", "./%s/template.yaml" % name, "--no-event", "-q"])
        self.assertEqual(0, result.exit_code)

        if os.path.exists(path):
            shutil.rmtree(path)

    
    def test_deploy_nodejs89(self):
        name = "landun-devops-nodejs89-" + get_datetime()
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'nodejs8.9', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(native_cli.invoke, ["-t", "./%s/template.yaml" % name, "--no-event"])
        self.assertEqual(0, result.exit_code)

        if os.path.exists(path):
            shutil.rmtree(path)

    def test_deploy_nodejs89_quiet(self):
        name = "landun-devops-nodejs89-" + get_datetime()
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'nodejs8.9', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(native_cli.invoke, ["-t", "./%s/template.yaml" % name, "--no-event", "-q"])
        self.assertEqual(0, result.exit_code)

        if os.path.exists(path):
            shutil.rmtree(path)

def get_datetime():
    now = datetime.now() # current date and time
    date_time = now.strftime("%m%d%Y%H%M%S")
    return date_time

if __name__ == "__main__":
    unittest.main(verbosity=2)
