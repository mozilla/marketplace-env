import argparse
import ConfigParser as configparser
import functools
import os
import re
import sha
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
from collections import namedtuple
from contextlib import contextmanager
from decimal import Decimal
from pprint import pprint

import netifaces
import requests

from fig.cli import main
from fig.cli.docker_client import docker_client
from version import __version__

ROOT = os.path.dirname(os.path.abspath(__file__))
join = functools.partial(os.path.join, ROOT)
CONFIG_PATH = os.path.expanduser('~/.wharfie')
FIG_PATH = os.getenv('FIG_FILE', os.path.expanduser('~/.mkt.fig.yml'))

BRANCHES = [
    'fireplace',
    'solitude',
    'spartacus',
    'webpay',
    'zamboni',
    'zippy',
]


# Mapping of the branch to [file in container, file locally].
req = namedtuple('Requirement', ['container', 'local'])
pip = req('/pip/requirements/prod.txt', 'requirements/prod.txt')
js = lambda x, y: req('/srv/{0}/{1}.json'.format(x, y), '{0}.json'.format(y))

REQUIREMENTS = {
    'zamboni': [pip],
    'solitude': [pip],
    'webpay': [pip],
    'fireplace': [js('fireplace', 'bower'), js('fireplace', 'package')],
    'spartacus': [js('spartacus', 'package')],
    'zippy': [js('zippy', 'package')],
}

MIGRATIONS = ['zamboni', 'solitude']

SERVICE_CHECKS = {
    'solitude': 'http://mp.dev/solitude/services/status/',
    'webpay': 'http://mp.dev/mozpay/services/monitor',
    'zamboni': 'http://mp.dev/services/monitor.json'
}

HUB_ACCOUNT = 'mozillamarketplace'

# Command functions:

def check_git_config(args, parser):
    for branch in BRANCHES:
        branch_dir = join(locations()['tree'], branch)
        with pushd(branch_dir):
            os.chdir(branch_dir)
            print "[{0}]".format(branch)
            indent("[remotes]")
            indent(subprocess.check_output(['git', 'remote', '-v']), 2)
            indent("[Master branch origin]")
            origin = subprocess.check_output(['git', 'config', '--get',
                                              'branch.master.remote'])
            indent(origin, 2)
            print


def revs(args, parser):
    for branch in BRANCHES:
        active_branch, rev = get_git_rev(branch)
        print "{0}: {1} [{2}]".format(branch, rev, active_branch)


def checkout(args, parser, gh_username=None):
    if not locations()['tree']:
        parser.error('Please set a location by calling root first.')

    if not gh_username:
        gh_username = whoami(quiet=True)
    if not gh_username:
        parser.error('Please set a github username with the "whoami" '
                     'command first')

    for branch in BRANCHES:
        branch_dir = join(locations()['tree'], branch)
        if not os.path.isdir(branch_dir):
            subprocess.call([
                'git', 'clone', '-o', args.moz_remote_name,
                'https://github.com/mozilla/{0}.git'.format(branch),
                branch_dir
            ])

            subprocess.call([
                'git', 'remote', 'add', args.fork_remote_name,
                'https://github.com/{0}/{1}.git'.format(gh_username, branch)
            ], cwd=branch_dir)

            subprocess.call([
                'git', 'config', 'branch.master.remote', args.moz_remote_name
            ])


def whoami(args=None, parser=None, quiet=False):
    user = os.environ.get('MKT_GITHUB_USERNAME', None)
    if not user:
        user = get_config_value('github', 'user')

    if args and args.github_username:
        user = args.github_username
        if user:
            set_config_value('github', 'user', user)

    if not quiet:
        if user:
            print('github user: {0}'.format(user))
        else:
            print('Try setting your github username with '
                  '"mkt whoami [github_username]"')

    return user


def locations():
    return {
        # Where the checked out projects live.
        'tree': get_config_value('paths', 'root'),
        # Where the images live, will be local or in the installed path.
        'image': join('data', 'images'),
        # Where fig config lives, will be local or in the installed file path.
        'fig.dist': join('data', 'fig.yml.dist'),
        # FIG_FILE is the file that fig uses.
        'fig': FIG_PATH
    }


