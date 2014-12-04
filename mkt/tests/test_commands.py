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


class TestProjectAndContainer(TestCase):

    def test_no_dockerfile(self):
        with mock.patch('os.listdir') as listdir:
            listdir.return_value = []
            with self.assertRaises(ValueError):
                cmds.get_project(None)

    def test_no_project(self):
        with mock.patch('os.listdir') as listdir:
            assert not listdir.called
            with self.assertRaises(ValueError):
                cmds.get_project('wat')

    def test_project(self):
        with mock.patch('os.listdir') as listdir:
            with mock.patch('os.path.basename') as basename:
                basename.return_value = 'solitude'
                listdir.return_value = ['Dockerfile']
                assert cmds.get_project(None) == 'solitude'


class TestCommands(TestCase):

    def setUp(self):
        self.parser = cmds.create_parser()
        self.args = mock.Mock()

        self.locations = mock.Mock()
        self.locations.return_value = {
            'tree': tempfile.mkdtemp(),
            'image': '/dir/images',
            'fig.dist': os.path.join(cmds.ROOT, 'data', 'fig.yml.dist'),
            'fig': tempfile.mkstemp()[1]
        }
        cmds.locations = self.locations
        cmds.CONFIG_PATH = tempfile.mkstemp()[1]
        cmds.FIG_PATH = tempfile.mkstemp()[1]
        cmds.BRANCHES = ['solitude']
        cmds.MIGRATIONS = ['solitude']

    def test_get_image(self):
        self.args.name = 'whatever'
        with self.assertRaises(SystemExit):
            cmds.get_image(self.args, self.parser)

    def test_checkout_no_root(self):
        self.locations.return_value['tree'] = None
        cmds.locations = self.locations

        args = self.parser.parse_args(['checkout'])
        with self.assertRaises(SystemExit):
            cmds.checkout(args, self.parser, 'gh-user')

    @mock.patch('mkt.cmds.BRANCHES', ['foo'])
    def test_checkout_command(self):
        """Test checkout cmd sees correct args."""
        args = self.parser.parse_args(['checkout'])
        directory = self.locations()['tree']
        with mock.patch('mkt.cmds.subprocess') as subprocess:

            cmds.checkout(args, self.parser, 'gh-user')

            self.assertEqual(subprocess.call.call_args_list, [
                mock.call([
                    'git', 'clone', '-o', 'upstream',
                    'git@github.com:mozilla/foo.git',
                    '{0}/foo'.format(directory)
                ]),
                mock.call([
                    'git', 'remote', 'add', 'origin',
                    'git@github.com:gh-user/foo.git'
                ], cwd='{0}/foo'.format(directory)),
                mock.call([
                    'git', 'config',
                    'branch.master.remote', 'origin'
                ])
            ])

    @mock.patch('mkt.cmds.BRANCHES', ['foo'])
    def test_checkout_command_inverted_origin_upstream(self):
        """Test checkout cmd sees correct args when origin is inverted."""
        args = self.parser.parse_args([
            'checkout',
            '--moz_remote_name', 'origin',
            '--fork_remote_name', 'upstream'
        ])
        directory = self.locations()['tree']

        with mock.patch('mkt.cmds.subprocess') as subprocess:

            cmds.checkout(args, self.parser, 'gh-user')

            self.assertEqual(subprocess.call.call_args_list, [
                mock.call([
                    'git', 'clone', '-o', 'origin',
                    'git@github.com:mozilla/foo.git',
                    '{0}/foo'.format(directory)
                ]),
                mock.call([
                    'git', 'remote', 'add', 'upstream',
                    'git@github.com:gh-user/foo.git'
                ], cwd='{0}/foo'.format(directory)),
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

    def test_root(self):
        directory = self.locations()['tree']
        args = self.parser.parse_args(['root', directory])
        cmds.root(args, self.parser)
        data = open(self.locations()['fig'], 'r').read()
        # Just a rough assertion that the build variable got changed.
        assert '{0}/webpay'.format(directory) in data
        # ANother rough check that volumes got set correctly.
        assert '/dir/images/elasticsearch'.format(directory) in data

    def test_root_no_args(self):
        args = self.parser.parse_args(['root'])
        with mock.patch('mkt.cmds.set_config_value') as scv:
            assert not scv.called

    def test_update(self):
        args = self.parser.parse_args(['update'])
        os.mkdir(os.path.join(self.locations()['tree'], 'solitude'))

        with mock.patch('mkt.cmds.subprocess') as subprocess:
            with mock.patch('mkt.cmds.fig_command') as fig:
                cmds.update(args, self.parser)
                subprocess.check_output.assert_called_with(
                    ['git', 'pull', '-q'])
                fig.assert_called_with(
                    'run', '--rm', 'solitude', 'schematic', 'migrations')

    def test_update_git_only(self):
        args = self.parser.parse_args(['update', '--git'])
        os.mkdir(os.path.join(self.locations()['tree'], 'solitude'))
        with mock.patch('mkt.cmds.subprocess') as subprocess:
            with mock.patch('mkt.cmds.fig_command') as fig:
                cmds.update(args, self.parser)
                assert subprocess.check_output.called
                assert not fig.called

    def test_update_no_dir(self):
        args = self.parser.parse_args(['update'])
        with self.assertRaises(OSError):
            cmds.update(args, self.parser)
