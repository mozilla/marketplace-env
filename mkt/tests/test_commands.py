import os
import sha
import tempfile
from decimal import Decimal
from unittest import TestCase

import mock

from mkt import cmds


class TestBase(TestCase):

    def setUp(self):
        test_file = tempfile.mkstemp()[1]
        cmds.MIGRATIONS = ['solitude']
        cmds.REQUIREMENTS = {'solitude': [cmds.req('f', test_file)]}
        open(test_file, 'w').write('this is a test')


class TestConfig(TestBase):

    def setUp(self):
        self.tmp = tempfile.mkstemp()[1]

    def test_set_and_get(self):
        with mock.patch('mkt.cmds.CONFIG_PATH', self.tmp):
            assert cmds.get_config_value('nope', 'k') is None
            cmds.set_config_value('nope', 'k', 'v')
            assert cmds.get_config_value('nope', 'k') == 'v'
            cmds.set_config_value('nope', 'k', 'p')
            assert cmds.get_config_value('nope', 'k') == 'p'


class TestProjectAndContainer(TestBase):

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


class TestVersions(TestBase):

    def test_get_fails(self):
        with mock.patch('subprocess.check_output') as sub:
            with self.assertRaises(ValueError):
                sub.side_effect = OSError
                cmds.get_version('docker')

    def test_get_wrong(self):
        with mock.patch('subprocess.check_output') as sub:
            with self.assertRaises(ValueError):
                sub.return_value = 'wat?'
                cmds.get_version('docker')

    def test_get_ok(self):
        with mock.patch('subprocess.check_output') as sub:
            sub.return_value = 'Client version: 1.3.1b, Server version: 1.3'
            self.assertEquals(
                cmds.get_version('docker'),
                [Decimal('1.3'), Decimal('1.3')]
            )


class TestRequirements(TestBase):

    def test_get_container(self):
        with mock.patch('mkt.cmds.subprocess') as sub:
            sub.check_output.return_value = 'x -'
            with mock.patch('mkt.cmds.get_compose_container') as compose:
                result = cmds.get_container_requirements(
                    'solitude', cmds.REQUIREMENTS['solitude'])
        self.assertEquals(result, 'x')

    def test_get_local(self):
        result = cmds.get_local_requirements(
            'solitude', cmds.REQUIREMENTS['solitude'])
        self.assertEquals(result, sha.new('this is a test').hexdigest())


class TestCommands(TestBase):

    def setUp(self):
        super(TestCommands, self).setUp()
        self.parser = cmds.create_parser()
        self.args = mock.Mock()

        self.locations = mock.Mock()
        self.locations.return_value = {
            'tree': tempfile.mkdtemp(),
            'image': '/dir/images',
            'docker-compose.dist': os.path.join(cmds.ROOT, 'data',
                                                'docker-compose.yml.dist'),
            'docker-compose': tempfile.mkstemp()[1]
        }
        cmds.locations = self.locations
        cmds.CONFIG_PATH = tempfile.mkstemp()[1]
        cmds.COMPOSE_PATH = tempfile.mkstemp()[1]

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
                    'https://github.com/mozilla/foo.git',
                    '{0}/foo'.format(directory)
                ]),
                mock.call([
                    'git', 'remote', 'add', 'origin',
                    'https://github.com/gh-user/foo.git'
                ], cwd='{0}/foo'.format(directory)),
                mock.call([
                    'git', 'config',
                    'branch.master.remote', 'upstream'
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
                    'https://github.com/mozilla/foo.git',
                    '{0}/foo'.format(directory)
                ]),
                mock.call([
                    'git', 'remote', 'add', 'upstream',
                    'https://github.com/gh-user/foo.git'
                ], cwd='{0}/foo'.format(directory)),
                mock.call([
                    'git', 'config',
                    'branch.master.remote', 'origin'
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
        args = self.parser.parse_args(['root', directory, '--buildfrom=local'])
        cmds.root(args, self.parser)
        data = open(self.locations()['docker-compose'], 'r').read()
        # Just a rough assertion that the build variable got changed.
        assert '{0}/webpay'.format(directory) in data
        # Another rough check that volumes got set correctly.
        assert '/dir/images/elasticsearch'.format(directory) in data

    def test_root_no_args(self):
        args = self.parser.parse_args(['root'])
        with mock.patch('mkt.cmds.set_config_value') as scv:
            cmds.root(args, self.parser)
            assert not scv.called

    def test_root_hub(self):
        directory = self.locations()['tree']
        args = self.parser.parse_args(['root', directory, '--buildfrom=hub'])
        cmds.root(args, self.parser)
        data = open(self.locations()['docker-compose'], 'r').read()
        # A rough assertion that the build variable changed.
        assert 'image: mozillamarketplace/elasticsearch' in data

    def test_up_passed(self):
        with mock.patch('mkt.cmds.compose_command') as compose_command:
            cmds.up(None, None, ['--f'])
            compose_command.assert_called_with('up', '--f')

    def test_update(self):
        args = self.parser.parse_args(['update'])
        for branch in cmds.BRANCHES:
            os.mkdir(os.path.join(self.locations()['tree'], branch))

        with mock.patch('mkt.cmds.subprocess') as subprocess:
            with mock.patch('mkt.cmds.compose_command') as compose:
                cmds.update(args, self.parser)
                subprocess.check_output.assert_called_with(
                    ['git', 'pull', '-q'])
                compose.assert_called_with(
                    'run', '--rm', 'solitude', 'schematic', 'migrations')

    def test_update_git_only(self):
        args = self.parser.parse_args(['update', '--git'])
        for branch in cmds.BRANCHES:
            os.mkdir(os.path.join(self.locations()['tree'], branch))

        with mock.patch('mkt.cmds.subprocess') as subprocess:
            with mock.patch('mkt.cmds.compose_command') as compose:
                cmds.update(args, self.parser)
                assert subprocess.check_output.called
                assert not compose.called

    def test_update_no_dir(self):
        args = self.parser.parse_args(['update'])
        with self.assertRaises(OSError):
            cmds.update(args, self.parser)