def root(args, parser):
    if not args.directory:
        value = get_config_value('paths', 'root')
        if value:
            print value
        return

    directory = os.path.abspath(os.path.expandvars(args.directory))
    if not os.path.exists(directory):
        raise ValueError('Directory {0} does not exist.'.format(directory))

    set_config_value('paths', 'root', directory)
    update_config(args, parser)


def update_config(args, parser):
    context = locations()
    src_file = context['fig.dist']
    with open(src_file, 'r') as src:
        src_data = src.read()

    dest_file = context['fig']
    new_data = src_data.format(**context)

    if os.path.exists(dest_file):
        # If the old file is the same as the new file, then there
        # is no need to add anything new.
        old_data = open(dest_file, 'r').read()
        if old_data == new_data:
            return

    with open(dest_file, 'w') as dest:
        dest.write(new_data)
        print 'Written fig file to {0}'.format(FIG_PATH)


def up(args, parser, argv):
    update_config(args, parser)
    cmd = ['up', '-d', '--no-recreate'] + argv
    fig_command(*cmd)

up.argv = True


def bash(args, parser):
    project = get_project(args.project)
    cmd = ('docker exec -t -i {0} /bin/bash'
           .format(get_fig_container(project).id))
    os.system(cmd)
    return


def get_version(method):
    methods = {
        'docker': [
            'Client version: (\d.\d).*?Server version: (\d.\d)',
            ['docker', 'version']
        ],
        'boot2docker': [
            '^Boot2Docker-cli version: v(\d.\d)',
            ['boot2docker', 'version']
        ],
        'fig': ['^fig (\d.\d)', ['fig', '--version']]
    }
    regex, command = methods[method]
    try:
        result = subprocess.check_output(command).strip()
    except OSError:
        raise ValueError('Command: "{0}" failed, is it installed?'
                         .format(' '.join(command)))

    try:
        res = re.findall(regex, result, flags=re.S)
        if isinstance(res[0], tuple):
            res = res[0]
    except IndexError:
        raise ValueError('Command: "{0}" returned an unknown value.'
                         .format(' '.join(command)))

    return [Decimal(v) for v in res]


def check(args, parser):
    context = locations()
    default = os.getenv('FIG_FILE')

    diffs = []
    if context['fig'] != default:
        diffs.append('FIG_FILE={0}'.format(FIG_PATH))

    default = os.getenv('FIG_PROJECT_NAME')
    if 'mkt' != os.getenv('FIG_PROJECT_NAME'):
        diffs.append('FIG_PROJECT_NAME=mkt')

    if diffs:
        print 'Set the following environment variables: '
        for d in diffs:
            print d
        print

    for path in ['tree', 'image']:
        if not os.path.exists(context[path]):
            print 'Directory {0} does not exist.'.format(context[path])

    for branch in BRANCHES:
        branch_dir = join(context['tree'], branch)
        if not os.path.exists(branch_dir):
            print ('Directory {0} does not exist, run checkout.'
                   .format(branch_dir))

    if args.services:
        for service, url in SERVICE_CHECKS.items():
            try:
                res = requests.get(url, timeout=5)
            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError):
                # nginx isn't even up.
                print 'Error on: {0}, is it running?'.format(service)
                continue

            if res.status_code == 502:
                # nginx proxy errors.
                print 'Service not up: {0} (proxy error)'.format(service)

            if res.status_code == 500:
                print 'Status failed on: {0}.'.format(service)
                print
                pprint(res.json())
                print

    if args.versions:
        dockers = get_version('docker')
        for version in dockers:
            if version < Decimal('1.3'):
                print ('Update docker, client or server version 1.3 or higher '
                       'is recommended. Run: docker version')
        if get_version('boot2docker')[0] < Decimal('1.3'):
            print 'Update boot2docker, version 1.3 or higher recommended.'
        if get_version('fig')[0] < Decimal('1.0'):
            print 'Update fig, version 1.0 or higher recommended.'

    if args.requirements:
        for branch in BRANCHES:
            files = REQUIREMENTS.get(branch)
            if not files:
                continue

            container = get_container_requirements(branch, files)
            local = get_local_requirements(branch, files)
            if local != container:
                print ('Requirements on container differ from local, '
                       'rebuild recommended for: {0}'.format(branch))


