import argparse
import ConfigParser as configparser
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
from contextlib import contextmanager

import netifaces


ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))
IMAGES_DIR = os.path.realpath(os.path.join(ROOT, 'images'))
CONFIG_PATH = os.path.expanduser('~/.wharfie')
TREES_DIR = os.path.realpath(os.path.join(ROOT, 'trees'))
BRANCHES = [
    'fireplace',
    'solitude',
    'spartacus',
    'webpay',
    'zamboni',
    'zippy',
]


# Command functions:


def checkout(args, parser, gh_username=None):
    if not gh_username:
        gh_username = whoami(quiet=True)
    if not gh_username:
        parser.error('Please set a github username with the "whoami" '
                     'command first')

    for branch in BRANCHES:
        tree_dir = os.path.join(TREES_DIR, branch)

        if not os.path.isdir(tree_dir):
            subprocess.call([
                'git', 'clone', '-o', args.moz_remote_name,
                'git@github.com:mozilla/{0}.git'.format(branch),
                tree_dir
            ])

            subprocess.call([
                'git', 'remote', 'add', args.fork_remote_name,
                'git@github.com:{0}/{1}.git'.format(gh_username, branch)
            ], cwd=tree_dir)

            subprocess.call([
                'git', 'config', 'branch.master.remote', args.fork_remote_name
            ])


def whoami(args=None, parser=None, quiet=False):
    user = os.environ.get('MKT_GITHUB_USERNAME', None)
    if not user:
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        try:
            user = config.get('github', 'user')
        except configparser.NoSectionError:
            pass

    if args and args.github_username:
        user = args.github_username
        if user:
            try:
                config.add_section('github')
            except configparser.DuplicateSectionError:
                pass
            config.set('github', 'user', user)
            if not quiet:
                print('Saving username {0} to ~/.wharfie'.format(user))
            with open(CONFIG_PATH, 'w') as configfile:
                config.write(configfile)

    if not quiet:
        if user:
            print('github user: {0}'.format(user))
        else:
            print('Try setting your github username with '
                  '"mkt whoami [github_username]"')

    return user


def shell(args, parser):
    image = get_image(args, parser)
    image_name = image['name']
    return subprocess.call(['docker', 'run', '-a', 'stdin', '-a', 'stdout',
                            '-i', '-t', image_name + '_img', '/bin/bash'])


def bind(args, parser):
    if args.interfaces:
        for interface, ip_addr in get_interface_data():
            print('{ip} ({int})'.format(ip=ip_addr, int=interface))
        return

    if not args.bind_ip:
        # Guess the IP.
        interfaces = get_interface_data(args.bind_int)
        if not interfaces:
            args.error('No useable interfaces found. Are you connected '
                       'to a network that your device will be able to "see"?')
        if len(interfaces) > 1:
            prompt = 'Not sure which IP to use. Please select one [1]:'
            interface_ips = get_interface_data()
            choices = []
            for interface, ip_addr in interface_ips:
                choices.append(('{ip} ({int})'.format(ip=ip_addr,
                                                      int=interface), ip_addr))

            choice = select(choices, prompt=prompt)
            args.bind_ip = choice[1]
        else:
            # Get the only IP we found.
            args.bind_ip = interfaces[0][1]

    devices = get_adb_devices()
    if len(devices) > 1:
        raise NotImplementedError(
            'adb says more than one device is connected. Updating the '
            'right one is not implemented yet.')
    elif len(devices) == 0:
        parser.error('Could not find any attached devices with adb. '
                     'Is your device connected?')

    print('About to bind host "{host}" on device to IP "{ip}"'
          .format(host=args.bind_host, ip=args.bind_ip))

    td = tempfile.mkdtemp()
    try:
        with pushd(td):
            subprocess.check_call(['adb', 'remount'])
            subprocess.check_call(['adb', 'pull', '/system/etc/hosts', './'])
            with open('./hosts') as f:
                lines = f.readlines()
                newlines = []
                for ln in lines:
                    if (ln.strip().endswith(args.bind_host) or
                            ln.startswith('# Docker:')):
                        # Remove the old IP binding and comments.
                        continue
                    newlines.append(ln)
                newlines.append('# Docker: wharfie `mkt bind` added this:\n')
                newlines.append('{ip}\t\t    {host}\n'
                                .format(ip=args.bind_ip, host=args.bind_host))

            with open('./new-hosts', 'w') as f:
                f.write(''.join(newlines))
            subprocess.check_call(['adb', 'push', './new-hosts',
                                   '/system/etc/hosts'])
    finally:
        shutil.rmtree(td)


# Helper functions:


@contextmanager
def pushd(newdir):
    wd = os.getcwd()
    try:
        os.chdir(newdir)
        yield
    finally:
        os.chdir(wd)


def get_adb_devices():
    devices = subprocess.check_output(['adb', 'devices']).strip().splitlines()
    devices.pop(0)  # remove the header
    return devices


def indent(text, times=1):
    wrapper = textwrap.TextWrapper(
        initial_indent='  '*times, width=90, subsequent_indent='  '*times
    )
    for line in text.splitlines():
        print wrapper.fill(line)


