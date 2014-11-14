import os
import tempfile
from unittest import TestCase

import mock

from mkt import cmds


class TestConfig(TestCase):

    def setUp(self):
        self.tmp = tempfile.mkstemp()[1]

    def test_set_and_get(self):
        with mock.patch('mkt.cmds.CONFIG_PATH', self.tmp):
            assert cmds.get_config_value('nope', 'k') is None
            cmds.set_config_value('nope', 'k', 'v')
            assert cmds.get_config_value('nope', 'k') == 'v'
            cmds.set_config_value('nope', 'k', 'p')
            assert cmds.get_config_value('nope', 'k') == 'p'


class TestCommands(TestCase):

    def setUp(self):
        self.parser = cmds.create_parser()
        self.args = mock.Mock()

    def test_get_image(self):
        self.args.name = 'whatever'
        with self.assertRaises(SystemExit):
            cmds.get_image(self.args, self.parser)

    @mock.patch('mkt.cmds.BRANCHES', ['foo'])
    @mock.patch('mkt.cmds.get_dir')
    def test_checkout_command(self, get_dir):
        """Test checkout cmd sees correct args."""
        get_dir.return_value = '/dir/foo'
        args = self.parser.parse_args(['checkout'])
        with mock.patch('mkt.cmds.subprocess') as subprocess:

            cmds.checkout(args, self.parser, 'gh-user')

            self.assertEqual(subprocess.call.call_args_list, [
                mock.call([
                    'git', 'clone', '-o', 'upstream',
                    'git@github.com:mozilla/foo.git',
                    '/dir/foo'
                ]),
                mock.call([
                    'git', 'remote', 'add', 'origin',
                    'git@github.com:gh-user/foo.git'
                ], cwd='/dir/foo'),
                mock.call([
                    'git', 'config',
                    'branch.master.remote', 'origin'
                ])
            ])

    @mock.patch('mkt.cmds.BRANCHES', ['foo'])
    @mock.patch('mkt.cmds.get_dir')
    def test_checkout_command_inverted_origin_upstream(self, get_dir):
        """Test checkout cmd sees correct args when origin is inverted."""
        get_dir.return_value = '/dir/foo'

        args = self.parser.parse_args([
            'checkout',
            '--moz_remote_name', 'origin',
            '--fork_remote_name', 'upstream'
        ])
        with mock.patch('mkt.cmds.subprocess') as subprocess:

            cmds.checkout(args, self.parser, 'gh-user')

            self.assertEqual(subprocess.call.call_args_list, [
                mock.call([
                    'git', 'clone', '-o', 'origin',
                    'git@github.com:mozilla/foo.git',
                    '/dir/foo'
                ]),
                mock.call([
                    'git', 'remote', 'add', 'upstream',
                    'git@github.com:gh-user/foo.git'
                ], cwd='/dir/foo'),
                mock.call([
                    'git', 'config',
                    'branch.master.remote', 'upstream'
                ])
            ])

    def test_bind_ip(self):
        args = self.parser.parse_args(['bind', '--bind_ip', '10.0.0.2'])

        p = mock.patch('mkt.cmds.get_adb_devices')
        p.start().return_value = ['abcde      device']
        self.addCleanup(p.stop)

        def mock_shell(args, **kw):
            if args[0:2] == ['adb', 'pull']:
                if os.path.exists('./hosts'):
                    raise RuntimeError(
                        'Expected to be running in a temp dir!')
                with open('./hosts', 'w') as f:
                    f.write('mock hosts file')

        with mock.patch('mkt.cmds.subprocess') as subprocess:
            subprocess.check_call.side_effect = mock_shell

            cmds.bind(args, self.parser)

            self.assertEqual(subprocess.check_call.call_args_list, [
                mock.call(['adb', 'remount']),
                mock.call(['adb', 'pull', '/system/etc/hosts', './']),
                mock.call(['adb', 'push', './new-hosts', '/system/etc/hosts'])
            ])