def push(args, parser):
    project = get_project(args.project)
    rev = get_image_rev(project)

    branch_dir = join(locations()['tree'], project)
    with pushd(branch_dir):
        container = get_fig_container(project)
        image_id = get_image_id(container)
        cmd = ('docker tag {0} {1}/{2}:{3}'
               .format(image_id, HUB_ACCOUNT, project, rev))
        os.system(cmd)
        cmd = 'docker push {0}/{1}:{2}'.format(HUB_ACCOUNT, project, rev)
        os.system(cmd)


def update(args, parser):
    git, migration = args.git, args.migrations
    if not git and not migration:
        # If the user didn't pass a flag, run both.
        git, migration = True, True

    if git:
        for branch in BRANCHES:
            branch_dir = join(locations()['tree'], branch)
            with pushd(branch_dir):
                try:
                    print 'Updating git for: {0}'.format(branch)
                    indent(subprocess.check_output(['git', 'pull', '-q']), 2)
                except subprocess.CalledProcessError:
                    print
                    print 'Failed to update: {0}'.format(branch_dir)
                    print
                    raise

    if migration:
        for migration in MIGRATIONS:
            print 'Running migration for: {0}'.format(migration)
            fig_command('run', '--rm', migration,
                        'schematic', 'migrations')


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
                newlines.append(
                    '# Docker: marketplace-env `mkt bind` added this:\n')
                newlines.append('{ip}\t\t    {host}\n'
                                .format(ip=args.bind_ip, host=args.bind_host))

            with open('./new-hosts', 'w') as f:
                f.write(''.join(newlines))
            subprocess.check_call(['adb', 'push', './new-hosts',
                                   '/system/etc/hosts'])
    finally:
        shutil.rmtree(td)


# Helper functions:

def get_container_requirements(branch, files):
    project = get_project(branch)
    files_str = ' '.join([f.container for f in files])
    cmd = ('docker exec -t -i {0} /bin/bash -c "cat {1} | sha1sum"'
            .format(get_fig_container(project).id, files_str))
    try:
        container = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        print 'Failed to check: {0}'.format(branch)
        raise
    # If we could supress the ' -' on the output of sha1sum, we
    # could remove this.
    return container.split(' ')[0]


def get_local_requirements(branch, files):
    branch_dir = join(locations()['tree'], branch)
    local = sha.new()
    for name in files:
        with open(os.path.join(branch_dir, name.local)) as handle:
            local.update(handle.read())
    return local.hexdigest()


def get_project(project):
    cur = os.getcwd()

    def walk(directory):
        if 'Dockerfile' in os.listdir(directory):
            return os.path.basename(directory)

        new = os.path.dirname(directory)
        if new == directory:
            raise ValueError('No project found.')
        return walk(new)

    project = project or walk(cur)
    if project not in BRANCHES:
        raise ValueError('Project {0} not in BRANCHES'.format(project))

    return project

def get_git_rev(branch):
    branch_dir = join(locations()['tree'], branch)
    with pushd(branch_dir):
        active_branch = subprocess.check_output([
            'git', 'rev-parse', '--abbrev-ref', 'HEAD'])
        rev = subprocess.check_output([
            'git', 'log', '-n', '1',
            '--pretty=oneline', '--abbrev-commit'])
        return active_branch.rstrip(), rev.split()[0]


def get_image_rev(branch):
    files = REQUIREMENTS.get(branch)[:]
    files.append(req('', 'Dockerfile'))
    return get_local_requirements(branch, files)[:8]


def get_image_id(container):
    for image in docker_client().images():
        for tag in image['RepoTags']:
            if tag == container.image:
                return image['Id']

    raise ValueError('No image found for: {0}'.format(container.image))


