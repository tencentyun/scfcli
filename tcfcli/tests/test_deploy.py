import unittest
import os
import shutil

from test_common import *
from click.testing import CliRunner
from tcfcli.cmds.configure import cli as configure_cli
from tcfcli.cmds.init import cli as init_cli
from tcfcli.cmds.deploy import cli as deploy_cli


class TestDeploy(unittest.TestCase):
    def setUp(self):
        super(TestDeploy, self).setUp()
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
        super(TestDeploy, self).tearDown()

    def test_deploy_python27(self):
        name = "hello_world_python27"
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'python2.7', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(deploy_cli.deploy, ["-t", "./%s/template.yaml" % name, "-f"])
        self.assertIn('Deploy function \'%s\' success' % name, result.output)
        self.assertEqual(0, result.exit_code)
        if os.path.exists(path):
            shutil.rmtree(path)

    def test_deploy_python36(self):
        name = "hello_world_python36"
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'python3.6', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(deploy_cli.deploy, ["-t", "./%s/template.yaml" % name, "-f"])
        self.assertIn('Deploy function \'%s\' success' % name, result.output)
        self.assertEqual(0, result.exit_code)
        if os.path.exists(path):
            shutil.rmtree(path)

    def test_deploy_nodejs610(self):
        name = "hello_world_nodejs610"
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'nodejs6.10', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(deploy_cli.deploy, ["-t", "./%s/template.yaml" % name, "-f"])
        self.assertIn('Deploy function \'%s\' success' % name, result.output)
        self.assertEqual(0, result.exit_code)
        if os.path.exists(path):
            shutil.rmtree(path)

    def test_deploy_nodejs89(self):
        name = "hello_world_nodejs89"
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'nodejs8.9', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(deploy_cli.deploy, ["-t", "./%s/template.yaml" % name, "-f"])
        self.assertIn('Deploy function \'%s\' success' % name, result.output)
        self.assertEqual(0, result.exit_code)
        if os.path.exists(path):
            shutil.rmtree(path)

    def test_deploy_python27_namespace(self):
        name = "hello_world_python27_ns"
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'python2.7', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(deploy_cli.deploy, ["-t", "./%s/template.yaml" % name, "-f"])
        self.assertIn('Deploy function \'%s\' success' % name, result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(deploy_cli.deploy, ["-t", "./%s/template.yaml" % name, "-f", "-ns", "default111"])
        self.assertIn('Deploy function \'%s\' success' % name, result.output)
        self.assertEqual(0, result.exit_code)

        if os.path.exists(path):
            shutil.rmtree(path)

    def test_deploy_python27_cos(self):
        name = "hello_world_python27_cos"
        path = "./" + name
        cos_bucket = "scf-function-test-hk"
        new_namespace = "default111"
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'python2.7', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(deploy_cli.deploy, ["-t", "./%s/template.yaml" % name, "-f", "-ns", new_namespace, "-c",
                                                   cos_bucket])
        self.assertIn('Deploy function \'%s\' success' % name, result.output)
        self.assertIn('to COS bucket \'%s\' success' % cos_bucket, result.output)
        self.assertEqual(0, result.exit_code)

        if os.path.exists(path):
            shutil.rmtree(path)

    def test_deploy_python27_region(self):
        name = "hello_world_python27_region"
        path = "./" + name
        if os.path.exists(path):
            shutil.rmtree(path)

        runner = CliRunner()
        result = runner.invoke(init_cli.init, ['-N', '-r', 'python2.7', '-n', name, '-ns', 'default'])
        self.assertIn('[*] Project initialization is complete\n', result.output)
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(deploy_cli.deploy, ["-t", "./%s/template.yaml" % name, "-f", "-r", "ap-chengdu"])
        self.assertIn('Deploy function \'%s\' success' % name, result.output)
        self.assertEqual(0, result.exit_code)

        if os.path.exists(path):
            shutil.rmtree(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
