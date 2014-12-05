import sys
from unittest import TestCase

from mkt import cmds
from mkt.bin import main


class TestArgs(TestCase):

    def setUp(self):
        self.parser = cmds.create_parser()

    def test_with_empty_args(self):
        """User passes no args, should fail with SystemExit"""
        with self.assertRaises(SystemExit):
            self.parser.parse_args([])

    def test_whoami(self):
        """User passes whoami command"""
        args = self.parser.parse_args(['whoami'])
        self.assertEqual(args.func.func_name, 'whoami')

    def test_whoami_name(self):
        """User passes whoami command"""
        args = self.parser.parse_args(['whoami', 'bungle'])
        self.assertEqual(args.github_username, 'bungle')

    def test_checkout(self):
        """User passes checkout command"""
        args = self.parser.parse_args(['checkout'])
        self.assertEqual(args.func.func_name, 'checkout')

    def test_checkout_defaults(self):
        """Check checkout defaults"""
        args = self.parser.parse_args(['checkout'])
        self.assertEqual(args.moz_remote_name, 'upstream')
        self.assertEqual(args.fork_remote_name, 'origin')

    def test_checkout_moz_remote(self):
        """User sets moz_remote"""
        args = self.parser.parse_args([
            'checkout',
            '--moz_remote_name',
            'foo'
        ])
        self.assertEqual(args.moz_remote_name, 'foo')

    def test_checkout_fork_remote(self):
        """User passes fork remote"""
        args = self.parser.parse_args([
            'checkout',
            '--fork_remote_name',
            'bar'
        ])
        self.assertEqual(args.fork_remote_name, 'bar')


class TestKnown(TestCase):

    def test_up(self):
        sys.argv = '- up foo bar bingo'.split(' ')
        self.assertEquals(main()[0].func, cmds.up)

    def test_check(self):
        sys.argv = '- check foo bar bingo'.split(' ')
        with self.assertRaises(SystemExit):
            self.assertEquals(main()[0].func, cmds.up)