def get_fig_container(project):
    cmd = main.Command()
    proj = cmd.get_project(FIG_PATH)
    containers = proj.containers(service_names=[project])
    if not containers:
        raise ValueError('No containers found for: {0}. '
                         'Run: mkt up' .format(project))
    return containers[0]


def fig_command(*args):
    cmd = main.TopLevelCommand()
    try:
        cmd.dispatch(args, None)
    except SystemExit as exit:
        if exit.code != 0:
            raise


def get_config_value(section, key, default=None):
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    try:
        return config.get(section, key)
    except configparser.NoSectionError:
        pass
    return default


def set_config_value(section, key, value):
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    try:
        config.add_section(section)
    except configparser.DuplicateSectionError:
        pass
    config.set(section, key, value)
    print('Saving {0} to {1}'.format(key, CONFIG_PATH))

    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)


def indent(text, times=1):
    wrapper = textwrap.TextWrapper(
        initial_indent='  '*times, width=90, subsequent_indent='  '*times
    )
    for line in text.splitlines():
        print wrapper.fill(line)


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
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        help='See each command for additional help',
        title='Sub-commands', description='Valid commands'
    )

    parser_root = subparsers.add_parser(
        'root', help='Create or update the root paths in the fig.yml.'
    )
    parser_root.add_argument(
        'directory', help='Path to the marketplace repositories.',
        default=None, nargs='?'
    )
    parser_root.set_defaults(func=root)

    parser_bash = subparsers.add_parser(
        'bash', help='Run a bash shell on a running container.'
    )
    parser_bash.add_argument(
        '--project',
        help='Project name, if not given will be calculated.',
        action='store')
    parser_bash.set_defaults(func=bash)

    parser_update = subparsers.add_parser(
        'update', help='Runs git pull on each repo and any migrations.'
    )
    parser_update.add_argument(
        '--git', help='Runs git pull', action='store_true')
    parser_update.add_argument(
        '--migrations', help='Runs migrations', action='store_true')
    parser_update.set_defaults(func=update)

    parser_check = subparsers.add_parser(
        'check', help='Basic health checks of the system.'
    )
    parser_check.add_argument(
        '--services', help='Checks the status page of each service.',
        action='store_true'
    )
    parser_check.add_argument(
        '--requirements', help='Checks the container requirements vs current'
                               ' requirements',
        action='store_true'
    )
    parser_check.add_argument(
        '--versions', help='Checks versions of docker, boot2docker and fig',
        action='store_true'
    )
    parser_check.set_defaults(func=check)

    parser_push = subparsers.add_parser(
        'push', help='Tag and push instances of containers to Docker Hub.'
    )
    parser_push.add_argument(
        '--project',
        help='Project name, if not given will be calculated.',
        action='store')
    parser_push.set_defaults(func=push)

    parser_up = subparsers.add_parser(
        'up', help='Recreates fig.yml and starts the '
                   'containers in the background, a wrapper around `fig up`'
    )
    parser_up.set_defaults(func=up)

    parser_checkgitconfig = subparsers.add_parser(
        'chkgitconfig', help='Print out the git config for mkt branches'
    )
    parser_checkgitconfig.set_defaults(func=check_git_config)

    parser_revs = subparsers.add_parser(
        'revs', help='Print out the git revs for the trees'
    )
    parser_revs.set_defaults(func=revs)

    parser_whoami = subparsers.add_parser(
        'whoami', help='Check or store your github credentials'
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
        help='Hostname to bind your IP too. Default: %(default)s')
    parser_bind.add_argument(
        '--bind_int',
        help='Network interface to guess a public IP from. Example: en0',
        default=None)
    parser_bind.add_argument(
        '--interfaces',
        help='Show network interfaces but do not bind anything.',
        action='store_true')
    parser_bind.set_defaults(func=bind)

    parser.add_argument('--version', action='version', version=__version__)
    # Setup the logging for fig.
    main.setup_logging()
    return parser
