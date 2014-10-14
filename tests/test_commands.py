from unittest import TestCase

import mock

import cmds


class TestCommands(TestCase):

    def setUp(self):
        self.parser = cmds.create_parser()

    @mock.patch('cmds.BRANCHES', ['foo'])
    @mock.patch('cmds.TREES_DIR', '/dir/')
    def test_checkout_command(self):
        """Test checkout cmd sees correct args."""

        args = self.parser.parse_args(['checkout'])
        with mock.patch("cmds.subprocess") as subprocess:

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

    @mock.patch('cmds.BRANCHES', ['foo'])
    @mock.patch('cmds.TREES_DIR', '/dir/')
    def test_checkout_command_inverted_origin_upstream(self):
        """Test checkout cmd sees correct args when origin is inverted."""

        args = self.parser.parse_args([
            'checkout',
            '--moz_remote_name', 'origin',
            '--fork_remote_name', 'upstream'
        ])
        with mock.patch("cmds.subprocess") as subprocess:

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