def check_git_config(args, parser):
    for branch in BRANCHES:
        tree_dir = os.path.join(TREES_DIR, branch)
        cur_dir = os.getcwd()
        if os.path.isdir(tree_dir):
            try:
                os.chdir(tree_dir)
                print "[{0}]".format(branch)
                indent("[remotes]")
                indent(subprocess.check_output(['git', 'remote', '-v']), 2)
                indent("[Master branch origin]")
                origin = subprocess.check_output(['git', 'config', '--get',
                                                  'branch.master.remote'])
                indent(origin, 2)
                print
            finally:
                os.chdir(cur_dir)


def get_image(args, parser):
    image_name = args.name
    image_dir = os.path.join(IMAGES_DIR, image_name)

    if not os.path.isdir(image_dir):
        parser.error('image_dir: {0} does not exist. '
                     'Exiting'.format(image_dir))

    return {
        'name': image_name,
        'dir': image_dir,
    }


def select(choices, default=1, prompt='Please choose from the following [1]:'):
    """Create a prompt similar to select in bash."""

    invalid_choice = 'Not a valid choice. Try again.'

    for i, value in enumerate(choices):
        print('{num}) {val}'.format(num=i + 1, val=value[0]))

    def get_choice():
        try:
            val = raw_input(prompt)
            if val == '':
                val = default
            val = int(val) - 1
        except ValueError:
            print(invalid_choice)
            return get_choice()
        except KeyboardInterrupt:
            print('')
            print('caught KeyboardInterrupt')
            sys.exit(1)

        try:
            return choices[val]
        except IndexError:
            print(invalid_choice)
            return get_choice()

    return get_choice()


def get_ips_for_interface(interface):
    """Get the ips for a specific interface."""
    interface_ips = []
    try:
        for fam, data in netifaces.ifaddresses(interface).items():
            if fam == socket.AF_INET:
                for d in data:
                    ip = d.get('addr')
                    if ip and not ip.startswith('127'):
                        interface_ips.append((interface, ip))
        return interface_ips
    except ValueError, exc:
        raise ValueError('You provided "{int}". Choose one of: {opt}; '
                         'ValueError: {err}'
                         .format(opt=', '.join(netifaces.interfaces()),
                                 int=interface, err=exc))


def get_interface_data(interface=None):
    """
    Get interface data for one or more interfaces.

    Returns data for all useful interfaces if no specific interface
    is provided.
    """
    if interface:
        interface_ips = get_ips_for_interface(interface)
    else:
        interface_ips = []
        for int_ in netifaces.interfaces():
            if int_ == 'vboxnet0':
                # Skip the Virtual Box interface because that's not publicly
                # accessible.
                continue
            interface_ips += get_ips_for_interface(int_)
    return sorted(interface_ips, key=lambda tup: tup[1])


def create_parser():
    parser = argparse.ArgumentParser(description='Wharfie')

    subparsers = parser.add_subparsers(
        help='See each command for additional help',
        title='Sub-commands', description='Valid commands'
    )

    if not os.path.isdir(IMAGES_DIR):
        parser.error('IMAGES_DIR: {0} does not exist. '
                     'Exiting'.format(IMAGES_DIR))

    VALID_SUBDIRS = os.walk(IMAGES_DIR).next()[1]

    parser_shell = subparsers.add_parser(
        'shell', help='Run image, and drop into a shell on it.'
    )
    parser_shell.add_argument(
        'name', help='The name of the image to run a shell on',
        metavar="IMAGE_NAME",
        choices=VALID_SUBDIRS
    )
    parser_shell.set_defaults(func=shell)
    parser_shell = subparsers.add_parser(
        'chkgitconfig', help='Print out the git config for mkt branches'
    )
    parser_shell.set_defaults(func=check_git_config)

    parser_whoami = subparsers.add_parser(
        'whoami', help='Check your github credentials'
    )
    parser_whoami.add_argument(
        'github_username', help='Your github username e.g. "jrrtolkien"',
        metavar="USER_NAME", default=None, nargs='?'
    )
    parser_whoami.set_defaults(func=whoami)

    parser_checkout = subparsers.add_parser(
        'checkout', help='Checkout your forks of sourcecode'
    )
    parser_checkout.add_argument(
        '--moz_remote_name',
        help='What to call the mozilla repo remote for this project. '
             'Following github terminology this defaults to "upstream"',
        metavar="MOZ_REMOTE_NAME",
        default='upstream', nargs='?'
    )
    parser_checkout.add_argument(
        '--fork_remote_name',
        help='What to call your fork remote for this project. Following '
             'github terminology this defaults to "origin"',
        metavar="FORK_REMOTE_NAME", default='origin', nargs='?'
    )
    parser_checkout.set_defaults(func=checkout)

    parser_bind = subparsers.add_parser(
        'bind', help='Bind the mp.dev domain to your public IP on '
                     'a Firefox OS device. Your public ID must be a proxy to '
                     'your internal Docker IP.'
    )
    parser_bind.add_argument(
        '--bind_ip',
        help='Public IP to bind to. If empty, the IP will be discovered.')
    parser_bind.add_argument(
        '--bind_host', default='mp.dev',
        help='Hostname to bind your IP too. Default: %default')
    parser_bind.add_argument(
        '--bind_int',
        help='Network interface to guess a public IP from. Example: en0',
        default=None)
    parser_bind.add_argument(
        '--interfaces',
        help='Show network interfaces but do not bind anything.',
        action='store_true')
    parser_bind.set_defaults(func=bind)

    return parser
