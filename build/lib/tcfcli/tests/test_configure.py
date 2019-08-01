import unittest

from test_common import *
from click.testing import CliRunner
from tcfcli.cmds.configure import cli as configure_cli


class TestConfigure(unittest.TestCase):

    def setUp(self):
        super(TestConfigure, self).setUp()

    def tearDown(self):
        super(TestConfigure, self).tearDown()

    def test_configure_set_appid(self):
        runner = CliRunner()
        result = runner.invoke(configure_cli.set, ['--appid', AppID])
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(configure_cli.get, ['--appid'])
        self.assertEqual('API config:\nappid = %s\n' % AppID, result.output)
        self.assertEqual(0, result.exit_code)

    def test_configure_set_region(self):
        runner = CliRunner()
        result = runner.invoke(configure_cli.set, ['--region', Region])
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(configure_cli.get, ['--region'])
        self.assertEqual('API config:\nregion = %s\n' % Region, result.output)
        self.assertEqual(0, result.exit_code)

    def test_configure_set_secret_id(self):
        runner = CliRunner()
        result = runner.invoke(configure_cli.set, ['--secret-id', SecretId])
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(configure_cli.get, ['--secret-id'])
        self.assertIn('API config:\nsecret-id', result.output)
        self.assertEqual(0, result.exit_code)

    def test_configure_set_secret_key(self):
        runner = CliRunner()
        result = runner.invoke(configure_cli.set, ['--secret-key', SecretKey])
        self.assertEqual(0, result.exit_code)

        result = runner.invoke(configure_cli.get, ['--secret-key'])
        self.assertIn('API config:\nsecret-key', result.output)
        self.assertEqual(0, result.exit_code)


if __name__ == "__main__":
    unittest.main(verbosity=2)
